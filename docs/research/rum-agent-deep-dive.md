# RUM Agent: Investigación Profunda y Arquitectura

- **Versión**: 1.0
- **Fecha**: 2026-06-11
- **Autores**: Equipo InfraIT GIDAS
- **Propósito**: Documento de investigación técnica sobre agentes RUM (Real User Monitoring): arquitectura interna, APIs del navegador, métricas, optimización de bundle, privacidad y diseño propuesto para el agente RUM de IntellOps.

---

## Índice

1. [¿Qué es un Agente RUM? Anatomía Completa](#1-qué-es-un-agente-rum-anatomía-completa)
2. [Browser APIs Utilizadas](#2-browser-apis-utilizadas)
3. [Cómo se Mide Cada Métrica: Implementación](#3-cómo-se-mide-cada-métrica-implementación)
4. [OTel Browser SDK: Arquitectura Interna](#4-otel-browser-sdk-arquitectura-interna)
5. [Análisis de Bundles Existentes](#5-análisis-de-bundles-existentes)
6. [Estrategias de Optimización de Bundle](#6-estrategias-de-optimización-de-bundle)
7. [Privacidad y Anonimización](#7-privacidad-y-anonimización)
8. [Arquitectura Propuesta para IntellOps RUM](#8-arquitectura-propuesta-para-intellops-rum)
9. [Plan de Implementación](#9-plan-de-implementación)
10. [Referencias](#10-referencias)

---

## 1. ¿Qué es un Agente RUM? Anatomía Completa

### 1.1. Definición Técnica

Un **agente RUM** es un runtime JavaScript que se ejecuta en el navegador del usuario, en producción, y cuyo trabajo es:

1. **Observar** pasivamente el comportamiento del navegador y del usuario
2. **Recolectar** métricas, trazas y logs sin bloquear el hilo principal
3. **Procesar** los datos (anonimizar, muestrear, batch)
4. **Exportar** los datos a un backend de observabilidad vía OTLP HTTP

Todo esto con **overhead mínimo** (< 3% en Lighthouse, < 30KB bundle gzip).

### 1.2. Ciclo de Vida de un Agente RUM

```
CARGA DE LA PÁGINA
│
├── FASE 1: INIT (0ms)
│   ├── Se carga el JS del agente (async, no bloqueante)
│   ├── Se inicializa el tracer provider OTel
│   └── Se registran los PerformanceObservers
│       ├── Observer LCP
│       ├── Observer INP
│       ├── Observer CLS
│       ├── Observer FCP
│       └── Observer Resource Timing
│
├── FASE 2: RECOLECCIÓN (0ms - page lifecycle)
│   ├── PerformanceObservers emiten eventos
│   ├── Se capturan errores JS (window.onerror)
│   ├── Se capturan fetch/XHR (OTel instrumentation)
│   └── Se acumula contexto de sesión
│
├── FASE 3: PROCESAMIENTO (en cada evento)
│   ├── Los datos se transforman a formato OTel
│   ├── Se anonimiza PII (userID, URL params)
│   ├── Se aplica sampling (si corresponde)
│   └── Se agregan atributos de contexto
│
├── FASE 4: EXPORT (batch cada 5-30s)
│   ├── Se acumulan spans + logs en buffer
│   ├── BatchSpanProcessor exporta via OTLP HTTP
│   └── sendBeacon() para no bloquear descarga de página
│
└── FASE 5: DESCARGA DE PÁGINA
    └── sendBeacon() garantiza que los datos pendientes se envían
        incluso durante descarga del page (beforeunload)
```

### 1.3. Componentes Internos

```
┌──────────────────────────────────────────────────────────┐
│                    AGENTE RUM                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────┐   ┌──────────────────────────┐  │
│  │  Core Web Vitals    │   │  OTel Tracer Provider    │  │
│  │  (web-vitals wrap)  │   │  (WebTracerProvider)     │  │
│  │  ─ LCP              │   │  ─ Tracer                │  │
│  │  ─ INP              │   │  ─ Span Processor        │  │
│  │  ─ CLS              │   │  ─ Span Exporter         │  │
│  │  ─ FCP              │   │                          │  │
│  │  ─ TTFB             │   └──────────────────────────┘  │
│  └─────────────────────┘                                 │
│                                                          │
│  ┌─────────────────────┐   ┌──────────────────────────┐  │
│  │  Error Tracker      │   │  Session Context         │  │
│  │  ─ window.onerror   │   │  ─ userID (hash)         │  │
│  │  ─ unhandledRej     │   │  ─ sessionID (UUID)      │  │
│  │  ─ console.error    │   │  ─ device info           │  │
│  │                     │   │  ─ geolocation           │  │
│  └─────────────────────┘   └──────────────────────────┘  │
│                                                          │
│  ┌─────────────────────┐   ┌──────────────────────────┐  │
│  │  Instrumentations   │   │  Buffer + Exporter       │  │
│  │  ─ DocumentLoad     │   │  ─ BatchSpanProcessor    │  │
│  │  ─ XMLHttpRequest   │   │  ─ OTLP HTTP Exporter    │  │
│  │  ─ UserInteraction  │   │  ─ Retry logic           │  │
│  └─────────────────────┘   └──────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Browser APIs Utilizadas

### 2.1. Performance Timeline API (W3C)

La API base de la que todas las demás métricas dependen. Especificación W3C (Peña Moreno, 2025).

```javascript
// PerformanceObserver: la columna vertebral del agente RUM
const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  // Cada entrada tiene: name, entryType, startTime, duration
});

// Registrar qué tipos de entradas observar
observer.observe({ type: 'largest-contentful-paint', buffered: true });

// Tipos soportados (varía por navegador):
PerformanceObserver.supportedEntryTypes
// → ['element', 'event', 'first-input', 'largest-contentful-paint',
//    'layout-shift', 'longtask', 'navigation', 'paint',
//    'resource', 'mark', 'measure', 'script']
```

### 2.2. Navigation Timing API

Mide tiempos de navegación de la página. Especificación W3C.

```javascript
const navEntry = performance.getEntriesByType('navigation')[0];

// Métricas disponibles:
navEntry = {
  // Red
  domainLookupStart / domainLookupEnd,    // DNS resolution
  connectStart / connectEnd,               // TCP connection
  secureConnectionStart,                    // TLS handshake start
  requestStart,                             // HTTP request start
  responseStart,                            // First byte received
  responseEnd,                              // Last byte received
  
  // Documento
  domInteractive,                          // DOM ready
  domContentLoadedEventEnd,                // DCL finished
  loadEventEnd,                            // Page fully loaded
  
  // Tamaño
  transferSize,                            // Total bytes transferred
  encodedBodySize,                         // Body size (compressed)
  decodedBodySize,                         // Body size (uncompressed)
  
  // Tipo de navegación
  type: 'navigate' | 'reload' | 'back_forward' | 'prerender'
};

// TTFB = responseStart - requestStart (o responseStart - fetchStart)
// DCL = domContentLoadedEventEnd - fetchStart
// Load = loadEventEnd - fetchStart
```

### 2.3. Paint Timing API

Mide eventos de renderizado. Especificación W3C.

```javascript
// FCP - First Contentful Paint
const paintEntries = performance.getEntriesByType('paint');
// → [{ name: 'first-paint', startTime: 1234 },
//    { name: 'first-contentful-paint', startTime: 1456 }]

// Se mide con PerformanceObserver
const fcpObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  for (const entry of entries) {
    if (entry.name === 'first-contentful-paint') {
      const fcp = entry.startTime;
      // FCP < 1.8s → good
    }
  }
});
fcpObserver.observe({ type: 'paint', buffered: true });
```

### 2.4. LargestContentfulPaint API

```javascript
const lcpObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];
  // LCP puede actualizarse si se carga una imagen más grande después
  
  const lcp = {
    startTime: lastEntry.startTime,        // LCP value in ms
    size: lastEntry.size,                   // Element size in pixels
    id: lastEntry.id,                       // Element ID
    url: lastEntry.url,                     // Image URL (si es imagen)
    element: lastEntry.element?.tagName,    // 'IMG', 'DIV', 'P', etc.
    loadTime: lastEntry.loadTime,          // Resource load time
    renderTime: lastEntry.renderTime,      // Render time
  };
  
  // LCP < 2.5s → good
});
lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });

// Waiting for LCP to settle (might update)
// Google recommends listening until page fully loaded
setTimeout(() => {
  // LCP is final at this point
}, 5000);
```

### 2.5. Event Timing API

```javascript
// INP - Interaction to Next Paint
const inpObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  
  for (const entry of entries) {
    // entry type: 'first-input' o 'event'
    const interaction = {
      name: entry.name,                    // 'click', 'keydown', 'pointerdown'
      startTime: entry.startTime,
      duration: entry.duration,            // Processing time
      delay: entry.processingStart - entry.startTime,  // Input delay
      processingTime: entry.processingEnd - entry.processingStart,
      interactionId: entry.interactionId,  // Groups related events
      target: entry.target?.tagName || 'unknown',
    };
    
    // INP focuses on the worst interaction
    // INP < 200ms → good
  }
});
inpObserver.observe({ type: 'event', buffered: true, durationThreshold: 40 });

// Also observe 'first-input' for FID (legacy)
const fidObserver = new PerformanceObserver((list) => {
  const firstInput = list.getEntries()[0];
  // FID = firstInput.processingStart - firstInput.startTime
});
fidObserver.observe({ type: 'first-input', buffered: true });
```

### 2.6. Layout Instability API

```javascript
// CLS - Cumulative Layout Shift
const clsObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  
  for (const entry of entries) {
    if (!entry.hadRecentInput) {
      // Solo layout shifts SIN interacción del usuario
      const cls = {
        value: entry.value,                 // Layout shift score
        sources: entry.sources,             // Elements that shifted
      };
    }
  }
});
clsObserver.observe({ type: 'layout-shift', buffered: true });

// CLS acumulado: sumar todos los values
// CLS < 0.1 → good
```

### 2.7. Resource Timing API

```javascript
const resourceObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();  // PerformanceResourceTiming[]
  
  for (const entry of entries) {
    const resource = {
      name: entry.name,                   // URL del recurso
      initiatorType: entry.initiatorType, // 'script', 'img', 'fetch', 'link', etc.
      duration: entry.duration,
      transferSize: entry.transferSize,
      encodedBodySize: entry.encodedBodySize,
      decodedBodySize: entry.decodedBodySize,
      protocol: entry.nextHopProtocol,    // 'h2', 'http/1.1', etc.
      // Timing por fases
      dns: entry.domainLookupEnd - entry.domainLookupStart,
      tcp: entry.connectEnd - entry.connectStart,
      tls: entry.secureConnectionStart ? 
           entry.connectEnd - entry.secureConnectionStart : 0,
      ttfb: entry.responseStart - entry.requestStart,
      download: entry.responseEnd - entry.responseStart,
    };
  }
});
resourceObserver.observe({ type: 'resource', buffered: true });
```

### 2.8. Long Tasks API

```javascript
// Long Tasks: tareas en main thread que duran > 50ms
const ltObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  
  for (const entry of entries) {
    const longTask = {
      duration: entry.duration,
      startTime: entry.startTime,
      // Atributo que indica qué atribución tuvo
      attribution: entry.attribution?.[0]?.containerName,
    };
    // Cada long task contribuye a TBT (Total Blocking Time)
    // TBT contribution = max(0, entry.duration - 50)
  }
});
ltObserver.observe({ type: 'longtask', buffered: true });
```

### 2.9. Network Information API

```javascript
// Información de conexión del usuario
const connection = navigator.connection || navigator.mozConnection;

if (connection) {
  const netInfo = {
    effectiveType: connection.effectiveType,  // '4g', '3g', '2g', 'slow-2g'
    downlink: connection.downlink,             // Mbps estimado
    rtt: connection.rtt,                       // Round-trip time estimado
    saveData: connection.saveData,             // Modo ahorro de datos
  };
  
  // Escuchar cambios en la conexión
  connection.addEventListener('change', () => {
    // Recolectar nueva info de conexión
  });
}
```

### 2.10. Device & Browser Detection

```javascript
const device = {
  userAgent: navigator.userAgent,
  platform: navigator.platform,           // 'Win32', 'MacIntel', 'Linux x86_64'
  language: navigator.language,           // 'es-AR', 'en-US'
  languages: navigator.languages,
  hardwareConcurrency: navigator.hardwareConcurrency,  // Núcleos CPU
  deviceMemory: navigator.deviceMemory,    // GB de RAM (non-standard)
  maxTouchPoints: navigator.maxTouchPoints,
  
  // Screen
  screenWidth: screen.width,
  screenHeight: screen.height,
  colorDepth: screen.colorDepth,
  
  // Window
  viewportWidth: window.innerWidth,
  viewportHeight: window.innerHeight,
  
  // Storage
  localStorageAvailable: typeof localStorage !== 'undefined',
  sessionStorageAvailable: typeof sessionStorage !== 'undefined',
  cookiesEnabled: navigator.cookieEnabled,
};
```

### 2.11. Error Tracking APIs

```javascript
// 1. Global error handler
window.addEventListener('error', (event) => {
  const error = {
    message: event.message,               // Error message
    source: event.filename,               // Script URL
    line: event.lineno,                   // Line number
    col: event.colno,                      // Column number
    stack: event.error?.stack,            // Stack trace
    timestamp: Date.now(),
    type: 'js_error',
  };
  // Enviar a backend
});

// 2. Unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  const error = {
    message: event.reason?.message || 'Promise rejected',
    stack: event.reason?.stack,
    timestamp: Date.now(),
    type: 'unhandled_promise_rejection',
  };
});

// 3. Console.error capture
const originalConsoleError = console.error;
console.error = (...args) => {
  // Forward to original
  originalConsoleError.apply(console, args);
  // Capturar para analytics
  const error = {
    message: args.map(String).join(' '),
    timestamp: Date.now(),
    type: 'console_error',
  };
};
```

---

## 3. Cómo se Mide Cada Métrica: Implementación

### 3.1. LCP (Largest Contentful Paint)

```javascript
// Algorithm: 
// 1. Observer 'largest-contentful-paint' entries
// 2. Keep track of the latest entry (can update)
// 3. Report once the page is fully loaded

function measureLCP(onReport) {
  let latestEntry = null;
  
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    latestEntry = entries[entries.length - 1];
  });
  observer.observe({ type: 'largest-contentful-paint', buffered: true });

  // The LCP can update until the page is fully loaded
  // or user interacts with the page
  const callback = () => {
    if (latestEntry) {
      onReport({
        metric: 'LCP',
        value: latestEntry.startTime,
        rating: latestEntry.startTime <= 2500 ? 'good' 
              : latestEntry.startTime <= 4000 ? 'needs-improvement' 
              : 'poor',
        element: latestEntry.element?.tagName,
        size: latestEntry.size,
        url: latestEntry.url,
      });
    }
    observer.disconnect();
  };
  
  // Listen for load event or visibility change
  ['load', 'visibilitychange'].forEach(evt => 
    document.addEventListener(evt, callback, { once: true })
  );
}
```

### 3.2. INP (Interaction to Next Paint)

```javascript
// Algorithm (simplified):
// 1. Observe all 'event' entries with durationThreshold 0
// 2. Group by interactionId (a user interaction may have multiple events)
// 3. For each interaction, take the longest event duration
// 4. Report the P75 of the worst interactions

function measureINP(onReport) {
  const interactions = new Map();  // interactionId → max duration
  
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      // Only process user-initiated events
      if (entry.interactionId > 0) {
        const existing = interactions.get(entry.interactionId) || 0;
        // Take the longest duration in this interaction group
        interactions.set(entry.interactionId, Math.max(existing, entry.duration));
      }
    }
  });
  observer.observe({ type: 'event', buffered: true, durationThreshold: 0 });
  
  // Report periodically - aggregate to P75
  setInterval(() => {
    if (interactions.size > 0) {
      const values = Array.from(interactions.values()).sort((a, b) => a - b);
      const p75 = values[Math.floor(values.length * 0.75)];
      
      onReport({
        metric: 'INP',
        value: p75,
        rating: p75 <= 200 ? 'good' : p75 <= 500 ? 'needs-improvement' : 'poor',
        samples: values.length,
        worstInteraction: values[values.length - 1],
      });
    }
  }, 60000);  // Report every minute
}
```

### 3.3. CLS (Cumulative Layout Shift)

```javascript
// Algorithm:
// 1. Observe all 'layout-shift' entries
// 2. Sum all scores where hadRecentInput === false
// 3. Report final value when page is hidden/unloaded

function measureCLS(onReport) {
  let clsValue = 0;
  let sessionWindowValue = 0;
  let sessionWindowStart = 0;
  const SESSION_GAP_MS = 1000;  // 1 second gap between sessions
  const SESSION_MAX_MS = 5000;  // Max 5 seconds per session
  
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      // Exclude shifts caused by user input
      if (!entry.hadRecentInput) {
        // Session window logic (per Google's spec)
        const now = performance.now();
        if (now - sessionWindowStart > SESSION_MAX_MS || 
            now - sessionWindowStart > SESSION_GAP_MS) {
          // New session window
          sessionWindowValue = 0;
          sessionWindowStart = now;
        }
        sessionWindowValue += entry.value;
        clsValue = Math.max(clsValue, sessionWindowValue);
      }
    }
  });
  observer.observe({ type: 'layout-shift', buffered: true });
  
  // Report when page is being unloaded
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      onReport({
        metric: 'CLS',
        value: clsValue,
        rating: clsValue <= 0.1 ? 'good' 
              : clsValue <= 0.25 ? 'needs-improvement' 
              : 'poor',
      });
      observer.disconnect();
    }
  });
}
```

### 3.4. TTFB (Time to First Byte)

```javascript
function measureTTFB(onReport) {
  // Navigation Timing API
  const navEntry = performance.getEntriesByType('navigation')[0];
  
  if (navEntry) {
    const ttfb = navEntry.responseStart - navEntry.requestStart;
    
    onReport({
      metric: 'TTFB',
      value: ttfb,
      rating: ttfb <= 800 ? 'good' : ttfb <= 1800 ? 'needs-improvement' : 'poor',
      // Breakdown for diagnostics
      dns: navEntry.domainLookupEnd - navEntry.domainLookupStart,
      tls: navEntry.secureConnectionStart ? 
           navEntry.connectEnd - navEntry.secureConnectionStart : 0,
      tcp: navEntry.connectEnd - navEntry.connectStart,
      download: navEntry.responseEnd - navEntry.responseStart,
    });
  } else {
    // Fallback: use Resource Timing for the page itself
    const pageEntry = performance.getEntriesByType('resource')
      .find(r => r.name === window.location.href);
    if (pageEntry) {
      onReport({ metric: 'TTFB', value: pageEntry.responseStart - pageEntry.requestStart });
    }
  }
}
```

### 3.5. FCP (First Contentful Paint)

```javascript
function measureFCP(onReport) {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.name === 'first-contentful-paint') {
        onReport({
          metric: 'FCP',
          value: entry.startTime,
          rating: entry.startTime <= 1800 ? 'good' 
                : entry.startTime <= 3000 ? 'needs-improvement' 
                : 'poor',
        });
        observer.disconnect();
      }
    }
  });
  observer.observe({ type: 'paint', buffered: true });
}
```

---

## 4. OTel Browser SDK: Arquitectura Interna

### 4.1. Paquetes y Dependencias

El stack de OpenTelemetry para browser se compone de:

```
@opentelemetry/api           → API pública (interfaces, tipos)
@opentelemetry/sdk-trace-web  → WebTracerProvider, instrumentaciones
@opentelemetry/sdk-trace-base → SpanProcessors, Exporters base
@opentelemetry/exporter-trace-otlp-http → Export OTLP via HTTP/JSON
@opentelemetry/instrumentation-document-load → Traza de carga de página
@opentelemetry/instrumentation-xml-http-request → Traza de fetch/XHR
@opentelemetry/instrumentation-user-interaction → Traza de interacciones
@opentelemetry/context-zone  → Zone.js context manager (Angular)
@opentelemetry/context-base  → Context manager base
@opentelemetry/resources     → Resource attributes
@opentelemetry/semantic-conventions → Constantes semánticas OTel
```

**Bundle size del SDK completo**: ~15KB gzip (sin tree-shaking)

### 4.2. Flujo de Datos Interno

```
WebTracerProvider
  │
  ├── register() → establece el tracer provider global
  │
  ├── Tracer → createSpan()
  │     │
  │     ├── Span.start() → inicia un span
  │     │                    (atributos: nombre, kind, timestamp)
  │     │
  │     ├── Span.end() → finaliza el span
  │     │                  (atributos: duration, status)
  │     │
  │     └── Span.setAttribute() → enriquece el span
  │
  ├── SpanProcessor (BatchSpanProcessor)
  │     │
  │     ├── Buffer interno (256 spans por defecto)
  │     ├── Exporta en batch cada 5s (configurable)
  │     ├── Se vacía ante eventos de descarga de página
  │     └── Limite de 256 spans por batch
  │
  └── SpanExporter (OTLPTraceExporter)
        │
        ├── Serializa a OTLP protobuf o JSON
        ├── POST HTTP a endpoint configurado
        ├── Retry con backoff (3 intentos)
        └── sendBeacon() fallback si disponible
```

### 4.3. Instrumentaciones Disponibles

#### DocumentLoadInstrumentation

Genera un span raíz por cada carga de página:

```
documentLoad (span raíz)
  ├── documentFetch (red)
  ├── domInteractive (DOM parsing)
  ├── domContentLoadedEvent (DCL handlers)
  ├── domComplete (DOM complete)
  └── loadEvent (load handlers)
```

**Atributos que captura**:
- `http.url`, `http.response_content_length`
- `http.status_code` (si disponible)
- Timings de red (domainLookup, connect, etc.)

#### XMLHttpRequestInstrumentation

Genera un span por cada XMLHttpRequest o Fetch:

```
HTTP GET /api/data
  │
  ├── Atributos: http.method, http.url, http.status_code
  ├── Propagación: traceparent header
  └── Eventos: headers, body size, timings
```

**Propagación de contexto**: Agrega header `traceparent` a cada request saliente.
Formato: `00-{traceId}-{spanId}-{flags}`

#### UserInteractionInstrumentation (Experimental)

Genera spans por interacciones de usuario (click, submit, etc.):

```
click #submit-button
  │
  ├── Atributos: event.type, target.tagName, target.id, target.className
  └── Duración: desde el evento hasta el próximo paint
```

---

## 5. Análisis de Bundles Existentes

### 5.1. Comparativa de Tamaños

| Agente | Bundle (gzip) | Core Web Vitals | Trazas OTel | Errores | Contexto Sesión |
|--------|--------------|-----------------|-------------|---------|-----------------|
| **web-vitals (Google)** | **~1.5KB** | ✅ Completo | ❌ | ❌ | ❌ |
| **Grafana Faro** | **~10KB** | ✅ | ✅ | ✅ | ✅ |
| **OTel JS SDK alone** | **~15KB** | ❌ (manual) | ✅ | ❌ | ❌ |
| **Sentry Browser** | **~25KB** | ⚠️ (básico) | ❌ | ✅ | ✅ |
| **IntellOps (target)** | **< 20KB** | ✅ | ✅ | ✅ | ✅ |
| **Datadog RUM** | ~50KB | ✅ | ✅ | ✅ | ✅ |
| **Dynatrace RUM** | ~35KB | ✅ | ✅ | ✅ | ✅ |
| **New Relic Browser** | ~40KB | ✅ | ✅ | ❌ | ✅ |

### 5.2. Desglose de Bundle (Estimado para IntellOps)

```
Componente                    Tamaño (gzip)
────────────────────────────────────────────
web-vitals wrapper              2.0 KB
OTel TracerProvider + core      5.0 KB
OTel BatchSpanProcessor         1.5 KB
OTel OTLP HTTP Exporter         2.0 KB
Error tracker (onerror + rej)   1.0 KB
Session context + device info   1.5 KB
URL anonimization               0.5 KB
BUFFER + batch logic            1.0 KB
Instrumentación document-load   2.5 KB
Instrumentación fetch/XHR       2.5 KB
────────────────────────────────────────────
TOTAL ESTIMADO                 19.5 KB
Budget                         20.0 KB ✅
```

### 5.3. Análisis de Oportunidades de Optimización

| Estrategia | Ahorro estimado | Complejidad |
|------------|----------------|-------------|
| Tree-shaking de módulos OTel no usados | ~3-5KB | Baja (vite/webpack) |
| Reemplazar protobuf por JSON | ~2KB | Baja |
| Implementación custom vs OTel SDK completo | ~5-8KB | Alta |
| Lazy loading de instrumentaciones no críticas | ~1-2KB | Media |
| Minimización + compresión avanzada | ~1-2KB | Baja |
| Eliminar polyfills no necesarios (modern browsers only) | ~2-3KB | Media |

---

## 6. Estrategias de Optimización de Bundle

### 6.1. Tree-Shaking Agresivo

El OTel JS SDK es modular. Podemos importar solo lo que necesitamos:

```javascript
// ❌ Importación completa (grande)
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';

// ✅ Importación específica (más pequeña)
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web/build/src/WebTracerProvider';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base/build/src/BatchSpanProcessor';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http/build/src/OTLPTraceExporter';
```

### 6.2. Implementación Custom de OTel Export

Reemplazar el OTLP exporter completo por un fetch + sendBeacon manual:

```javascript
// Custom exporter liviano (~1KB vs ~2KB del OTel exporter)
class IntellOpsExporter {
  constructor(endpoint) {
    this.endpoint = endpoint;
    this.queue = [];
    this.flushInterval = setInterval(() => this.flush(), 5000);
  }

  export(spans, callback) {
    this.queue.push(...spans);
    if (this.queue.length >= 50) this.flush();
    callback({ code: 0 }); // Success
  }

  flush() {
    if (this.queue.length === 0) return;
    const payload = this.serialize(this.queue);
    
    if (document.visibilityState === 'hidden') {
      navigator.sendBeacon(this.endpoint, payload);
    } else {
      fetch(this.endpoint, { method: 'POST', body: payload, keepalive: true })
        .catch(() => {}); // Fire and forget
    }
    this.queue = [];
  }

  serialize(spans) {
    return JSON.stringify({
      resourceSpans: [{
        resource: { attributes: this.resourceAttributes },
        scopeSpans: [{ spans: spans.map(s => this.serializeSpan(s)) }]
      }]
    });
  }

  shutdown() {
    clearInterval(this.flushInterval);
    this.flush();
  }
}
```

### 6.3. Lazy Loading de Instrumentaciones

```javascript
// Solo carga instrumentaciones cuando son necesarias
const agent = {
  metrics: null,
  traces: null,
  errors: null,
};

// Cargar Core Web Vitals inmediatamente (crítico)
import('./metrics/web-vitals.js').then(mod => {
  agent.metrics = mod.init();
});

// Cargar trazas OTel después de FCP (no bloqueante)
requestIdleCallback(() => {
  import('./traces/otel-init.js').then(mod => {
    agent.traces = mod.init();
  });
});

// Cargar error tracking en el primer idle
window.addEventListener('load', () => {
  import('./errors/error-tracker.js').then(mod => {
    agent.errors = mod.init();
  });
});
```

### 6.4. Compresión y Minificación

Configuración de Vite para producción:

```javascript
// vite.config.js
export default {
  build: {
    target: 'es2020',  // Modern browsers only, fewer polyfills
    minify: 'esbuild', // Fast, good compression
    rollupOptions: {
      output: {
        manualChunks: undefined, // Single chunk es mejor para agente RUM
        compact: true,
      },
    },
    // Source maps only in dev
    sourcemap: false,
    // Report bundle size
    reportCompressedSize: true,
  },
};
```

---

## 7. Privacidad y Anonimización

### 7.1. Principios de Privacidad por Diseño

1. **No recolectar PII (Personally Identifiable Information)**: no emails, no nombres, no IPs completas
2. **Hashing de IDs de usuario**: userID → SHA-256 hash
3. **Anonimización de URLs**: `/users/123` → `/users/{id}`
4. **No trackear en modo incógnito** (si el navegador lo soporta)
5. **Opt-out por usuario**: `localStorage.setItem('intellops-optout', 'true')`
6. **Retención limitada**: datos crudos < 90 días

### 7.2. Implementación de Anonimización

```javascript
class Anonymizer {
  // Patrones de datos sensibles
  patterns = [
    { regex: /\/users\/\d+/g, replacement: '/users/{id}' },
    { regex: /\/orders\/[A-Z0-9-]+/g, replacement: '/orders/{id}' },
    { regex: /email=[^&]+/g, replacement: 'email=redacted' },
    { regex: /token=[^&]+/g, replacement: 'token=redacted' },
    { regex: /password=[^&]+/g, replacement: 'password=redacted' },
  ];

  anonymizeUrl(url) {
    let safe = url;
    for (const { regex, replacement } of this.patterns) {
      safe = safe.replace(regex, replacement);
    }
    return safe;
  }

  hashUserIdentifier(id) {
    if (!id) return 'anonymous';
    // Simple hash para no depender de Web Crypto API
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
      const char = id.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash |= 0; // Convert to 32bit integer
    }
    return 'u_' + Math.abs(hash).toString(36);
  }

  shouldTrack() {
    // No trackear en modo incógnito (limitado)
    try {
      return !localStorage.getItem('intellops-optout');
    } catch {
      return true; // localStorage no disponible = incógnito
    }
  }
}
```

### 7.3. Consentimiento y Transparencia

```html
<!-- El agente RUM incluye un banner de consentimiento configurable -->
<script>
window.intellopsAgentConfig = {
  consentRequired: true,
  consentMessage: "Este sitio utiliza IntellOps para monitorear la experiencia de usuario. Los datos son anónimos.",
  privacyPolicyUrl: "/privacidad",
};
</script>
<script src="/agent/rum.js" async defer></script>
```

---

## 8. Arquitectura Propuesta para IntellOps RUM

### 8.1. Estructura de Archivos

```
src/agent/
├── index.js                    ← Entry point, inicialización
├── config.js                   ← Configuración (endpoint, sampling, etc.)
├── metrics/
│   ├── core-web-vitals.js      ← LCP, INP, CLS, FCP, TTFB
│   ├── resource-timing.js      ← Resource Timing API
│   └── navigation-timing.js    ← Navigation Timing API
├── traces/
│   ├── otel-init.js            ← WebTracerProvider setup
│   ├── document-load.js        ← Document load instrumentation
│   └── fetch-instrumentation.js ← Fetch/XHR tracking
├── errors/
│   ├── error-tracker.js        ← window.onerror + unhandledrejection
│   └── console-capture.js      ← console.error capture
├── context/
│   ├── session.js              ← sessionID, userID (hash), pageID
│   ├── device.js               ← Device detection, browser, connection
│   └── geo.js                  ← Geolocation via IP (backend lookup)
├── export/
│   ├── exporter.js             ← Custom OTLP exporter
│   ├── buffer.js               ← Batch buffer with backpressure
│   └── retry.js                ← Retry logic with backoff
├── privacy/
│   ├── anonymizer.js           ← URL sanitization, PII removal
│   └── consent.js              ← Consent management
└── utils/
    ├── performance-observer.js ← Wrapper around PerformanceObserver
    └── timing.js               ← High-resolution timing helpers
```

### 8.2. Flujo de Inicialización

```javascript
// index.js — Entry point del agente RUM

import { Config } from './config.js';
import { Anonymizer } from './privacy/anonymizer.js';
import { ConsentManager } from './privacy/consent.js';
import { SessionContext } from './context/session.js';
import { DeviceInfo } from './context/device.js';
import { initWebVitals } from './metrics/core-web-vitals.js';
import { initOTel } from './traces/otel-init.js';
import { initErrorTracking } from './errors/error-tracker.js';
import { IntellOpsExporter } from './export/exporter.js';

class IntellOpsRUM {
  constructor(config = {}) {
    this.config = new Config(config);
    this.anonymizer = new Anonymizer();
    this.consent = new ConsentManager(this.config.consentRequired);
    this.session = new SessionContext();
    this.device = new DeviceInfo();
    this.exporter = new IntellOpsExporter(this.config.endpoint, {
      session: this.session,
      device: this.device,
      anonymizer: this.anonymizer,
    });

    if (!this.consent.isGranted()) return;

    this.init();
  }

  init() {
    // 1. Core Web Vitals
    initWebVitals(this.exporter);

    // 2. OTel Traces (post-load para no bloquear)
    window.addEventListener('load', () => {
      initOTel(this.exporter);
    }, { once: true });

    // 3. Error tracking inmediato
    initErrorTracking(this.exporter);
  }
}

// Exposición global
window.IntellOpsRUM = IntellOpsRUM;
```

### 8.3. Configuración

```javascript
// config.js
export class Config {
  constructor(config) {
    this.endpoint = config.endpoint || '/otel/v1/traces';
    this.sampleRate = config.sampleRate || 1.0;  // 1.0 = 100%
    this.consentRequired = config.consentRequired ?? false;
    this.flushInterval = config.flushInterval || 5000;  // 5s
    this.batchSize = config.batchSize || 50;
    this.retryAttempts = config.retryAttempts || 3;
    this.debug = config.debug ?? false;
  }
}
```

### 8.4. Formato de Datos Exportados

```javascript
// Cada payload enviado al OTel Collector
{
  "resourceSpans": [{
    "resource": {
      "attributes": [
        { "key": "service.name", "value": { "stringValue": "intellops-rum" } },
        { "key": "service.version", "value": { "stringValue": "0.1.0" } },
        { "key": "deployment.environment", "value": { "stringValue": "production" } }
      ]
    },
    "scopeSpans": [{
      "scope": { "name": "intellops-rum" },
      "spans": [
        {
          "traceId": "ab42124a3c573678d4d8b21ba52df3bf",
          "spanId": "5123fc802ffb5255",
          "parentSpanId": "cfb565047957cb0d",
          "name": "LCP",
          "kind": 4,  // SPAN_KIND_INTERNAL
          "startTimeUnixNano": "1606814247811266000",
          "endTimeUnixNano": "1606814247811266000",  // instant event
          "attributes": [
            { "key": "metric.name", "value": { "stringValue": "LCP" } },
            { "key": "metric.value", "value": { "doubleValue": 2340.5 } },
            { "key": "metric.rating", "value": { "stringValue": "good" } },
            { "key": "session.id", "value": { "stringValue": "sess_abc123" } },
            { "key": "user.id", "value": { "stringValue": "u_xyz789" } },
            { "key": "device.type", "value": { "stringValue": "mobile" } },
            { "key": "connection.type", "value": { "stringValue": "4g" } },
            { "key": "geography.country", "value": { "stringValue": "AR" } },
            { "key": "url.path", "value": { "stringValue": "/dashboard" } }
          ],
          "status": { "code": 0 }  // STATUS_OK
        }
      ]
    }]
  }]
}
```

---

## 9. Plan de Implementación

### 9.1. Fases de Desarrollo

```
FASE 1 — PoC Funcional (1 sprint)
  ├── Implementar Core Web Vitals con web-vitals library
  ├── Export a endpoint OTel
  ├── Bundle size: ~15KB
  └── Prueba: página HTML estática → datos en OTel Collector

FASE 2 — OTel Traces (1 sprint)
  ├── Agregar DocumentLoadInstrumentation
  ├── Agregar fetch/XHR instrumentation
  ├── Context propagation vía traceparent
  ├── Bundle size: ~18KB
  └── Prueba: traza completa (frontend → backend) en Tempo

FASE 3 — Error Tracking + Contexto (1 sprint)
  ├── window.onerror + unhandledrejection
  ├── Session context + device info + geolocation
  ├── Anonimización de URLs e IDs
  ├── Bundle size: ~20KB
  └── Prueba: error JS con stack trace + contexto en Loki

FASE 4 — Optimización + Pruebas (1 sprint)
  ├── Custom exporter vs OTel exporter (comparativa)
  ├── Bundle size audit con source-map-explorer
  ├── Lighthouse overhead test (con/sin agente)
  ├── Prueba cross-browser (Chrome, Firefox, Safari)
  └── Bundle size target: < 20KB final

FASE 5 — Integración con IntellOps (1 sprint)
  ├── Instrumentar el propio dashboard de IntellOps
  ├── User Health Score desde datos RUM
  ├── Dashboards en Grafana con datos RUM
  └── Alertas basadas en Core Web Vitals
```

### 9.2. Entregables por Fase

| Fase | Entregable | Criterio de Aceptación |
|------|-----------|------------------------|
| **F1** | `src/agent/rum.js` + Collector config | Core Web Vitals visibles en Grafana |
| **F2** | `src/agent/traces/otel-init.js` | Traza completa en Tempo |
| **F3** | `src/agent/errors/error-tracker.js` | Error JS con contexto en Loki |
| **F4** | Reporte de bundle audit + overhead | Bundle < 20KB, overhead < 3% |
| **F5** | Dashboard Grafana + alertas | Alertas de LCP/INP/CLS funcionando |

### 9.3. Roadmap de Investigación Asociada

| Sprint | Federico (RUM) | Romeo (ML) | Santiago (QA) |
|--------|---------------|------------|---------------|
| **3-4** | F1: PoC Core Web Vitals | Diseño User Health Score | Synthetic journeys OTel |
| **5-6** | F2: OTel Traces | Clasificador reclamos | Quality gates OTel |
| **7-8** | F3: Error Tracking + Contexto | User Health Score | Chaos engineering |
| **9-10** | F4: Optimización bundle | Agente RCA con LLM | Dashboard CBA |

---

## 10. Referencias

### Especificaciones W3C

- W3C Performance Timeline. Peña Moreno, N. (2025). *W3C Candidate Recommendation Draft*. https://www.w3.org/TR/performance-timeline/
- W3C Navigation Timing Level 2. https://www.w3.org/TR/navigation-timing-2/
- W3C Paint Timing. https://www.w3.org/TR/paint-timing/
- W3C Event Timing. https://www.w3.org/TR/event-timing/
- W3C Layout Instability. https://www.w3.org/TR/layout-instability/
- W3C Largest Contentful Paint. https://www.w3.org/TR/largest-contentful-paint/
- W3C Long Tasks. https://www.w3.org/TR/longtasks/
- W3C Resource Timing Level 2. https://www.w3.org/TR/resource-timing-2/
- W3C Trace Context. https://www.w3.org/TR/trace-context/

### Documentación Técnica

- MDN PerformanceObserver. https://developer.mozilla.org/en-US/docs/Web/API/PerformanceObserver
- MDN PerformanceEntry. https://developer.mozilla.org/en-US/docs/Web/API/PerformanceEntry
- Google web-vitals library. https://github.com/GoogleChrome/web-vitals
- OpenTelemetry Browser Getting Started. https://opentelemetry.io/docs/languages/js/getting-started/browser/
- OpenTelemetry JS SDK. https://www.npmjs.com/package/@opentelemetry/sdk-trace-web

### Google Web Vitals

- Walton, P. (2020). Web Vitals. *web.dev*. https://web.dev/articles/vitals
- Walton, P. (2020). Best practices for measuring Web Vitals in the field. *web.dev*.
- Google Chrome Team. (2024). Interaction to Next Paint (INP). *web.dev*.
- Google Chrome Team. (2024). Largest Contentful Paint (LCP). *web.dev*.
- Google Chrome Team. (2024). Cumulative Layout Shift (CLS). *web.dev*.

### Proyectos Relacionados

- Grafana Faro Web SDK. https://github.com/grafana/faro-web-sdk
- OpenTelemetry JS Contrib. https://github.com/open-telemetry/opentelemetry-js-contrib
- Sentry JavaScript SDK. https://github.com/getsentry/sentry-javascript
- Datadog Browser SDK (RUM). https://github.com/DataDog/browser-sdk

### Rendimiento y Bundle

- Vite Build Options. https://vitejs.dev/config/build-options.html
- esbuild Minification. https://esbuild.github.io/api/#minify
- Web Vitals Library Bundle Size. https://bundlephobia.com/package/web-vitals
- OTel JS SDK Bundle Analysis (manual).

---

*Documento vivo. Versión 1.0 — Junio 2026. Equipo InfraIT GIDAS — UTN FrLP.*
