import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { backoffDelay, createTransport } from "../src/transport.js";
import { fakeFetch } from "./helpers.js";

const noSleep = async () => {};

function makeTransport(fetch, extra = {}) {
  return createTransport(
    { fetch, AbortController: globalThis.AbortController },
    { apiKey: "ilp_test_key", endpoint: "https://ingest.example.com", sleep: noSleep, random: () => 0.5, ...extra },
  );
}

describe("transporte (§4, AC-06)", () => {
  it("envía con fetch keepalive, CORS sin credenciales y X-API-Key", async () => {
    const fetch = fakeFetch([{ status: 202, body: { accepted: 1, rejected: [] } }]);
    const transport = makeTransport(fetch);
    const result = await transport.send("/telemetry/metrics", { schema_version: "1.0", events: [{ a: 1 }] });

    assert.equal(result.ok, true);
    assert.equal(result.status, 202);
    const [call] = fetch.calls;
    assert.equal(call.url, "https://ingest.example.com/telemetry/metrics");
    assert.equal(call.init.method, "POST");
    assert.equal(call.init.keepalive, true);
    assert.equal(call.init.mode, "cors");
    assert.equal(call.init.credentials, "omit");
    assert.equal(call.init.headers["X-API-Key"], "ilp_test_key");
    assert.equal(call.init.headers["Content-Type"], "application/json");
  });

  it("no existe sendBeacon en el entorno del agente", async () => {
    const fetch = fakeFetch();
    const transport = makeTransport(fetch);
    await transport.send("/telemetry/metrics", { schema_version: "1.0", events: [] });
    assert.equal(fetch.calls[0].init.beacon, undefined);
  });
});

describe("reintentos y backoff (§7, AC-08)", () => {
  it("reintenta hasta 3 intentos ante 503 y luego falla", async () => {
    const fetch = fakeFetch([{ status: 503 }]);
    const transport = makeTransport(fetch);
    const result = await transport.send("/telemetry/metrics", { events: [] });
    assert.equal(result.ok, false);
    assert.equal(result.reason, "exhausted");
    assert.equal(fetch.calls.length, 3);
  });

  it("se recupera si un reintento devuelve 202", async () => {
    const fetch = fakeFetch([{ status: 503 }, { status: 503 }, { status: 202, body: { accepted: 1, rejected: [] } }]);
    const transport = makeTransport(fetch);
    const result = await transport.send("/telemetry/metrics", { events: [] });
    assert.equal(result.ok, true);
    assert.equal(fetch.calls.length, 3);
  });

  it("reintenta ante error de red", async () => {
    const fetch = fakeFetch([new Error("network down"), { status: 202, body: {} }]);
    const transport = makeTransport(fetch);
    const result = await transport.send("/telemetry/metrics", { events: [] });
    assert.equal(result.ok, true);
    assert.equal(fetch.calls.length, 2);
  });

  it("no reintenta ante 400 ni ante 429", async () => {
    for (const status of [400, 429]) {
      const fetch = fakeFetch([{ status }]);
      const transport = makeTransport(fetch);
      const result = await transport.send("/telemetry/metrics", { events: [] });
      assert.equal(result.ok, false);
      assert.equal(result.reason, "permanent");
      assert.equal(fetch.calls.length, 1);
    }
  });

  it("abre el circuito y deja de enviar ante 401 y 403", async () => {
    for (const status of [401, 403]) {
      const fetch = fakeFetch([{ status }]);
      const transport = makeTransport(fetch);
      const result = await transport.send("/telemetry/exceptions", { events: [] });
      assert.equal(result.reason, "stopped");
      assert.equal(transport.stopped, true);
      const second = await transport.send("/telemetry/exceptions", { events: [] });
      assert.equal(second.reason, "circuit_open");
      assert.equal(fetch.calls.length, 1);
    }
  });

  it("expone los rechazos parciales del 202", async () => {
    const fetch = fakeFetch([{ status: 202, body: { accepted: 0, rejected: [{ index: 0, reason: "invalid_range" }] } }]);
    const transport = makeTransport(fetch);
    const result = await transport.send("/telemetry/metrics", { events: [] });
    assert.deepEqual(result.body.rejected, [{ index: 0, reason: "invalid_range" }]);
  });
});

describe("backoff (§7)", () => {
  it("sigue la secuencia 1 s y 2 s con jitter de ±20 %", () => {
    assert.equal(backoffDelay(0, () => 0.5), 1000);
    assert.equal(backoffDelay(1, () => 0.5), 2000);
    assert.equal(backoffDelay(0, () => 0), 800);
    assert.equal(backoffDelay(0, () => 1), 1200);
  });
});
