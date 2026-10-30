import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isCollectionAllowed,
  redact,
  safeMessage,
  safeStackTrace,
  sanitizeUrl,
  truncateUserAgent,
} from "../src/privacy.js";
import { asAdapter, fakeStorage } from "./helpers.js";

describe("saneado de URL (§9, AC-09)", () => {
  it("descarta query string y fragmento", () => {
    const url = sanitizeUrl("https://shop.example.com/product?id=7&token=secret#top");
    assert.equal(url, "https://shop.example.com/product");
  });

  it("reemplaza segmentos numéricos y UUID por {id}", () => {
    const url = sanitizeUrl(
      "https://shop.example.com/orders/12345/users/3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    );
    assert.equal(url, "https://shop.example.com/orders/{id}/users/{id}");
  });

  it("conserva segmentos que no son identificadores", () => {
    assert.equal(sanitizeUrl("https://shop.example.com/checkout/summary"), "https://shop.example.com/checkout/summary");
  });

  it("trunca a 2048 caracteres", () => {
    const url = sanitizeUrl(`https://shop.example.com/${"a".repeat(3000)}`);
    assert.equal(url.length, 2048);
  });

  it("devuelve cadena vacía ante valores inválidos", () => {
    assert.equal(sanitizeUrl(undefined), "");
    assert.equal(sanitizeUrl(""), "");
  });
});

describe("redacción de PII (§9, AC-09)", () => {
  it("redacta emails", () => {
    assert.equal(redact("falló para federico@example.com"), "falló para [REDACTED]");
  });

  it("redacta tokens bearer", () => {
    assert.equal(redact("Authorization: Bearer eyabc123"), "Authorization: Bearer [REDACTED]");
  });

  it("redacta API keys de ingesta", () => {
    assert.equal(redact("key ilp_fixture_de_prueba_1234"), "key [REDACTED]");
  });

  it("redacta parámetros sensibles en texto libre", () => {
    assert.equal(redact("GET /login?password=hunter2&user=x"), "GET /login?password=[REDACTED]&user=x");
  });

  it("redacta JWT", () => {
    assert.equal(
      redact("token eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123XYZ"),
      "token [REDACTED]",
    );
  });
});

describe("truncado posterior a la redacción", () => {
  it("no deja media credencial al recortar el mensaje", () => {
    const message = `${"a".repeat(1990)} federico@example.com`;
    const safe = safeMessage(message);
    assert.equal(safe.length, 2000);
    assert.equal(safe.includes("federico@"), false);
  });

  it("devuelve undefined para stack vacío", () => {
    assert.equal(safeStackTrace(""), undefined);
    assert.equal(safeStackTrace(undefined), undefined);
  });

  it("trunca el user agent a 256", () => {
    assert.equal(truncateUserAgent("u".repeat(400)).length, 256);
    assert.equal(truncateUserAgent(undefined), "");
  });
});

describe("consentimiento, DNT y opt-out (§9)", () => {
  it("sin consentimiento explícito no recolecta", () => {
    const env = { navigator: {}, storage: asAdapter(fakeStorage()) };
    assert.equal(isCollectionAllowed(env, false), false);
    assert.equal(isCollectionAllowed(env, undefined), false);
  });

  it("recolecta con consentimiento y sin señales de opt-out", () => {
    const env = { navigator: {}, storage: asAdapter(fakeStorage()) };
    assert.equal(isCollectionAllowed(env, true), true);
  });

  it("respeta Do Not Track", () => {
    const env = { navigator: { doNotTrack: "1" }, storage: asAdapter(fakeStorage()) };
    assert.equal(isCollectionAllowed(env, true), false);
  });

  it("respeta Global Privacy Control", () => {
    const env = { navigator: { globalPrivacyControl: true }, storage: asAdapter(fakeStorage()) };
    assert.equal(isCollectionAllowed(env, true), false);
  });

  it("respeta la clave intellops-optout en localStorage", () => {
    const env = {
      navigator: {},
      storage: asAdapter(fakeStorage({ "intellops-optout": "1" })),
    };
    assert.equal(isCollectionAllowed(env, true), false);
  });
});
