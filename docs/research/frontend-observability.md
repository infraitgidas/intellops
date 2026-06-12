# Frontend Observability: Estado del Arte — Research Document

- **Versión**: 1.0
- **Fecha**: 2026-06-11
- **Autores**: Equipo InfraIT GIDAS
- **Línea**: L5 — Observabilidad UX-Céntrica con OpenTelemetry
- **Propósito**: Documento de investigación sobre observabilidad desde el frontend, métricas de usuario real, metodologías, tendencias de industria y análisis predictivo para el proyecto IntellOps.

---

## Índice

1. [Introducción: ¿Qué es Frontend Observability?](#1-introducción-qué-es-frontend-observability)
2. [Metodología de Investigación](#2-metodología-de-investigación)
3. [Los Tres Pilares desde el Frontend](#3-los-tres-pilares-desde-el-frontend)
4. [Métricas de UX: Catálogo Completo](#4-métricas-de-ux-catálogo-completo)
5. [Core Web Vitals: Especificación Técnica](#5-core-web-vitals-especificación-técnica)
6. [RED Method para Frontend](#6-red-method-para-frontend)
7. [RUM vs Synthetic Monitoring](#7-rum-vs-synthetic-monitoring)
8. [OpenTelemetry en el Frontend](#8-opentelemetry-en-el-frontend)
9. [Geolocalización y Observabilidad Regional](#9-geolocalización-y-observabilidad-regional)
10. [Análisis Predictivo desde Señales de UX](#10-análisis-predictivo-desde-señales-de-ux)
11. [Herramientas de la Industria](#11-herramientas-de-la-industria)
12. [Tendencias 2025-2026](#12-tendencias-2025-2026)
13. [Referencias Bibliográficas](#13-referencias-bibliográficas)

---

## 1. Introducción: ¿Qué es Frontend Observability?

La observabilidad tradicional nace en sistemas distribuidos (MACE, 2009), enfocada en entender el estado interno de un sistema a partir de sus outputs externos. Durante años, esto significó monitorear servidores: CPU, RAM, disco, red. Pero hay un problema de base:

> **El servidor puede estar perfecto y el usuario frustrado.**

La observabilidad de frontend cambia el foco: del servidor al usuario. No pregunta "¿está funcionando el servicio?" sino "¿qué está experimentando el usuario?".

### 1.1. Definición Formal

> **Frontend Observability** es la práctica de instrumentar, recolectar, correlacionar y analizar señales (métricas, logs, trazas) desde el lado del cliente (navegador, app mobile) para entender, diagnosticar y anticipar la experiencia de usuario real.

Se diferencia del monitoreo tradicional en:

| Aspecto | Monitoreo Backend | Observabilidad Frontend |
|---------|------------------|------------------------|
| **Origen de datos** | Servidores, contenedores, APIs | Navegadores, dispositivos, redes de usuarios |
| **Naturaleza** | Controlada (entorno conocido) | No controlada (millones de entornos únicos) |
| **Variabilidad** | Baja (mismo hardware, misma red) | Alta (cada usuario es distinto) |
| **Métricas** | CPU, RAM, disco, throughput | Core Web Vitals, errores JS, interacciones |
| **Contexto** | "El servicio X falló" | "El usuario Y en ciudad Z con dispositivo W tuvo una experiencia mala" |
| **Valor** | Estabilidad del sistema | Satisfacción y retención de usuarios |

### 1.2. ¿Por qué es I+D+i?

La observabilidad de frontend es un área **activa de investigación** porque:

1. **No hay estandarización completa**: OpenTelemetry Browser es experimental (OpenTelemetry SIG Browser, 2026). No existe un estándar maduro para instrumentación de frontend.
2. **Privacidad vs datos**: Recolectar datos de usuario real implica navegar regulaciones (GDPR, CCPA) y anonimización — un problema abierto.
3. **Correlación señales**: Vincular una métrica de frontend (LCP > 4s) con una causa raíz en backend (DB lenta) requiere tracing distribuido completo, algo raramente implementado.
4. **Recursos escasos**: Los agentes de monitoreo compiten por recursos con la propia aplicación — el overhead debe ser mínimo (< 3%).
5. **Predictivo**: Usar ML sobre señales de UX para anticipar reclamos es un área con pocos papers publicados.

---

## 2. Metodología de Investigación

Este documento sigue una **Systematic Literature Review (SLR)** adaptada de Kitchenham & Charters (2007) combinada con **grey literature** (blogs técnicos, whitepapers, documentación de herramientas) dado que el tema tiene alta velocidad de cambio en la industria.

### 2.1. Período de Búsqueda

- **Principal**: 2020-2026
- **Clásicos**: 2000-2019 (trabajos fundacionales)

### 2.2. Fuentes

| Tipo | Fuentes |
|------|---------|
| **Académicas** | IEEE Xplore, ACM Digital Library, arXiv, Scopus, Google Scholar |
| **Técnicas** | W3C Specifications, MDN Web Docs, Chromium Blog, web.dev |
| **Industria** | Grafana Labs Blog, OpenTelemetry Documentation, Google Research, Datadog/Dynatrace whitepapers |
| **Comunidad** | CNCF Landscape, GitHub Awesome Lists, Discord/Slack de OTel |

### 2.3. Términos de Búsqueda

- `("frontend observability" OR "client-side monitoring" OR "RUM" OR "real user monitoring")`
- `("Core Web Vitals" OR "LCP" OR "CLS" OR "INP" OR "FCP" OR "TTFB")`
- `("OpenTelemetry browser" OR "OTel frontend" OR "web instrumentation")`
- `("predictive UX" OR "user complaint prediction" OR "proactive observability")`
- `("geolocated observability" OR "regional performance analysis")`
- `("RED method" OR "USE method" OR "apdex" OR "user satisfaction")`

### 2.4. Criterios de Inclusión/Exclusión

| Criterio | Inclusión | Exclusión |
|----------|-----------|-----------|
| **Idioma** | Inglés, español | Otros idiomas |
| **Tipo** | Papers revisados por pares, specs W3C, documentación oficial | Blog posts sin datos, opiniones no fundamentadas |
| **Relevancia** | Relacionado a frontend, UX, RUM, Web Vitals | Monitoreo exclusivamente backend |
| **Actualidad** | 2020-2026 (o trabajos fundacionales previos) | Obsoleto sin actualizaciones |

---

## 3. Los Tres Pilares desde el Frontend

La observabilidad clásica se sostiene en 3 pilares: **métricas**, **logs** y **trazas** (Sridharan, 2018). Desde el frontend, cada pilar tiene su equivalente:

### 3.1. Métricas de Frontend

Son datos numéricos agregados que describen el comportamiento de la aplicación en el navegador.

| Tipo de Métrica | Ejemplos | API Web |
|----------------|----------|---------|
| **Rendimiento de carga** | TTFB, FCP, LCP, DomContentLoaded | Navigation Timing API, Paint Timing API |
| **Estabilidad visual** | CLS, Layout Shift count | Layout Instability API |
| **Interactividad** | INP, FID, TBT | Event Timing API, Long Tasks API |
| **Red** | Resource timing, transfer size, protocol | Resource Timing API, Performance Observer |
| **Errores** | JS errors, promise rejections, unhandled exceptions | window.onerror, window.onunhandledrejection |
| **Memoria** | JS heap size, DOM nodes | Performance.memory (non-standard) |

**Valor**: Las métricas permiten **tendencias**, **alertas** y **SLIs/SLOs** desde la perspectiva del usuario.

### 3.2. Logs de Frontend

Son eventos discretos con contexto sobre lo que ocurrió en el navegador.

| Tipo de Log | Ejemplo | Recolección |
|------------|---------|-------------|
| **Errores JS** | `TypeError: Cannot read property 'x' of undefined` | `window.onerror` con stack trace |
| **Errores de red** | `FetchError: Failed to fetch /api/data` | `window.onunhandledrejection` |
| **Errores de recurso** | `GET https://cdn.com/image.png 404` | Performance Observer (resource error) |
| **Acciones de usuario** | `click #submit-button`, `route /dashboard` | Instrumentación manual |
| **Consola** | `console.warn`, `console.error` | Patch de console methods |
| **Transiciones de ruta** | `navigate /dashboard`, `navigate /settings` | History API + instrumentation |

**Valor**: Los logs permiten **debugging contextual**. Un error JS sin contexto no sirve. Un error JS con trace ID, sesión, y User Health Score permite RCA.

### 3.3. Trazas de Frontend

Son el registro del viaje completo de una interacción de usuario a través del sistema.

```
[Usuario] → [Click en botón] → [Fetch a API] → [Backend] → [DB] → [Response] → [Render]
     ↑                                                                           ↑
     └─────────────────── TRAZA COMPLETA (traceId: abc-123) ────────────────────┘
```

En frontend, las trazas capturan:

| Evento en la Traza | Atributos Clave |
|-------------------|-----------------|
| **Navigation** | URL, previous URL, navigation type |
| **Page Load** | TTFB, FCP, LCP, DOM interactive, load event |
| **Fetch/XHR** | method, URL, status, duration, request body size |
| **User Interaction** | target, type, duration, INP contribution |
| **Resource Load** | src, type, duration, size, protocol |
| **Component Render** | component name, render time, props (anonimizados) |

**Valor**: Las trazas permiten **correlación causa-efecto**. Ver que un INP alto está causado por un fetch lento a un endpoint específico que a su vez está lento por una query pesada en la DB.

---

## 4. Métricas de UX: Catálogo Completo

### 4.1. Métricas de Carga (Loading)

#### TTFB — Time to First Byte

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Tiempo entre que el navegador inicia la solicitud y recibe el primer byte de respuesta del servidor |
| **API** | `Navigation Timing API` → `performance.getEntriesByType('navigation')[0].responseStart` |
| **Threshold Google** | Bueno: < 0.8s, Necesita mejora: 0.8-1.8s, Malo: > 1.8s |
| **Percentil clave** | p75 |
| **Afectado por** | Server processing time, network latency, CDN cache hit/miss, DNS resolution, TLS negotiation |
| **Especificación** | W3C Navigation Timing Level 2 |
| **Valor para el proyecto** | Indicador primario de latencia de backend percibida por el usuario |

#### FCP — First Contentful Paint

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Tiempo desde que la página comienza a cargar hasta que cualquier contenido (texto, imagen, SVG, canvas) se renderiza por primera vez |
| **API** | `Paint Timing API` → `performance.getEntriesByType('paint')` |
| **Threshold Google** | Bueno: < 1.8s, Necesita mejora: 1.8-3.0s, Malo: > 3.0s |
| **Percentil clave** | p75 |
| **Afectado por** | Render-blocking resources (CSS, JS), server response time, font loading |
| **Especificación** | W3C Paint Timing |
| **Valor para el proyecto** | Primera impresión del usuario sobre la velocidad del sitio |

#### LCP — Largest Contentful Paint

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Tiempo hasta que el elemento de contenido más grande (imagen, video, bloque de texto) es visible en la ventana |
| **API** | `LargestContentfulPaint API` → `PerformanceObserver` |
| **Threshold Google** | Bueno: < 2.5s, Necesita mejora: 2.5-4.0s, Malo: > 4.0s |
| **Percentil clave** | p75 |
| **Afectado por** | Imágenes sin optimizar, server-side rendering lento, render-blocking JS, TTFB alto |
| **Estado Core Web Vital** | **Stable** |
| **Valor para el proyecto** | Métrica Core más importante para loading. Correlacionada con bounce rate. |
| **Referencia** | Walton (2020) — web.dev |

### 4.2. Métricas de Interactividad (Interactivity)

#### INP — Interaction to Next Paint

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Mide la latencia de todas las interacciones del usuario (click, tap, teclado) y reporta el percentil peor (o cercano al peor) |
| **API** | `Event Timing API` → `PerformanceObserver('event')` |
| **Threshold Google** | Bueno: < 200ms, Necesita mejora: 200-500ms, Malo: > 500ms |
| **Percentil clave** | p75 (aunque se observa el peor percentil) |
| **Reemplaza a** | FID (First Input Delay) — retirado como Core Web Vital en 2024 |
| **Estado Core Web Vital** | **Stable** (desde marzo 2024) |
| **Afectado por** | Long tasks en main thread, renderizado pesado, third-party scripts, evaluación JS |
| **Valor para el proyecto** | La métrica más compleja de mejorar. Requiere tracing de interacciones. |
| **Nota académica** | INP es un área activa de investigación: cómo predecir INP alto antes de que ocurra es un problema abierto |

#### FID — First Input Delay

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Tiempo entre la primera interacción del usuario y el momento en que el navegador puede procesarla |
| **API** | `Event Timing API` (deprecated en favor de INP) |
| **Threshold** | Bueno: < 100ms, Necesita mejora: 100-300ms, Malo: > 300ms |
| **Estado** | **Retirado** como Core Web Vital en 2024. INP es su reemplazo. |

#### TBT — Total Blocking Time

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Suma de tiempo entre FCP y TTI donde el main thread estuvo bloqueado (long tasks > 50ms) |
| **API** | Solo medible en lab (Lighthouse). No disponible en field directamente. |
| **Threshold** | Bueno: < 200ms, Necesita mejora: 200-600ms, Malo: > 600ms |
| **Valor para el proyecto** | Proxy de laboratorio para INP. Útil en CI/CD para detectar regresiones. |

### 4.3. Métricas de Estabilidad Visual (Visual Stability)

#### CLS — Cumulative Layout Shift

| Propiedad | Valor |
|-----------|-------|
| **Definición** | Suma de todos los cambios de layout inesperados durante toda la vida de la página. Calculado como `impact fraction * distance fraction` |
| **API** | `Layout Instability API` → `PerformanceObserver('layout-shift')` |
| **Threshold Google** | Bueno: < 0.1, Necesita mejora: 0.1-0.25, Malo: > 0.25 |
| **Percentil clave** | p75 |
| **Estado Core Web Vital** | **Stable** |
| **Afectado por** | Imágenes sin dimensiones, ads, embeds, fonts, injected content |
| **Valor para el proyecto** | Crítica para UX. CLS alto en páginas con datos dinámicos/dashboards es un problema conocido. |

### 4.4. Métricas de Red (Network)

#### Page Load Metrics

| Métrica | Definición | API |
|---------|------------|-----|
| **DNS Lookup** | Tiempo de resolución DNS | `domainLookupEnd - domainLookupStart` |
| **TCP Connection** | Tiempo de conexión TCP | `connectEnd - connectStart` |
| **TLS Negotiation** | Tiempo de handshake TLS | `secureConnectionStart` |
| **Request + Response** | Tiempo total de solicitud | `responseEnd - requestStart` |
| **Transfer Size** | Tamaño total transferido (compressed) | `transferSize` |
| **Resource Count** | Número de recursos cargados | `performance.getEntriesByType('resource').length` |

#### HTTP RED Metrics (Rate, Errors, Duration)

| Métrica | Frontend | Backend |
|---------|----------|---------|
| **Rate** | Requests/min desde el navegador | Requests/min al servidor |
| **Errors** | HTTP 4xx/5xx + JS errors + resource load failures | HTTP 5xx + excepciones |
| **Duration** | Tiempo de respuesta percibido | Tiempo de procesamiento |

### 4.5. Sesiones y Usuarios (Session-Level)

| Métrica | Definición |
|---------|------------|
| **Session Duration** | Tiempo total que un usuario pasa en la aplicación |
| **Page Views / Session** | Cantidad de páginas visitadas por sesión |
| **Bounce Rate** | % de sesiones de una sola página |
| **User ID** | Identificador anonimizado del usuario (hash, no PII) |
| **Session ID** | Identificador de sesión único |

### 4.6. Métricas de Calidad de Experiencia (QoE)

Más allá de métricas técnicas, la QoE intenta medir cómo el usuario **percibe** la experiencia:

| Métrica | Definición | Medición |
|---------|------------|----------|
| **Apdex** | Application Performance Index — % de requests que cumplen threshold de satisfacción | (Satisfied + Tolerating / 2) / Total |
| **JS Error Rate** | % de sesiones con al menos un error JS no manejado | (Sesiones con errores / Sesiones totales) * 100 |
| **Console Error Rate** | % de páginas con errores en consola | Logs de console.error / páginas totales |
| **DOM Mutations** | Cantidad de cambios en el DOM después de carga inicial | PerformanceObserver('mutations') |
| **Memory Leak** | Crecimiento de heap JS entre páginas | `performance.memory.usedJSHeapSize` |
| **Time to Interactive** | Tiempo hasta que la página es completamente interactiva | Lab metric (Lighthouse) |

---

## 5. Core Web Vitals: Especificación Técnica

### 5.1. Ciclo de Vida de los Core Web Vitals

Google define un ciclo de vida en 3 fases para cada métrica (web.dev, 2024):

```
Experimental → Pending (≥ 6 meses) → Stable
```

Estado actual (junio 2026):
- **LCP**: Stable
- **CLS**: Stable
- **INP**: Stable (promovido en marzo 2024, reemplazando a FID)

### 5.2. Cálculo de Percentiles

Los Core Web Vitals se reportan al **p75** (percentil 75), segmentado por:

- **Tipo de dispositivo**: mobile, desktop, tablet
- **Tipo de conexión**: 4G, 3G, 2G, WiFi
- **Geografía**: país, región

> **Interpretación**: Si tu LCP p75 es 2.0s, significa que el 75% de tus usuarios tienen LCP ≤ 2.0s. El 25% restante está peor.

### 5.3. Herramientas de Medición

| Herramienta | Tipo | Cobertura | Precisión |
|-------------|------|-----------|-----------|
| **Chrome User Experience Report (CrUX)** | Field (datos reales de Chrome) | Millones de URLs | Alta (datos reales) |
| **PageSpeed Insights** | Field + Lab | Una URL por vez | Alta |
| **Search Console (Core Web Vitals report)** | Field (CrUX data) | Todo el sitio | Alta |
| **web-vitals JS library** | Field (RUM propio) | Tus usuarios | Máxima (tus datos) |
| **Lighthouse** | Lab (simulado) | Una URL por vez | Buena para debugging |
| **Chrome DevTools** | Lab | Una sesión | Buena para debugging |

### 5.4. web-vitals JavaScript Library

Google provee la librería [`web-vitals`](https://github.com/GoogleChrome/web-vitals) (Walton, 2020) para medir Core Web Vitals en producción:

```javascript
import {onCLS, onINP, onLCP, onFCP, onTTFB} from 'web-vitals';

function sendToAnalytics(metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,        // 'good' | 'needs-improvement' | 'poor'
    delta: metric.value - metric.entries[0].startTime,
    id: metric.id,
    navigationType: metric.navigationType,
    // + contexto: userID, sessionID, geolocation, device
  });
  navigator.sendBeacon('/analytics', body);
}

onCLS(sendToAnalytics);
onINP(sendToAnalytics);
onLCP(sendToAnalytics);
onFCP(sendToAnalytics);
onTTFB(sendToAnalytics);
```

**Bundle size**: ~1.5KB gzip. La librería más liviana posible.

### 5.5. Limitaciones Conocidas de Core Web Vitals

1. **Solo Chrome**: CrUX solo recolecta datos de usuarios de Chrome. Usuarios de Safari, Firefox, Edge no están representados.
2. **Agregado**: CrUX da datos agregados por URL, no por sesión ni por usuario.
3. **Sin contexto**: Un LCP malo no dice *por qué* — requiere debugging adicional.
4. **Sin trazabilidad**: CrUX no vincula una métrica mala con una traza específica.
5. **Ventana móvil**: CrUX promedia 28 días — no detecta regresiones rápidas.

---

## 6. RED Method para Frontend

El **RED Method** (Rate, Errors, Duration) fue popularizado por Tom Wilkie (Grafana Labs, 2015) para monitoreo de servicios. Se puede adaptar al frontend:

### 6.1. RED para Page Loads

| Señal | Métrica | Frontend |
|-------|---------|----------|
| **Rate** | Page views por minuto | `pageViews / min` |
| **Errors** | % de páginas con errores | `(JS errors + fetch fails) / page views` |
| **Duration** | Tiempo de carga p75 | `LCP p75` |

### 6.2. RED para API Calls (desde frontend)

| Señal | Métrica | Frontend |
|-------|---------|----------|
| **Rate** | Requests por minuto por endpoint | `fetch('/api/x') count / min` |
| **Errors** | HTTP 4xx/5xx + timeout | `(status >= 400) / total requests` |
| **Duration** | Latencia de respuesta p95 | `responseEnd - requestStart` |

### 6.3. RED para User Interactions

| Señal | Métrica | Frontend |
|-------|---------|----------|
| **Rate** | Interacciones por minuto | `clicks + taps + keypress / min` |
| **Errors** | % de interacciones con error | `(interactions con error / total interactions)` |
| **Duration** | INP p75 | Event Timing API |

### 6.4. Implementación RED en Grafana

```
Métrica: red_rate{service="frontend", type="page_load"}
Métrica: red_errors{service="frontend", type="page_load"}
Métrica: red_duration{service="frontend", type="page_load"}
```

Cada métrica se etiqueta con:
- `service`: frontend | backend | api
- `type`: page_load | api_call | interaction | resource
- `route`: /dashboard | /api/users (anonimizado)
- `geography`: ar-bsas | us-nyc | es-mad
- `device`: mobile | desktop | tablet

---

## 7. RUM vs Synthetic Monitoring

### 7.1. Real User Monitoring (RUM)

| Aspecto | Descripción |
|---------|-------------|
| **Qué es** | Monitoreo basado en usuarios reales que visitan la aplicación |
| **Datos** | Reales, variados, contexto completo (dispositivo, red, geografía) |
| **Ventaja** | Refleja la experiencia real de todos tus usuarios |
| **Desventaja** | No puedes reproducir el problema, datos no controlados |
| **Cobertura** | 100% del tráfico (o muestreo configurable) |
| **Overhead** | ~10-50KB de JS en el navegador |
| **Herramientas** | web-vitals, OpenTelemetry JS, Datadog RUM, New Relic Browser, Grafana Faro |

### 7.2. Synthetic Monitoring

| Aspecto | Descripción |
|---------|-------------|
| **Qué es** | Monitoreo basado en scripts que simulan usuarios desde ubicaciones controladas |
| **Datos** | Controlados, reproducibles, entornos conocidos |
| **Ventaja** | Detectas problemas antes de que afecten a usuarios reales. Reproducible. |
| **Desventaja** | No refleja la experiencia real de usuarios con dispositivos/redes reales |
| **Cobertura** | Limitada a los escenarios definidos y ubicaciones configuradas |
| **Overhead** | No afecta a usuarios reales |
| **Herramientas** | Lighthouse CI, Playwright, Cypress, k6, Locust, Grafana k6 |

### 7.3. Cuándo Usar Cada Uno

```
Synthetic → CI/CD (pre-deploy), canary testing, alertas de disponibilidad
RUM       → Producción (post-deploy), experiencia real, tendencias, SLOs
Ambos     → Estrategia completa: synthetic detecta, RUM confirma
```

### 7.4. Estrategia Híbrida para IntellOps

```
1. CI/CD (Synthetic)
   ├── Lighthouse CI en cada PR → bloquea si LCP > 2.5s o CLS > 0.1
   ├── Playwright + OTel → trazas de journeys sintéticos
   └── k6/Locust → carga sintética con validación de métricas

2. Producción (RUM)
   ├── web-vitals + OTel JS → Core Web Vitals de usuarios reales
   ├── PerformanceObserver → trazas de interacciones reales
   └── Error tracking → JS errors + console.error

3. Correlación
   ├── Trace ID en synthetic y RUM → mismo span en Tempo
   └── User Health Score → alertas cuando score < threshold
```

---

## 8. OpenTelemetry en el Frontend

### 8.1. Estado Actual

OpenTelemetry para browser es **experimental** (OpenTelemetry Browser SIG, 2026). La instrumentación del lado del cliente está mayormente **unspecified**, lo que significa que no hay especificación formal — cada SDK implementa lo que puede.

**Paquetes disponibles (JavaScript):**

| Paquete | Estado | Propósito |
|---------|--------|-----------|
| `@opentelemetry/sdk-trace-web` | Estable | SDK base para web |
| `@opentelemetry/instrumentation-document-load` | Estable | Trazas de carga de documento |
| `@opentelemetry/instrumentation-xml-http-request` | Estable | Trazas de fetch/XHR |
| `@opentelemetry/instrumentation-user-interaction` | Experimental | Trazas de clicks, inputs |
| `@opentelemetry/context-zone` | Estable | Zone.js context manager (Angular) |
| `@opentelemetry/auto-instrumentations-web` | Experimental | Meta-package con todas las instrumentaciones |
| `@opentelemetry/exporter-trace-otlp-http` | Estable | Export OTLP via HTTP |

### 8.2. Arquitectura de Instrumentación Frontend

```
[Navegador del Usuario]
│
├── web-vitals (Core Web Vitals)
├── OTel JS SDK (trazas)
├── PerformanceObserver (métricas ad-hoc)
├── Error tracking (logs de errores)
│
└──→ OTLP HTTP ──→ [OpenTelemetry Collector]
                         │
                    ┌────┼────┐
                    ▼    ▼    ▼
                  Tempo Loki Mimir
                  (trazas) (logs) (métricas)
                    │
                    ▼
                 Grafana
              (dashboards + alertas)
```

### 8.3. Lo que se Puede Instrumentar Hoy

| Señal | Disponible | Calidad |
|-------|-----------|---------|
| **Document Load** (navigation span) | ✅ OTel nativo | Buena |
| **Fetch/XHR Spans** | ✅ OTel nativo | Buena |
| **Resource Timing Spans** | ⚠️ Parcial (via manual) | Media |
| **User Interaction Spans** | ⚠️ OTel experimental | Experimental |
| **Long Tasks** | ⚠️ PerformanceObserver + OTel custom | Manual |
| **Layout Shifts** | ⚠️ PerformanceObserver + OTel custom | Manual |
| **JS Errors** | ❌ No hay OTel nativo. Log manual. | Manual |
| **Memory** | ❌ No hay API estandarizada | Manual |

### 8.4. El Gap de Investigación

> **No existe un agente RUM unificado open-source que capture Core Web Vitals + trazas OTel + errores JS + contexto de sesión con bundle < 30KB.**

Este es exactamente el nicho donde IntellOps (Federico, Fase 2) puede hacer un aporte de I+D+i.

---

## 9. Geolocalización y Observabilidad Regional

### 9.1. Por qué es Importante

Un usuario en Buenos Aires con fibra óptica tiene experiencia muy distinta a uno en Salta con 4G. Sin geolocalización, los promedios globales esconden problemas regionales.

### 9.2. Datos que Afectan por Región

| Factor | Impacto en UX |
|--------|---------------|
| **Latencia de red** | TTFB, LCP |
| **CDN coverage** | Cache hit/miss ratio, latency |
| **Tipo de conexión predominante** | 4G vs 5G vs WiFi vs DSL |
| **Dispositivos predominantes** | Gama baja/alta, RAM disponible |
| **Horario pico** | Contención de recursos, degradación |

### 9.3. Implementación en RUM

```javascript
// Geolocalización via IP → base de datos GeoIP (MaxMind, ip2location)
const geolocation = {
  country: 'AR',
  region: 'B',
  city: 'Buenos Aires',
  lat: -34.61,
  lng: -58.38,
  timezone: 'America/Argentina/Buenos_Aires',
  connection: navigator.connection?.effectiveType, // '4g', '3g', '2g'
};

// Cada métrica se etiqueta con estos datos
analytics.send({
  ...webVitalMetric,
  geolocation,
});
```

### 9.4. Visualización en Grafana

```
Panel: Worldmap panel
Query: rate(rum_lcp{geography="*"}[5m])
Thresholds: verde < 2.5s, amarillo < 4.0s, rojo > 4.0s
Tooltip: país, LCP p75, sample size
```

### 9.5. Alertas Geolocalizadas

> **Alerta**: "LCP p75 en región AR-B supera 4.0s durante los últimos 15 minutos. Sample size: 500 usuarios afectados."

Esto permite detectar problemas de CDN regional, censura de ISP, o degradación de peering que no afectan al resto del mundo.

---

## 10. Análisis Predictivo desde Señales de UX

### 10.1. El Problema

Hoy, la mayoría de los equipos se enteran de problemas de UX cuando:

1. Un usuario se queja (ticket de soporte)
2. Las métricas de negocio caen (conversión, retención)
3. Un dashboard muestra una anomalía (reactivo)

**El objetivo predictivo**: detectar que un usuario *va a tener* un problema antes de que lo experimente.

### 10.2. Señales Predictivas Tempranas

| Señal | Predice | Ventana de anticipación |
|-------|---------|------------------------|
| **LCP > 3.0s trending up** | Abandono de página en próxima navegación | 1-2 páginas |
| **INP > 300ms trending up** | Reclamo por "aplicación lenta" | 2-3 interacciones |
| **JS Error Rate > 2%** | Reclamo por "no funciona" | 1-2 minutos |
| **CLS > 0.2** | Reclamo por "página rota" | 1 sesión |
| **Memory heap creciendo** | Crash de navegador en próximas páginas | 3-5 minutos |
| **API Latency trending up** | Degradación general de UX | 5-10 minutos |

### 10.3. User Health Score (UHS)

El UHS es un score compuesto (0-100) que sintetiza múltiples señales de UX en un solo valor accionable.

**Propuesta de diseño para IntellOps:**

```python
# Pesos configurables vía API
WEIGHTS = {
    'lcp_score': 0.25,      # Loading performance
    'inp_score': 0.25,      # Interactivity
    'cls_score': 0.15,      # Visual stability
    'error_rate': 0.20,     # Error rate (invertido)
    'api_latency': 0.15,    # Backend latency percibida
}

def calculate_uhs(metrics):
    """
    User Health Score: 0-100
    90-100: Excelente (verde)
    70-89:  Bueno (verde claro)
    50-69:  Regular (amarillo)
    30-49:  Malo (naranja)
     0-29:  Crítico (rojo)
    """
    lcp_score = score_lcp(metrics['lcp_p75'])
    inp_score = score_inp(metrics['inp_p75'])
    cls_score = score_cls(metrics['cls_p75'])
    error_score = score_errors(metrics['error_rate_p75'])
    api_score = score_api(metrics['api_latency_p95'])

    uhs = (
        WEIGHTS['lcp_score'] * lcp_score +
        WEIGHTS['inp_score'] * inp_score +
        WEIGHTS['cls_score'] * cls_score +
        WEIGHTS['error_rate'] * error_score +
        WEIGHTS['api_latency'] * api_score
    )
    return round(uhs, 1)
```

### 10.4. Modelo Predictivo de Reclamos

**Features** (entrada del modelo):
- LCP p75 (últimos 5 min)
- INP p75 (últimos 5 min)
- CLS p75 (últimos 5 min)
- JS Error Rate (últimos 5 min)
- API Latency p95 (últimos 5 min)
- User Health Score (últimos 5 min)
- Tendencia de UHS (últimos 30 min)
- Hora del día
- Día de la semana
- Geografía
- Versión del frontend

**Target** (salida):
- `complaint_probability`: 0.0 - 1.0 (probabilidad de reclamo en próxima hora)
- `expected_impact`: número estimado de usuarios afectados

**Algoritmo**: Random Forest classifier (liviano, < 50MB RAM) con threshold dinámico.

**Validación**:
- Precisión target: > 80%
- Recall target: > 75%
- F1 target: > 0.75

### 10.5. Integración con Alertas Multicanal

```
User Health Score < 60
  └→ ¿Severidad?
       ├─ < 30: Crítico → WhatsApp + Telegram + Mail
       ├─ 30-49: Alto  → Telegram + Mail
       ├─ 50-69: Medio → Mail (daily digest)
       └─ > 70: Bueno  → No alerta

Complaint Probability > 0.75
  └→ Alerta predictiva: "Se estima que usuarios en región X comenzarán a reportar problemas en los próximos 30 minutos debido a degradación de LCP (3.8s p75). Causa probable: CDN edge en X con latencia alta."
```

---

## 11. Herramientas de la Industria

### 11.1. Plataformas Completas

| Herramienta | RUM | Synthetic | Trazas | Logs | Core Web Vitals | Costo |
|-------------|-----|-----------|--------|------|-----------------|-------|
| **Datadog RUM** | ✅ | ✅ | ✅ | ✅ | ✅ | $$$ |
| **New Relic Browser** | ✅ | ✅ | ✅ | ✅ | ✅ | $$$ |
| **Dynatrace RUM** | ✅ | ✅ | ✅ | ✅ | ✅ | $$$$ |
| **Grafana Faro** | ✅ | ❌ | ✅ | ✅ | ✅ | Gratis (OSS) |
| **OpenTelemetry + Tempo** | ⚠️ (experimental) | ✅ | ✅ | ✅ | ⚠️ | Gratis (OSS) |
| **Sentry** | ✅ | ❌ | ✅ | ✅ | ⚠️ (básico) | Freemium |
| **LogRocket** | ✅ | ❌ | ❌ | ✅ | ✅ | $$ |
| **FullStory** | ✅ | ❌ | ❌ | ❌ | ✅ | $$$ |

### 11.2. Librerías y SDKs Open-Source

| Librería | Bundle Size | Core Web Vitals | OTel | Trazas | Errores |
|----------|-------------|-----------------|------|--------|---------|
| **web-vitals** (Google) | ~1.5KB | ✅ Completo | ❌ | ❌ | ❌ |
| **OTel JS SDK** | ~15KB | ⚠️ (manual) | ✅ | ✅ | ⚠️ (manual) |
| **Grafana Faro SDK** | ~10KB | ✅ | ✅ | ✅ | ✅ |
| **Sentry Browser SDK** | ~25KB | ⚠️ | ❌ | ❌ | ✅ |
| **posthog-js** | ~15KB | ✅ | ❌ | ❌ | ⚠️ |

### 11.3. Grafana Faro — El Referente Open-Source

Grafana Faro (antes Grafana Agent for RUM) es el proyecto open-source más cercano a una solución completa de frontend observability:

**Características**:
- Core Web Vitals out-of-the-box
- Trazas OTel con contexto de sesión
- Logs de errores JS
- Session replay (experimental)
- Export a Grafana Cloud o self-managed

**Bundle size**: ~10KB gzip

**Gap**: Faro está orientado a Grafana Cloud. Para self-hosted con recursos escasos, la configuración es compleja y el backend (Tempo + Loki + Mimir) requiere ~1GB RAM.

---

## 12. Tendencias 2025-2026

### 12.1. INP como Nuevo Core Web Vital

El reemplazo de FID por INP (estable desde marzo 2024) marca un cambio fundamental: ya no importa solo la *primera* interacción, sino **todas** las interacciones. Esto implica:

- Mayor énfasis en long tasks y main thread
- Necesidad de tracking de interacciones continuo (no solo first input)
- Oportunidad para ML predictivo: anticipar INP alto antes de que ocurra

### 12.2. OpenTelemetry Browser se Estabiliza

El Browser SIG de OTel está trabajando activamente en la especificación para browser. Se espera:

- **2026-2027**: Spec estable para instrumentación de browser
- **Soporte nativo** para Core Web Vitals en OTel
- **Context propagation** mejorada entre service workers y main thread

### 12.3. IA Generativa para RCA de Frontend

Aplicación de LLMs (locales o cloud) para:

- Explicar por qué un LCP es alto en lenguaje natural
- Correlacionar errores JS con cambios de release
- GenerarSuggested fixes basados en patrones históricos
- Automatizar rollback cuando User Health Score cae por debajo de threshold

### 12.4. Correlación Traza-Log-Métrica Unificada

El stack LGTM (Loki, Grafana, Tempo, Mimir) de Grafana Labs permite por primera vez:

- Navegar de una traza lenta (Tempo) al log específico (Loki)
- Ver la métrica de CPU del servidor en el momento exacto (Mimir)
- Todo desde un mismo panel en Grafana

**Esta capacidad aplicada a frontend** (traza de usuario → log de error → métrica de dispositivo) es un área virgen.

### 12.5. Privacidad por Diseño

Con regulaciones más estrictas (GDPR, CCPA, LGPD en Brasil), la recolección de datos de frontend debe:

- Anonimizar IDs de usuario (hashing, no almacenar PII)
- Permitir opt-out por usuario
- No trackear en modos incógnito
- Tener política de retención clara (< 90 días para datos crudos)

---

## 13. Referencias Bibliográficas

### 13.1. Estándares W3C

- W3C Navigation Timing Level 2. *W3C Recommendation*. https://www.w3.org/TR/navigation-timing-2/
- W3C Resource Timing Level 2. *W3C Recommendation*. https://www.w3.org/TR/resource-timing-2/
- W3C Paint Timing. *W3C Recommendation*. https://www.w3.org/TR/paint-timing/
- W3C Event Timing. *W3C Candidate Recommendation*. https://www.w3.org/TR/event-timing/
- W3C Layout Instability. *W3C Candidate Recommendation*. https://www.w3.org/TR/layout-instability/
- W3C Performance Timeline. *W3C Candidate Recommendation Draft*, May 2025. https://www.w3.org/TR/performance-timeline/
- W3C Trace Context. *W3C Recommendation*. https://www.w3.org/TR/trace-context/
- W3C User Timing Level 2. *W3C Candidate Recommendation*. https://www.w3.org/TR/user-timing-2/
- W3C Large Contentful Paint. *W3C Working Draft*. https://www.w3.org/TR/largest-contentful-paint/
- W3C Long Tasks API. *W3C Working Draft*. https://www.w3.org/TR/longtasks/

### 13.2. Google Web Vitals

- Walton, P. (2020). Web Vitals. *web.dev*. https://web.dev/articles/vitals
- Walton, P. (2020). Defining the Core Web Vitals metrics thresholds. *web.dev*.
- Walton, P. (2020). Best practices for measuring Web Vitals in the field. *web.dev*.
- Google Chrome Team. (2024). Interaction to Next Paint (INP). *web.dev*. https://web.dev/articles/inp
- Google Chrome Team. (2024). Largest Contentful Paint (LCP). *web.dev*. https://web.dev/articles/lcp
- Google Chrome Team. (2024). Cumulative Layout Shift (CLS). *web.dev*. https://web.dev/articles/cls
- Google Chrome Team. (2024). INP launches as a new Core Web Vital. *Chromium Blog*. https://blog.chromium.org/2024/03/inp-launches-as-new-core-web-vital.html

### 13.3. OpenTelemetry

- OpenTelemetry Specification v1.33.0. CNCF. https://opentelemetry.io/docs/specs/otel/
- OpenTelemetry JS SDK Documentation. https://opentelemetry.io/docs/languages/js/
- OpenTelemetry Browser Getting Started. https://opentelemetry.io/docs/languages/js/getting-started/browser/
- OpenTelemetry Browser SIG. GitHub. https://github.com/open-telemetry/community#sig-browser
- OpenTelemetry Auto-Instrumentations Web. GitHub. https://github.com/open-telemetry/opentelemetry-js-contrib

### 13.4. Grafana LGTM

- Grafana Tempo Documentation. https://grafana.com/docs/tempo/latest/
- Grafana Loki Documentation. https://grafana.com/docs/loki/latest/
- Grafana Faro (RUM). https://grafana.com/docs/grafana-cloud/monitor-applications/faro/
- Wilkie, T. (2015). The RED Method: How to Instrument Your Services. *Grafana Labs Blog*.
- Grafana Labs. (2025). Best practices for traces. https://grafana.com/docs/tempo/latest/set-up-for-tracing/best-practices/

### 13.5. Libros y Trabajos Académicos

- Sridharan, C. (2018). *Distributed Systems Observability*. O'Reilly Media. ISBN: 978-1492033448.
- Kitchenham, B. & Charters, S. (2007). Guidelines for performing Systematic Literature Reviews in Software Engineering. *EBSE Technical Report*, Keele University.
- MACE (2009). Control Theory for Observability. Definición original de observabilidad en sistemas.
- Dang, Y. et al. (2019). AIOps: Real-World Challenges and Research Innovations. *IEEE/ACM ICSE-SEIP*.
- Notaro, P. et al. (2021). A Systematic Mapping Study on AIOps. *Journal of Systems and Software*, 168.
- Ahmed, T. et al. (2024). Towards Incident Response with Large Language Models. *arXiv:2401.08754*.
- Jiang, Y. et al. (2023). LLM-based Root Cause Analysis for Cloud Incidents. *ACM SIGOPS*.
- Schmid, P. et al. (2024). Anomaly Detection in Time Series: A Comprehensive Evaluation. *Proc. VLDB Endowment*.
- Chen, Z. et al. (2024). Auto-Remediation with LLMs: A Case Study. *IEEE/ACM ICSE*.

### 13.6. Performance y UX

- Google Chrome Team. (2024). The Science Behind Web Vitals. *Google Research Blog*.
- Web Almanac by HTTP Archive (2025). Performance Chapter. https://almanac.httparchive.org/
- CrUX Dashboard. Chrome User Experience Report. https://developer.chrome.com/docs/crux/
- Lighthouse Performance Scoring. https://developer.chrome.com/docs/lighthouse/performance/
- Nielsen, J. (1993). *Usability Engineering*. Morgan Kaufmann. — Trabajo fundacional sobre UX metrics.
- Sevcik, P. (2023). The User Experience Metrics That Matter. *Catchpoint Blog*.

### 13.7. Proyectos Relacionados

- web-vitals (Google). https://github.com/GoogleChrome/web-vitals
- Grafana Faro. https://github.com/grafana/faro-web-sdk
- OpenTelemetry JS Contrib. https://github.com/open-telemetry/opentelemetry-js-contrib
- Sentry Browser SDK. https://github.com/getsentry/sentry-javascript
- PostHog. https://github.com/PostHog/posthog

---

## Apéndice A: Glosario de Métricas

| Sigla | Nombre | Unidad | Core Web Vital | API de Medición |
|-------|--------|--------|----------------|-----------------|
| **TTFB** | Time to First Byte | ms | ❌ | Navigation Timing |
| **FCP** | First Contentful Paint | ms | ❌ | Paint Timing |
| **LCP** | Largest Contentful Paint | ms | ✅ **Sí** | LargestContentfulPaint |
| **INP** | Interaction to Next Paint | ms | ✅ **Sí** | Event Timing |
| **CLS** | Cumulative Layout Shift | score | ✅ **Sí** | Layout Instability |
| **FID** | First Input Delay | ms | ❌ (retirado) | Event Timing |
| **TBT** | Total Blocking Time | ms | ❌ (lab) | Long Tasks |
| **SI** | Speed Index | ms | ❌ | Lighthouse |
| **TTI** | Time to Interactive | ms | ❌ | Lighthouse |
| **DCL** | DOM Content Loaded | ms | ❌ | Navigation Timing |
| **BT** | Bounce Rate | % | ❌ | Analytics |

## Apéndice B: Guía de Implementación Rápida

Para implementar RUM en IntellOps con el stack definido (Federico, Fase 2):

```javascript
// 1. Instalar dependencias
// npm install @opentelemetry/sdk-trace-web @opentelemetry/instrumentation-document-load
// npm install @opentelemetry/exporter-trace-otlp-http web-vitals

// 2. Inicializar OTel + Web Vitals
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { onCLS, onINP, onLCP, onFCP, onTTFB } from 'web-vitals';

const provider = new WebTracerProvider({
  spanProcessors: [
    // Export a OTel Collector
    new BatchSpanProcessor(new OTLPTraceExporter({
      url: 'http://localhost:4318/v1/traces',
    })),
  ],
});

provider.register();

// Instrumentaciones OTel
registerInstrumentations({
  instrumentations: [
    new DocumentLoadInstrumentation(),
    new XMLHttpRequestInstrumentation(),
  ],
});

// Core Web Vitals → Loki via OTel logs
function sendWebVital(metric) {
  // Convertir a formato OTel LogRecord y enviar
  const body = {
    traceId: provider.activeSpan?.spanContext().traceId,
    metric: metric.name,
    value: metric.value,
    rating: metric.rating,
    navigationType: metric.navigationType,
    timestamp: Date.now(),
    userId: anonymizedUserId,
    sessionId: sessionId,
    geolocation: geoData,
    device: navigator.userAgent,
  };
  navigator.sendBeacon('/otel/v1/logs', JSON.stringify(body));
}

onLCP(sendWebVital);
onINP(sendWebVital);
onCLS(sendWebVital);
```

---

*Documento vivo. Versión 1.0 — Junio 2026. Equipo InfraIT GIDAS — UTN FrLP.*
