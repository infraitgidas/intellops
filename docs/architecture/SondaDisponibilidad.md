# Sonda de disponibilidad (B.13)

Sonda HTTP mínima: mide **disponibilidad** de un sitio desde un solo origen y la
reporta por el mismo camino de ingesta que el agente RUM. No es un componente
aparte con base de datos propia: es un productor de eventos RUM.

Decisiones y alcance: `odd/tasks/b13-sonda-http.md`. Fuera de alcance por D2 y
R.4 (2027): TLS, DNS y multi-origen.

## Qué mide

Una corrida es un `GET` al target. Se registran tres cosas por ejecución:

| Dato | Dónde queda | Cómo se lee |
|------|-------------|-------------|
| Disponibilidad (1/0) | métrica `AVAILABILITY`, unidad `count` | `AVG(value)` por bucket en `GET /metrics/query` = razón de uptime |
| Latencia (ms) | métrica `TTFB`, unidad `ms` | `AVG(value)` por bucket, comparable con la latencia RUM |

La latencia se toma al recibir los headers y **el body no se lee**: es el tiempo
al primer byte, no el tiempo total de descarga. Leerlo mediría otra cosa y un
sitio arriba con un body lento podría registrarse como `timeout`.
| Código de estado HTTP | `rum_metric.metadata.http_status` | `GET /metrics/probes`, por ejecución |

Un status `>= 400` es servicio no disponible (outcome `http_error`); la latencia
**sí** se registra, porque hubo respuesta. Un timeout o un error de conexión son
indisponibilidad explícita (outcomes `timeout` y `connection_error`) y **no**
inventan latencia: no hay TTFB que medir.

No se modela el status como métrica a propósito: `AVG(404, 200)` no significa
nada. El promedio de un código de estado es un error conceptual, no un dato.

## Cómo se ejecuta

```bash
python -m probe
```

Variables de entorno (`ProbeSettings`, prefijo `PROBE_`):

| Variable | Default | Descripción |
|----------|---------|-------------|
| `PROBE_TARGET_URL` | — (requerida) | Origen único medido; debe empezar con `http://` o `https://` |
| `PROBE_API_KEY` | — (requerida) | API key del tenant que reporta (`X-API-Key`) |
| `INGEST_BASE_URL` | `http://localhost:8000` | Base de la API de ingesta |
| `PROBE_INTERVAL_SECONDS` | `60` | Intervalo entre corridas; debe ser `> 0` |
| `PROBE_TIMEOUT_SECONDS` | `5` | Timeout de la corrida; debe ser `> 0` |
| `PROBE_APPLICATION_ID` | — (opcional) | `application_id` del evento; nunca es autoridad de tenant |

Una configuración inválida (target sin esquema, intervalo o timeout no
positivos) falla al construir, no en la primera corrida.

## Cómo reporta

El batch es un `RumEventBatch` normal contra `POST /telemetry/metrics`, con la
API key del tenant: la sonda no tiene camino privilegiado ni endpoint propio de
escritura. Cada evento lleva una sesión sintética estable derivada de **(tenant,
target)**: `uuid5` sobre el hash de la API key y la URL. La sesión entra en la
derivación porque `session_id` es la PK de `user_session` y su dueña es la
aplicación; sin el tenant, dos clientes que miden el mismo sitio compartirían
sesión y sus métricas se atribuirían o se descartarían al otro. El hash evita
codificar la API key en un identificador persistido.

El envío a la ingesta siempre lleva timeout acotado: una ingesta que no responde
no puede colgar el ciclo ni detener el intervalo configurado.

El payload se valida contra la política real de ingesta
(`api.domain.services.ingest_policy.validate_rum_event`) en los tests: si el
contrato cambia, la sonda falla en la suite, no en producción.

## Límites conocidos

- Un solo origen: la comparación multi-punto es R.4 (2027).
- Sin TLS ni DNS: son parte de R.4; acá `connection_error` los agrupa.
- Sin reintento: un ciclo fallido se registra y el siguiente intervalo vuelve a
  intentar. La sonda no acumula estado.- No se despliega como contenedor propio en este slice (ADR-0010 fija cuatro
  contenedores); el despliegue se decide en C.5 junto con el release.
