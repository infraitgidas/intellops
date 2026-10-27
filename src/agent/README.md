# Agente RUM de navegador (B.1, ISS-B-01)

Implementación del contrato [`docs/architecture/ContratoAgenteRUM.md`](../../docs/architecture/ContratoAgenteRUM.md) v0.1:
captura TTFB, FCP y errores JS no manejados, agrupa en batches y los envía a
`POST /telemetry/metrics` y `POST /telemetry/exceptions`.

Sin dependencias de runtime ni polyfills. El único artefacto publicado es
`dist/rum.js`: un IIFE minificado de **~4.3 KB gzip** (tope del contrato: 30 KB,
objetivo 20 KB). `dist/` está en `.gitignore`: se genera con `npm run build`.

## Uso

```html
<script src="/rum.js"></script>
<script>
  IntellOpsRUM.init({
    apiKey: "ilp_...",              // API key de la aplicación (nunca se versiona)
    endpoint: "https://ingesta.example.com",
    consent: true,                  // sin consentimiento no se recolecta (§9)
    sampleRate: 1,                  // 0..1, muestreo determinista por sesión (§5)
  });
</script>
```

## Comandos

```bash
cd src/agent
npm install
npm run build       # genera dist/rum.js y verifica el presupuesto gzip
npm test            # 78 tests con el runner nativo de Node (node --test)
npm run check-size  # mide un dist/rum.js ya construido
```

## Verificación E2E contra la ingesta

```bash
npm run build
INTELLOPS_API_KEY=ilp_... INTELLOPS_ENDPOINT=http://localhost:8000 node scripts/e2e.mjs
```

Emite un page view con TTFB y una excepción con PII, y falla si la ingesta no
responde 202 con los eventos aceptados. La API key se pasa por entorno: nunca se
escribe en el repositorio.

## Demo

`demo/index.html` carga `../dist/rum.js` (ejecutá `npm run build` antes) y
permite iniciar el agente contra la ingesta local y provocar errores,
promesas rechazadas y un mensaje con PII para ver la redacción en el servidor.

```bash
cd src/agent && npm run build
python3 -m http.server 8080   # desde src/agent
# abrir http://localhost:8080/demo/
```

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `src/index.js` | inicialización, ciclo de vida, flush y contadores |
| `src/capture.js` | TTFB, FCP, normalización de excepciones y deduplicación |
| `src/session.js` | `session_id`, rotación y muestreo determinista |
| `src/queue.js` | cola acotada y partición en requests |
| `src/transport.js` | `fetch` keepalive, reintentos y circuito abierto |
| `src/privacy.js` | saneado de URL, redacción de PII, DNT/GPC y opt-out |
| `src/constants.js` | números del contrato en un solo lugar |

## Fuera de alcance v0.1

LCP, CLS, INP, XHR latency, rage clicks (B.7, diferible a v1.1), persistencia
local de payloads, `sendBeacon` (§4) e idempotencia por `batch_id` (OD-05).
