import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { createQueue, splitIntoRequests } from "../src/queue.js";

describe("cola acotada (§6)", () => {
  it("descarta los eventos más antiguos al desbordar y los contabiliza", () => {
    const queue = createQueue(3);
    queue.push("a");
    queue.push("b");
    queue.push("c");
    queue.push("d");
    assert.equal(queue.length, 3);
    assert.equal(queue.dropped, 1);
    assert.deepEqual(queue.take(3), ["b", "c", "d"]);
  });

  it("respeta el cap de eventos por request", () => {
    const queue = createQueue();
    for (let i = 0; i < 10; i += 1) queue.push({ n: i });
    assert.equal(queue.take(4).length, 4);
    assert.equal(queue.length, 6);
  });

  it("respeta el cap de bytes serializados (§6)", () => {
    const queue = createQueue();
    for (let i = 0; i < 10; i += 1) queue.push({ n: i, pad: "x".repeat(100) });
    const taken = queue.take(10, 400);
    const bytes = taken.reduce((total, event) => total + JSON.stringify(event).length, 0);
    assert.ok(bytes <= 400, `bytes=${bytes}`);
    assert.equal(taken.length, 3);
  });

  it("siempre entrega al menos un evento aunque supere el cap de bytes", () => {
    const queue = createQueue();
    queue.push({ pad: "x".repeat(1000) });
    assert.equal(queue.take(10, 100).length, 1);
  });

  it("take devuelve vacío con la cola vacía", () => {
    const queue = createQueue();
    assert.deepEqual(queue.take(5), []);
  });
});

describe("partición en requests (§6)", () => {
  it("parte en chunks de 400 eventos como máximo", () => {
    const events = Array.from({ length: 401 }, (_, index) => ({ index }));
    const chunks = splitIntoRequests(events.map((event) => ({ n: event.index })));
    assert.equal(chunks.length, 2);
    assert.equal(chunks[0].length, 400);
    assert.equal(chunks[1].length, 1);
  });

  it("parte por cap de bytes", () => {
    const events = Array.from({ length: 10 }, () => ({ pad: "x".repeat(100) }));
    const chunks = splitIntoRequests(events, 400);
    for (const chunk of chunks) {
      const bytes = chunk.reduce((total, event) => total + JSON.stringify(event).length, 0);
      assert.ok(bytes <= 400, `bytes=${bytes}`);
    }
  });

  it("con lista vacía no produce requests", () => {
    assert.deepEqual(splitIntoRequests([]), []);
  });
});
