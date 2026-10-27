import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildPageViewMetrics,
  canonicalErrorType,
  createExceptionGate,
  normalizeException,
  observeFcp,
  readTtfb,
} from "../src/capture.js";
import { fakePerformance, fakeObserverFactory } from "./helpers.js";

describe("TTFB (§2.2, AC-03)", () => {
  it("usa responseStart - requestStart y redondea a ms", () => {
    const performance = fakePerformance({
      navigation: { responseStart: 320.7, requestStart: 120.2 },
    });
    assert.equal(readTtfb(performance), 201);
  });

  it("devuelve undefined cuando no hay Navigation Timing API", () => {
    assert.equal(readTtfb(undefined), undefined);
    assert.equal(readTtfb(fakePerformance()), undefined);
  });

  it("devuelve undefined en lugar de 0 cuando los tiempos no son finitos", () => {
    const performance = fakePerformance({
      navigation: { responseStart: undefined, requestStart: 10 },
    });
    assert.equal(readTtfb(performance), undefined);
  });
});

describe("FCP (§2.2)", () => {
  it("toma el startTime de first-contentful-paint ya registrado", () => {
    const values = [];
    const performance = fakePerformance({
      paint: [
        { name: "first-paint", startTime: 90 },
        { name: "first-contentful-paint", startTime: 480.4 },
      ],
    });
    observeFcp({ performance }, (value) => values.push(value));
    assert.deepEqual(values, [480]);
  });

  it("emite el FCP cuando el observer lo entrega", () => {
    const { Observer, observers } = fakeObserverFactory();
    const values = [];
    observeFcp(
      { performance: fakePerformance(), PerformanceObserver: Observer },
      (value) => values.push(value),
    );
    assert.equal(observers.length, 1);
    observers[0].emit([{ name: "first-contentful-paint", startTime: 1234.4 }]);
    assert.deepEqual(values, [1234]);
    assert.equal(observers[0].disconnected, true);
  });

  it("no inventa un FCP de 0 cuando no ocurrió (AC-02)", () => {
    const metrics = buildPageViewMetrics(250, undefined);
    assert.deepEqual(metrics, [{ type: "TTFB", value: 250, unit: "ms" }]);
  });

  it("envía TTFB y FCP en el mismo page view", () => {
    const metrics = buildPageViewMetrics(250, 900);
    assert.deepEqual(metrics, [
      { type: "TTFB", value: 250, unit: "ms" },
      { type: "FCP", value: 900, unit: "ms" },
    ]);
  });
});

describe("error_type canónico (§2.3, AC-04)", () => {
  it("conserva los nombres del catálogo", () => {
    for (const name of ["TypeError", "RangeError", "ReferenceError", "EvalError"]) {
      assert.equal(canonicalErrorType(name, false), name);
    }
  });

  it("mapea nombres desconocidos a Other", () => {
    assert.equal(canonicalErrorType("VendorError", false), "Other");
    assert.equal(canonicalErrorType(undefined, false), "Other");
  });

  it("usa UnhandledRejection para promesas rechazadas", () => {
    assert.equal(canonicalErrorType("Error", true), "UnhandledRejection");
  });
});

describe("normalización de excepciones (§2.3)", () => {
  it("extrae tipo, mensaje y stack de un Error", () => {
    const error = new TypeError("x is not a function");
    error.stack = "TypeError: x is not a function\n    at app.js:1:1";
    const event = normalizeException(error, false);
    assert.equal(event.errorType, "TypeError");
    assert.equal(event.message, "x is not a function");
    assert.match(event.stackTrace, /app\.js:1:1/);
  });

  it("trunca message a 2000 y stack_trace a 20000", () => {
    const error = new RangeError("m".repeat(3000));
    error.stack = "s".repeat(30_000);
    const event = normalizeException(error, false);
    assert.equal(event.message.length, 2000);
    assert.equal(event.stackTrace.length, 20_000);
  });

  it("usa error_type como mensaje cuando no hay message", () => {
    const event = normalizeException(new TypeError(""), false);
    assert.equal(event.errorType, "TypeError");
    assert.equal(event.message, "TypeError");
  });

  it("acepta string y valor desconocido como fuente", () => {
    assert.equal(normalizeException("boom", false).message, "boom");
    assert.equal(normalizeException(undefined, true).errorType, "UnhandledRejection");
  });
});

describe("topes por sesión (§5)", () => {
  it("deduplica por huella dentro de 60 s", () => {
    let clock = 1_000;
    const accept = createExceptionGate(() => clock);
    assert.equal(accept("TypeError", "boom").accepted, true);
    assert.equal(accept("TypeError", "boom").accepted, false);
    clock += 60_001;
    assert.equal(accept("TypeError", "boom").accepted, true);
  });

  it("no deduplica tipos distintos con el mismo mensaje", () => {
    const accept = createExceptionGate(() => 0);
    assert.equal(accept("TypeError", "boom").accepted, true);
    assert.equal(accept("RangeError", "boom").accepted, true);
  });

  it("corta a 20 excepciones por sesión", () => {
    const accept = createExceptionGate(() => 0);
    for (let i = 0; i < 20; i += 1) {
      assert.equal(accept("Error", `boom-${i}`).accepted, true);
    }
    const extra = accept("Error", "boom-20");
    assert.equal(extra.accepted, false);
    assert.equal(extra.reason, "session_cap");
  });
});
