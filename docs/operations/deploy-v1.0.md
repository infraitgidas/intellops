# Despliegue y rollback de la v1.0

Runbook para levantar **IntellOps v1.0** en una máquina limpia, verificar que quedó operativo y
volver atrás si algo sale mal. Complementa `docs/release-notes-v1.0.md` (qué entra) y
`docs/operations/smoke-e2e.md` (cómo se prueba el flujo completo).

## 1. Prerrequisitos

| Requisito | Verificación |
|---|---|
| Docker con compose v2 (`docker compose version`) | ≥ 2.20 |
| ≥ 4 GB de RAM libre y ~3 GB de disco para las imágenes | `docker stats` / `df -h` |
| Puerto **8000** libre en el host | `ss -lntp \| grep 8000` |
| Python 3.11+ (sólo para el smoke y la carga, no para el producto) | `python3 --version` |
| Node ≥ 22 **sólo** si se sirve la SPA (no es parte del compose, ADR-0010) | `node --version` |

La stack son cuatro servicios: `intellops-core` (API), `intellops-db` (PostgreSQL 16),
`intellops-ai-engine` (reglas) e `intellops-comms` (despacho). El quinto (`intellops-telegram-stub`)
sólo existe bajo el perfil `smoke`.

## 2. Variables de entorno

`docker compose` lee `.env` de la raíz del repo (está en `.gitignore`; **nunca** se versiona). El
template es `.env.example`.

```bash
cp .env.example .env
$EDITOR .env
```

| Variable | Para qué | En producción |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | credenciales de la DB | cambiar la password |
| `JWT_SECRET` | firma HS256 de los tokens (≥ 32 bytes) | **cambiar**: el default es dev/CI |
| `INTELLOPS_ENV` | etiqueta de entorno | `production` |
| `INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN` / `_CHAT_ID` | canal Telegram | opcional: sin esto la alerta queda `Pending` |
| `INTELLOPS_COMMS_SMTP_*` | canal mail | opcional, mismo criterio |

> **Cuidado con el Admin del seed.** La migración `0002` inserta `admin@intellops.local` con un
> hash **precalculado** para la password de desarrollo (`admin-dev-password`):
> `ADMIN_BOOTSTRAP_PASSWORD` **no** cambia ese hash en una base nueva. En un despliegue real,
> después del primer arranque: rotá la password del Admin por SQL (hash argon2 nuevo) o desactivá
> el usuario semilla (`UPDATE lab_user SET is_active = false WHERE email = 'admin@intellops.local'`)
> y creá los usuarios reales por API.

## 3. Levantar

```bash
git checkout v1.0.0            # el tag local de esta entrega
docker compose up -d --build   # construye core, ai-engine y comms; core corre las migraciones
```

`intellops-core` ejecuta `alembic upgrade head` en su entrypoint; los workers no migran, pero
reintentan su ciclo si la DB todavía no está lista.

## 4. Verificar que quedó operativo (smoke post-deploy)

Checklist mínimo, en orden:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/health   # 200
docker compose ps                                                        # 4 servicios Up
```

Y el flujo completo, con el stub de Telegram incluido (crea una aplicación `smoke-<ts>`, su
telemetría, una regla y una alerta `sent`):

```bash
make smoke        # ~10 s si las imágenes ya están; ver docs/operations/smoke-e2e.md
```

Si el smoke queda en verde, la ingesta, la persistencia, el motor de reglas, el despacho y la
lectura están funcionando de punta a punta. Para probar el envío **real** por Telegram, configurá
`INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN` y `_CHAT_ID` en `.env` (sin
`INTELLOPS_COMMS_TELEGRAM_API_BASE`) y repetí el guion de `docs/operations/demo-mvp1.md`.

Frontend (opcional, build estático servido aparte):

```bash
cd src/frontend && npm ci && npm run build && npm run preview   # http://localhost:4173
```

## 5. Rollback

Dos casos, según qué se quiera deshacer.

### 5.1 Volver a la versión anterior del código (sin tocar los datos)

```bash
docker compose down                # baja los servicios; el volumen de la DB se conserva
git checkout <tag-o-commit-anterior>
docker compose up -d --build
```

Como la v1.0 **no agrega migraciones** sobre `origin/develop` (B.14/B.10/B.9/C.1/C.3 son código,
docs y un cambio aditivo de configuración), volver a develop no requiere `alembic downgrade`.

Si en el futuro un despliegue incluye una migración nueva, el rollback es:

```bash
docker compose exec intellops-core alembic downgrade <revision-anterior>
```

Un downgrade puede negarse a propósito (por ejemplo, `0008` no baja si hay alertas con `rule_id`
cargado): en ese caso se restaura el backup.

### 5.2 Deshacer todo, incluidos los datos

```bash
docker compose --profile smoke down -v   # ⚠️ borra el volumen de PostgreSQL
```

Es destructivo y no tiene vuelta atrás. Preferible: `pg_dump` antes de cada despliegue.

```bash
docker compose exec intellops-db pg_dump -U intellops intellops > backup-v1.0.sql
docker compose exec -T intellops-db psql -U intellops -d intellops < backup-v1.0.sql
```

## 6. Cuando algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `/health` devuelve 503 | la DB no está lista o la migración falló | `docker compose logs intellops-core`; `docker compose ps` |
| `/health` no responde | puerto 8000 ocupado o el contenedor no arrancó | `ss -lntp \| grep 8000`; `docker compose logs intellops-core` |
| El smoke falla en `login` | no hay Admin del seed en la base | base vacía: `alembic upgrade head` corrió? ver logs; o `docker compose --profile smoke down -v` y volver a levantar |
| El smoke falla en `notificación` | comms no llegó al stub (perfil `smoke` sin levantar) o puerto 8099 ocupado | `docker compose --profile smoke ps`; ver `docs/operations/smoke-e2e.md` §5 |
| Los workers no procesan | arrancaron antes de la migración y siguen reintentando | esperar un ciclo (`INTELLOPS_RULES_INTERVAL_SECONDS`, 60 s por defecto) o `docker compose restart intellops-ai-engine intellops-comms` |
| Las alertas quedan en `Pending` | no hay credenciales de canal | es el comportamiento documentado (S9/OAS-B10-2): configurar `.env` |

## 7. Checklist de aceptación del despliegue (C.5)

- [ ] `docker compose up -d --build` en una máquina limpia (sin volúmenes previos) termina sin error.
- [ ] `/health` 200 y los cuatro servicios `Up`.
- [ ] `make smoke` verde: ingesta → lectura → regla → alerta → notificación.
- [ ] La SPA abre, pide la API key y muestra las dos vistas con datos.
- [ ] `pg_dump` de respaldo tomado antes de exponer el entorno.
- [ ] Password del Admin semilla rotada o usuario semilla desactivado.
- [ ] `JWT_SECRET` propio (no el default de dev/CI).
