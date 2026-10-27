// Cola acotada y armado de batches.
// Contrato A.3 §6: cap de eventos por request, cap de bytes serializados y
// descarte de los eventos más antiguos ante desborde.

import {
  MAX_BYTES_PER_REQUEST,
  MAX_EVENTS_PER_REQUEST,
  MAX_QUEUED_EVENTS,
} from "./constants.js";

/**
 * Cola en memoria con tope duro. Al desbordar descarta los eventos más antiguos
 * y lo contabiliza: nunca crece sin límite ni persiste payloads (§9).
 */
export function createQueue(maxSize) {
  const limit = maxSize || MAX_QUEUED_EVENTS;
  const items = [];
  let dropped = 0;

  return {
    push(event) {
      if (items.length >= limit) {
        items.shift();
        dropped += 1;
      }
      items.push(event);
    },
    /** Extrae hasta `count` eventos, respetando el cap de bytes serializados. */
    take(count, maxBytes) {
      const byteCap = maxBytes || MAX_BYTES_PER_REQUEST;
      const eventCap = count || MAX_EVENTS_PER_REQUEST;
      const taken = [];
      let bytes = 0;
      while (items.length > 0 && taken.length < eventCap) {
        const candidate = items[0];
        const size = JSON.stringify(candidate).length;
        if (taken.length > 0 && bytes + size > byteCap) break;
        items.shift();
        taken.push(candidate);
        bytes += size;
      }
      return taken;
    },
    get length() {
      return items.length;
    },
    get dropped() {
      return dropped;
    },
    clear() {
      items.length = 0;
    },
  };
}

/** Envelope de métricas (`RumEventBatch`, §2.2) con su cap de bytes. */
export function buildMetricsEnvelope(schemaVersion, events) {
  return { schema_version: schemaVersion, events };
}

/** Envelope de excepciones (`JsExceptionBatch`, §2.3). */
export function buildExceptionsEnvelope(schemaVersion, events) {
  return { schema_version: schemaVersion, events };
}

/**
 * Parte eventos en varios requests: el servidor rechaza el batch completo si
 * `events` sale de 1..500, por eso el agente nunca supera 400 ni 32 KiB.
 */
export function splitIntoRequests(events, maxBytes) {
  const byteCap = maxBytes || MAX_BYTES_PER_REQUEST;
  const chunks = [];
  let current = [];
  let bytes = 0;
  for (const event of events) {
    const size = JSON.stringify(event).length;
    if (current.length >= MAX_EVENTS_PER_REQUEST || (current.length > 0 && bytes + size > byteCap)) {
      chunks.push(current);
      current = [];
      bytes = 0;
    }
    current.push(event);
    bytes += size;
  }
  if (current.length > 0) chunks.push(current);
  return chunks;
}
