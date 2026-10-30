import assert from "node:assert/strict";
import { describe, it, afterEach } from "node:test";

import { init } from "../src/index.js";
import { fakeEnv, fakeFetch, fakePerformance, fakeStorage, flushMicrotasks } from "./helpers.js";

const CONFIG = {
  apiKey: "ilp_test_key",
  endpoint: "https://ingest.example.com",
  consent: true,
  sampleRate: 1,
};

let active = [];

function start(options = {}, config = {}) {
  const fake = fakeEnv(options);
  const agent = init({ ...CONFIG, ...config }, fake.env);
  active.push(agent);
  return { ...fake, agent };
}

afterEach(() => {
  for (const agent of active) if (agent && agent.stop) agent.stop();
  active = [];
});

describe("page view (§2.2, AC-02, AC-03)", () => {
  it("envía TTFB y FCP y cumple el contrato del envelope", async () => {
    const fetch = fakeFetch();
    const { agent, fetch: used } = start(
      {
        fetch,
        performance: fakePerformance({
          timeOrigin: 1_700_000_000_000,
          navigation: { responseStart: 300, requestStart: 100 },
          paint: [{ name: "first-contentful-paint", startTime: 700 }],
        }),
      },
      { apiKey: "ilp_test_key" },
    );
    assert.equal(agent.enabled, true);
    await flushMicrotasks();
    await agent.flush();
    await flushMicrotasks();

    assert.ok(used.calls.length >= 1);
    const call = used.calls[0];
    assert.equal(call.url, "https://ingest.example.com/telemetry/metrics");
    assert.equal(call.body.schema_version, "1.0");
    assert.equal(call.body.events.length, 1);

    const [event] = call.body.events;
    assert.equal(event.schema_version, "1.0");
    assert.equal(event.session_id, agent.sessionId);
    assert.equal(event.timestamp, new Date(1_700_000_000_000).toISOString());
    assert.deepEqual(
      event.metrics.map((metric) => [metric.type, metric.value, metric.unit]),
      [
        ["TTFB", 200, "ms"],
        ["FCP", 700, "ms"],
      ],
    );
    assert.equal(event.metrics[0].page_url, "https://shop.example.com/product/{id}");
    assert.equal(event.metrics[0].metadata.sample_rate, 1);
    assert.equal(event.metrics[0].metadata.agent_version, "1.0.0");
    // §2.2: user_agent va en el metadata del EVENTO (user_session.user_agent).
    assert.equal(event.metadata.user_agent, "test-agent/1.0");
    assert.equal(event.metadata.user_agent.length <= 256, true);
  });

  it("envía solo TTFB cuando FCP no ocurrió", async () => {
    const fetch = fakeFetch();
    const { agent, fetch: used } = start({
      fetch,
      performance: fakePerformance({ navigation: { responseStart: 250, requestStart: 50 } }),
    });
    await flushMicrotasks();
    await agent.flush();
    const [event] = used.calls[0].body.events;
    assert.deepEqual(event.metrics.map((m) => m.type), ["TTFB"]);
    assert.equal(event.metrics[0].value, 200);
  });

  it("no envía métricas cuando la Navigation Timing API no existe", async () => {
    const fetch = fakeFetch();
    const { agent, fetch: used } = start({ fetch, performance: fakePerformance() });
    await flushMicrotasks();
    await agent.flush();
    assert.equal(used.calls.length, 0);
  });
});

describe("excepciones (§2.3, AC-04)", () => {
  it("envía un TypeError no manejado a /telemetry/exceptions", async () => {
    const fetch = fakeFetch();
    const { agent, window, fetch: used } = start({ fetch });

    const error = new TypeError("render falló");
    error.stack = "TypeError: render falló\n    at app.js:10:5";
    window.dispatch("error", error);

    await flushMicrotasks();
    await agent.flush();
    const call = used.calls.find((item) => item.url.endsWith("/telemetry/exceptions"));
    assert.ok(call, "debe existir un request a /telemetry/exceptions");
    assert.equal(call.body.schema_version, "1.0");
    const [event] = call.body.events;
    assert.equal(event.schema_version, "1.0");
    assert.equal(event.error_type, "TypeError");
    assert.equal(event.message, "render falló");
    assert.match(event.stack_trace, /app\.js:10:5/);
    assert.equal(event.session_id, agent.sessionId);
    assert.match(event.timestamp, /Z$/);
    assert.equal(event.sample_rate, 1);
    assert.equal("metric_id" in event, false);
    assert.equal("application_id" in event, false);
  });

  it("marca las promesas rechazadas como UnhandledRejection", async () => {
    const fetch = fakeFetch();
    const { agent, window, fetch: used } = start({ fetch });
    window.dispatch("unhandledrejection", { reason: new Error("boom asíncrono") });
    await flushMicrotasks();
    await agent.flush();
    const call = used.calls.find((item) => item.url.endsWith("/telemetry/exceptions"));
    assert.equal(call.body.events[0].error_type, "UnhandledRejection");
    assert.equal(call.body.events[0].message, "boom asíncrono");
  });

  it("agrupa excepciones en un solo batch", async () => {
    const fetch = fakeFetch();
    const { agent, window, fetch: used } = start({ fetch });
    for (let i = 0; i < 3; i += 1) window.dispatch("error", new Error(`e${i}`));
    await flushMicrotasks();
    await agent.flush();
    const call = used.calls.find((item) => item.url.endsWith("/telemetry/exceptions"));
    assert.equal(call.body.events.length, 3);
  });
});

describe("privacidad y consentimiento (§9, AC-09)", () => {
  it("no se inicializa sin consentimiento", () => {
    const { agent } = start({}, { consent: false });
    assert.equal(agent.enabled, false);
    assert.equal(agent.reason, "not_allowed");
  });

  it("no se inicializa con Do Not Track", () => {
    const { agent } = start({ navigator: { doNotTrack: "1" } });
    assert.equal(agent.enabled, false);
  });

  it("no se inicializa con la clave de opt-out", () => {
    const { agent } = start({ localStorage: fakeStorage({ "intellops-optout": "1" }) });
    assert.equal(agent.enabled, false);
  });

  it("el payload no incluye query strings ni credenciales", async () => {
    const fetch = fakeFetch();
    const { agent, fetch: used } = start({
      fetch,
      performance: fakePerformance({ navigation: { responseStart: 200, requestStart: 100 } }),
      location: { href: "https://shop.example.com/p/9?token=secreto#x", origin: "https://shop.example.com" },
    });
    await flushMicrotasks();
    await agent.flush();
    const serialized = JSON.stringify(used.calls[0].body);
    assert.equal(serialized.includes("token"), false);
    assert.equal(serialized.includes("secreto"), false);
    assert.equal(serialized.includes("#"), false);
  });

  it("redacta PII en el mensaje de la excepción", async () => {
    const fetch = fakeFetch();
    const { agent, window, fetch: used } = start({ fetch });
    window.dispatch("error", new Error("falló federico@example.com"));
    await flushMicrotasks();
    await agent.flush();
    const call = used.calls.find((item) => item.url.endsWith("/telemetry/exceptions"));
    assert.equal(call.body.events[0].message, "falló [REDACTED]");
  });
});

describe("muestreo (§5, AC-08)", () => {
  it("no recolecta cuando la sesión no fue muestreada", async () => {
    const fetch = fakeFetch();
    const { agent, window, fetch: used } = start({ fetch }, { sampleRate: 0 });
    assert.equal(agent.enabled, false);
    assert.equal(agent.reason, "not_sampled");
    window.dispatch("error", new Error("no debería enviarse"));
    await flushMicrotasks();
    assert.equal(used.calls.length, 0);
  });

  it("reporta sample_rate en métricas y excepciones", async () => {
    const fetch = fakeFetch();
    const { agent, window, fetch: used } = start(
      { fetch, performance: fakePerformance({ navigation: { responseStart: 200, requestStart: 100 } }) },
      { sampleRate: 1 },
    );
    await flushMicrotasks();
    window.dispatch("error", new Error("boom muestreado"));
    await flushMicrotasks();
    await agent.flush();
    const metricsCall = used.calls.find((call) => call.url.endsWith("/telemetry/metrics"));
    const exceptionsCall = used.calls.find((call) => call.url.endsWith("/telemetry/exceptions"));
    assert.equal(metricsCall.body.events[0].metrics[0].metadata.sample_rate, 1);
    assert.equal(exceptionsCall.body.events[0].sample_rate, 1);
  });
});

describe("reintentos end-to-end (§7, AC-08)", () => {
  it("reintenta el batch ante 503 y termina en éxito", async () => {
    const fetch = fakeFetch([{ status: 503 }, { status: 202, body: { accepted: 1, rejected: [] } }]);
    const { agent, fetch: used } = start(
      { fetch, performance: fakePerformance({ navigation: { responseStart: 200, requestStart: 100 } }) },
      {},
    );
    await flushMicrotasks();
    await agent.flush();
    await flushMicrotasks();
    const metricsCalls = used.calls.filter((call) => call.url.endsWith("/telemetry/metrics"));
    assert.equal(metricsCalls.length, 2);
    assert.ok(agent.counters.sent >= 1);
  });
});

describe("ciclo de vida (§6)", () => {
  it("hace flush al ocultarse la pestaña", async () => {
    const fetch = fakeFetch();
    const { agent, window, document, fetch: used } = start({ fetch });
    assert.ok(agent.enabled);
    window.dispatch("error", new Error("antes de ocultar"));
    document.visibilityState = "hidden";
    document.dispatch("visibilitychange");
    await flushMicrotasks();
    await flushMicrotasks();
    assert.ok(used.calls.some((call) => call.url.endsWith("/telemetry/exceptions")));
  });

  it("hace flush en pagehide", async () => {
    const fetch = fakeFetch();
    const { window, fetch: used } = start({ fetch });
    window.dispatch("error", new Error("antes de salir"));
    window.dispatch("pagehide");
    await flushMicrotasks();
    await flushMicrotasks();
    assert.ok(used.calls.some((call) => call.url.endsWith("/telemetry/exceptions")));
  });
});
