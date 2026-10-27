// Entorno de navegador falso para los tests del agente RUM.
// Mantiene los mocks explícitos: sin jsdom ni frameworks (ISS-B-01).

/** Storage en memoria con la misma interfaz que Storage. */
export function fakeStorage(initial = {}) {
  const map = new Map(Object.entries(initial));
  return {
    getItem: (key) => (map.has(key) ? map.get(key) : null),
    setItem: (key, value) => void map.set(key, String(value)),
    removeItem: (key) => void map.delete(key),
    get size() {
      return map.size;
    },
  };
}

/** Adapta un Storage con API del navegador a la interfaz interna ({get,set,remove}). */
export function asAdapter(storage) {
  return {
    get: (key) => storage.getItem(key),
    set: (key, value) => storage.setItem(key, value),
    remove: (key) => storage.removeItem(key),
  };
}

/** Performance mínima: navigation timing y paint entries configurables. */
export function fakePerformance({ timeOrigin = 1_700_000_000_000, navigation, paint = [] } = {}) {
  return {
    timeOrigin,
    getEntriesByType: (type) => {
      if (type === "navigation") return navigation ? [navigation] : [];
      if (type === "paint") return paint;
      return [];
    },
  };
}

/**
 * PerformanceObserver falso: captura el callback para emitir entradas de paint
 * de forma controlada desde el test.
 */
export function fakeObserverFactory() {
  const observers = [];
  class FakeObserver {
    constructor(callback) {
      this.callback = callback;
      this.disconnected = false;
      observers.push(this);
    }
    observe() {}
    disconnect() {
      this.disconnected = true;
    }
    emit(entries) {
      if (!this.disconnected) this.callback({ getEntries: () => entries });
    }
  }
  return { Observer: FakeObserver, observers };
}

/** fetch falso con respuestas encoladas y registro de requests. */
export function fakeFetch(responses = [{ status: 202, body: { accepted: 1, rejected: [] } }]) {
  const calls = [];
  const queue = [...responses];
  const fn = async (url, init) => {
    calls.push({ url, init, body: JSON.parse(init.body) });
    const next = queue.length > 1 ? queue.shift() : queue[0];
    if (next instanceof Error) throw next;
    const status = next.status ?? 202;
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => next.body ?? {},
    };
  };
  fn.calls = calls;
  return fn;
}

/** EventTarget mínimo para `window` y `document`. */
export function fakeTarget(props = {}) {
  const listeners = new Map();
  return {
    ...props,
    listeners,
    addEventListener(type, handler) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(handler);
    },
    removeEventListener(type, handler) {
      const list = listeners.get(type) || [];
      const index = list.indexOf(handler);
      if (index >= 0) list.splice(index, 1);
    },
    dispatch(type, event = {}) {
      for (const handler of listeners.get(type) || []) handler(event);
    },
  };
}

/**
 * Entorno completo. `tick(ms)` avanza el reloj controlado por el test para los
 * backoffs de reintento sin esperas reales.
 */
export function fakeEnv(options = {}) {
  const { Observer, observers } = fakeObserverFactory();
  const fetch = options.fetch || fakeFetch();
  const sessionStorage = options.sessionStorage || fakeStorage();
  const localStorage = options.localStorage || fakeStorage();
  const document = fakeTarget({ visibilityState: "visible" });
  const window = fakeTarget({});
  const env = {
    window,
    document,
    navigator: options.navigator || { userAgent: "test-agent/1.0" },
    performance: options.performance || fakePerformance(),
    PerformanceObserver: Observer,
    fetch,
    AbortController: globalThis.AbortController,
    crypto: options.crypto || globalThis.crypto,
    location: options.location || { href: "https://shop.example.com/product/42?token=abc", origin: "https://shop.example.com" },
    storage: asAdapter(sessionStorage),
    optOutStorage: asAdapter(localStorage),
  };
  return { env, window, document, fetch, observers, sessionStorage, localStorage };
}

/** Espera a que se resuelvan las promesas pendientes del microtask queue. */
export const flushMicrotasks = () => new Promise((resolve) => setImmediate(resolve));
