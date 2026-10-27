import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { createSession, createSessionId, hash32, isSampled } from "../src/session.js";
import { asAdapter, fakeStorage } from "./helpers.js";

const ENV = (storage, crypto) => ({ storage: asAdapter(storage), crypto: crypto ?? globalThis.crypto });

describe("identidad de sesión (§2.1)", () => {
  it("genera un UUID v4 válido", () => {
    const id = createSessionId(globalThis.crypto);
    assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  });

  it("genera UUID con fallback cuando no hay contexto seguro (sin crypto)", () => {
    const id = createSessionId(undefined);
    assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  });

  it("reutiliza el session_id entre llamadas dentro de la ventana", () => {
    const storage = fakeStorage();
    let clock = 1_000;
    const first = createSession(ENV(storage), () => clock);
    clock += 60_000;
    const second = createSession(ENV(storage), () => clock);
    assert.equal(second.id, first.id);
  });

  it("rota la sesión tras 30 minutos de inactividad", () => {
    const storage = fakeStorage();
    let clock = 1_000;
    const first = createSession(ENV(storage), () => clock);
    clock += 30 * 60_000 + 1;
    const second = createSession(ENV(storage), () => clock);
    assert.notEqual(second.id, first.id);
  });

  it("rota la sesión tras 24 horas de vida aunque haya actividad", () => {
    const storage = fakeStorage();
    let clock = 1_000;
    const first = createSession(ENV(storage), () => clock);
    for (let i = 0; i < 48; i += 1) {
      clock += 30 * 60_000;
      createSession(ENV(storage), () => clock);
    }
    clock += 1;
    const rotated = createSession(ENV(storage), () => clock);
    assert.notEqual(rotated.id, first.id);
  });

  it("descarta un estado corrupto en sessionStorage", () => {
    const storage = fakeStorage({ "intellops-session": "no-es-json" });
    const session = createSession(ENV(storage), () => 1_000);
    assert.match(session.id, /^[0-9a-f-]{36}$/i);
  });
});

describe("muestreo determinista (§5)", () => {
  it("tasa 1.0 muestrea siempre y tasa 0 nunca", () => {
    assert.equal(isSampled("cualquier-sesion", 1), true);
    assert.equal(isSampled("cualquier-sesion", 0), false);
  });

  it("la decisión es estable para el mismo session_id y la misma tasa", () => {
    const id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";
    const first = isSampled(id, 0.5);
    for (let i = 0; i < 20; i += 1) assert.equal(isSampled(id, 0.5), first);
  });

  it("hash32 devuelve siempre el mismo valor para la misma entrada", () => {
    assert.equal(hash32("abc"), hash32("abc"));
    assert.notEqual(hash32("abc"), hash32("abd"));
  });

  it("usa el hash como umbral sobre 2^32 (§5)", () => {
    const id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";
    const bucket = hash32(id) / 4294967296;
    assert.equal(isSampled(id, bucket + 0.0001), true);
    if (bucket > 0.0001) {
      assert.equal(isSampled(id, bucket - 0.0001), false);
    }
  });
});
