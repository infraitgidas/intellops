# Proposal: ISS-B-10 — Despacho de alertas por Telegram y Email

**Cambio**: B.10 (#72). **Base**: `develop` + ISS-B-03 (`0007`) + ISS-B-14 (motor de reglas).
**Depende de**: B.3 (tabla `alert` y `GET /alerts`), B.14 (alertas `Pending` del motor de reglas).
**Lo consumen**: C.1 (E2E), C.3 (piloto medido) y C.5 (release).

## Intent

D1 dejó la v1 sin detección ML, pero M2 exige que una anomalía llegue **por Telegram** y que
el equipo reciba aviso por correo cuando la severidad es baja. B.14 ya crea la fila en `alert`
con severidad y mensaje en estado `Pending`; nada la despacha. `intellops-comms` es todavía un
placeholder que solo mantiene el proceso vivo, `src/comms/Dockerfile` empaqueta únicamente
`entrypoint.py` y la tabla `alert` nunca sale de `Pending`.

Este cambio cierra el último eslabón del camino crítico de M2: toma las alertas `Pending`, elige
canal por severidad, envía con retry y backoff exponencial y deja la alerta en `Sent` o `Failed`.

## Scope

### In Scope (RFC 2119)

- MUST: worker `intellops-comms` con ciclo propio, sin puertos, lote acotado por ciclo
  (default 20) (ADR-0010).
- MUST: routing por severidad configurable por entorno, con defaults `critical`/`high` →
  Telegram y `medium`/`low` → Email. Catálogo de la v1: Telegram y Email, **sin WhatsApp**.
- MUST: un destino por canal, tomado del entorno (`INTELLOPS_COMMS_TELEGRAM_CHAT_ID`,
  `INTELLOPS_COMMS_SMTP_TO`) y persistido en `alert.recipient` al despachar.
- MUST: retry con backoff exponencial (default 4 intentos, base 1 s, factor 2 → 1, 2, 4 s),
  configurable por entorno y con presupuesto total acotado.
- MUST: los 4xx que el proveedor marca permanentes (Telegram 400/403, SMTP 5xx) van a Failed sin
  reintento.
- MUST: éxito → `Sent` con `sent_at`, `channel_id` y `recipient`; intentos agotados → `Failed`
  con `sent_at` NULL.
- MUST: reclamar con `SELECT ... WHERE status = Pending ORDER BY created_at FOR UPDATE SKIP
  LOCKED LIMIT :batch` y despachar con el lock tomado.
- MUST: un canal sin credenciales NO es un fallo: la alerta queda Pending, se loguea una vez con
  el nombre del canal y `docker compose up` sigue funcionando sin secretos.
- MUST: secretos solo por entorno, nunca en código ni en logs; el log nombra id de alerta, canal
  e intento.
- MUST: sin dependencias nuevas de runtime (`smtplib` + `email.message`, `httpx` ya presente).
- MUST: tests unitarios con proveedores falsos, de contrato con el motor y de empaquetado de la
  imagen.
- SHOULD: el ciclo registra cuántas alertas reclamó, envió y falló.

### Out of Scope

- Cambios de API: `GET /alerts` ya expone estado, canal y `sent_at` (B.3). `recipient` no se
  expone y este cambio no lo agrega.
- Migraciones: las columnas necesarias existen desde `0001`/`0007`/`0008`.
- Ack de alertas (`/alerts/{id}/ack`): sin issue en la v1.
- WhatsApp y múltiples destinos por canal: fuera del catálogo de la v1.
- Cola durable o broker: ADR-0002 y ADR-0010 los excluyen; el estado vive en `alert`.

## Capabilities

- **Nuevas**: `alert-dispatch` (despacho, retry y transiciones), `notification-channels`
  (routing y credenciales por entorno).
- **Modificadas**: ninguna. `database` y `contract` quedan iguales.

## Approach

Tres piezas con límites claros (ADR-0010):

1. **Configuración** (`comms/config.py`): `pydantic-settings` con alias `INTELLOPS_COMMS_*`,
   validada al construir, con un singleton por proceso.
2. **Despacho** (`comms/dispatcher.py`, `comms/repository.py`, `comms/providers.py`): la decisión
   y el retry son una clase con repositorio y proveedores inyectados; el reclamo usa
   `FOR UPDATE SKIP LOCKED`; Telegram va por `httpx` y Email por `smtplib` en un hilo.
3. **Operación** (`comms/entrypoint.py`, `comms/scheduler.py`, `src/comms/Dockerfile`,
   `docker-compose.yml`): worker sin puertos, ciclo cada `INTELLOPS_COMMS_INTERVAL_SECONDS`,
   apagado ordenado con SIGTERM/SIGINT e imagen que empaqueta `src/` completo.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `src/comms/{config,dispatcher,providers,repository,scheduler,entrypoint}.py` | Nuevo | Worker de despacho |
| `src/comms/Dockerfile` | Reescrito | Espeja el `Dockerfile` del core: `COPY src/`, `PYTHONPATH`, CMD por módulo |
| `docker-compose.yml` | Modificado | Variables del worker con default vacío (`${VAR:-}`) |
| `.env.example` | Modificado | Variables nuevas, sin valores reales |
| `tests/test_comms_{dispatch,contract,container}.py` | Nuevo | Unit, contrato CT-B14-B10 y empaquetado |
| `openspec/changes/ISS-B-10/` | Nuevo | Proposal, design, spec y tasks |
| `CHANGELOG.md`, `docs/business/brief-v1.md` | Docs | Trazabilidad del cambio |

## Vínculo con la investigación

Es la acción observable del sistema: sin despacho no hay alerta percibida, y el cálculo de falsos
positivos (C.4) necesita que la alerta haya llegado a una persona.

## Recursos

Sin dependencias nuevas. Un ciclo cada 30 s con un `SELECT ... SKIP LOCKED` acotado a 20 filas;
el envío es una llamada HTTP o SMTP por alerta, con timeout de 10 s.

## Rollback

Revertir el PR: `intellops-comms` vuelve a ser un placeholder y las alertas quedan en `Pending`
(no hay migración que bajar). Las filas ya enviadas conservan su estado, canal, destinatario y
`sent_at`; no hay pérdida de datos porque este cambio no escribe nada fuera de `alert`.
