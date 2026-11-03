# Preparar tu sitio para la sonda de disponibilidad

Instructivo para el usuario de IntellOps que quiere que su sitio quede **medido
por la sonda HTTP** de la v1. Al terminar, la plataforma registra cada corrida
contra tu sitio: si respondió, con qué código, cuánto tardó, y una serie de
disponibilidad que se puede graficar.

Alcance: sonda HTTP desde **un solo origen**. TLS, DNS y multi-origen son R.4
(2027) y no se configuran acá. La instalación del agente RUM en el navegador es
otra cosa (issue C.2) y no se cubre en este documento.

---

## 0. Qué necesitás antes de empezar

- Una cuenta en IntellOps con rol **Admin** (solo Admin puede crear aplicaciones
  y emitir API keys) o alguien del equipo que lo sea.
- La URL base de la API de IntellOps (`https://api.<tu-dominio>` en el piloto,
  `http://localhost:8000` en desarrollo).
- Acceso al servidor donde va a correr la sonda.

## 1. Preparar el sitio (5 minutos)

La sonda hace un `GET` y mira el código de estado y el tiempo hasta el primer
byte. Para que la medición signifique algo, el sitio tiene que cumplir esto:

| Requisito | Por qué |
|---|---|
| Una URL pública que responda **HTTP 200** sin sesión, cookie ni captcha | La sonda no tiene credenciales: si la página exige login, mide el login |
| Preferentemente un endpoint dedicado de salud, por ejemplo `/health` o `/status` | Mide el sitio y no el peso de una página completa; el TTFB es comparable entre corridas |
| Responder en **menos de `PROBE_TIMEOUT_SECONDS`** (default 5 s) | Lo que tarde más que el timeout se registra como `timeout` = no disponible |
| Sin redirecciones en la URL exacta que vas a configurar | La sonda **no sigue redirecciones**: un 301/302 se registra como disponible pero mide el redirect, no tu página |
| Un solo origen | Comparar desde varias redes es R.4 (2027), fuera de la v1 |

Probá el endpoint desde la máquina que va a correr la sonda:

```bash
curl -s -o /dev/null -w "status=%{http_code} ttfb=%{time_starttransfer}s\n" https://tu-sitio.example.com/health
```

Si eso no devuelve `status=200` con un `ttfb` de menos de 5 segundos, ese no es
el endpoint que querés medir.

## 2. Dar de alta tu sitio en la plataforma

La sonda reporta como **una aplicación** (un tenant). Cada aplicación tiene su
propia API key, y el tenant se deriva **exclusivamente** de esa key: no se
manda `application_id` como autoridad.

### 2.1 Iniciar sesión

```bash
TOKEN=$(curl -s -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"tu@usuario","password":"tu-password"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

### 2.2 Crear la aplicación

```bash
curl -s -X POST "$API/applications" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Sitio piloto","description":"Sitio medido por la sonda B.13"}'
```

Guardá el `app_id` de la respuesta: lo vas a usar en el paso 3 solo si querés
declarar `application_id` en el evento (opcional).

### 2.3 Emitir la API key

```bash
curl -s -X POST "$API/applications/<app_id>/api-key" \
  -H "Authorization: Bearer $TOKEN"
```

La respuesta trae `api_key` (el secreto completo) y `hint` (los últimos 4
caracteres).

> **La key se muestra una sola vez.** No se guarda en la base: si la perdés,
> revocala con `DELETE /applications/<app_id>/api-key` y emití otra. Si intentás
> emitir dos veces sin revocar, la API responde `409`.

Tratala como una contraseña: es lo único que autentica la ingesta.

## 3. Configurar y arrancar la sonda

La sonda se configura por variables de entorno y se ejecuta con:

```bash
python -m probe
```

| Variable | Obligatoria | Default | Qué poner |
|---|---|---|---|
| `PROBE_TARGET_URL` | sí | — | La URL del paso 1, con `http://` o `https://` |
| `PROBE_API_KEY` | sí | — | La `api_key` del paso 2.3 |
| `INGEST_BASE_URL` | no | `http://localhost:8000` | La base de la API de IntellOps |
| `PROBE_INTERVAL_SECONDS` | no | `60` | Cada cuánto medir. Debe ser `> 0` |
| `PROBE_TIMEOUT_SECONDS` | no | `5` | Cuánto esperar antes de declarar `timeout` |
| `PROBE_APPLICATION_ID` | no | — | El `app_id`, si querés declararlo en el evento |

Ejemplo:

```bash
PROBE_TARGET_URL=https://tu-sitio.example.com/health \
PROBE_API_KEY=ilp_xxxxxxxxxxxxxxxx \
INGEST_BASE_URL=https://api.tu-dominio \
PROBE_INTERVAL_SECONDS=60 \
PROBE_TIMEOUT_SECONDS=5 \
python -m probe
```

Si falta una variable obligatoria, o el intervalo es `0`/negativo, o la URL no
tiene esquema, la sonda **falla al arrancar** y te lo dice. No arranca a medias.

Cada corrida deja una línea de log con el resultado:

```
outcome=ok target=https://... http_status=200 latency_ms=143.812 ingest_status=202
```

## 4. Verificar que los datos llegaron

### 4.1 Qué tipos de métrica existen

```bash
curl -s "$API/metrics/list" -H "X-API-Key: $API_KEY"
```

Buscá los `metric_type_id` de `AVAILABILITY` y `TTFB`: los vas a necesitar como
filtro.

### 4.2 Disponibilidad y latencia agregadas

```bash
curl -s "$API/metrics/query?metric_type=<id AVAILABILITY>&bucket_seconds=300" \
  -H "X-API-Key: $API_KEY"
```

- `value` entre **0 y 1**: es la razón de uptime del bucket (`1.0` = todas las
  corridas respondieron, `0.5` = la mitad). Es un promedio de 1 y 0, no un
  porcentaje: multiplicá por 100 para leerlo como tal.
- Repetí con el id de `TTFB` para ver la latencia en milisegundos.

### 4.3 Detalle por corrida

```bash
curl -s "$API/metrics/probes?limit=10" -H "X-API-Key: $API_KEY"
```

Devuelve las últimas corridas, la más nueva primero, con `timestamp`, `target`,
`http_status`, `latency_ms`, `outcome` y `available`. Acá es donde ves el código
de estado de cada ejecución.

## 5. Cómo leer los resultados

| `outcome` | `available` | Significado | Qué hacer |
|---|---|---|---|
| `ok` | `true` | Respondió con status menor a 400 | — |
| `http_error` | `false` | Respondió, pero con 4xx/5xx | Mirá `http_status`; el problema es del sitio |
| `timeout` | `false` | No respondió en `PROBE_TIMEOUT_SECONDS` | Subí el timeout o revisá el sitio; no tiene `latency_ms` a propósito |
| `connection_error` | `false` | No se pudo conectar (DNS, TCP rechazado, TLS) | Verificá host, puerto y certificado |

Un `timeout` y un `connection_error` **no inventan latencia**: no hubo respuesta
que medir. Por eso en esas corridas la métrica es solo `AVAILABILITY = 0`.

## 6. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `401 invalid_api_key` al enviar | Key mal copiada, revocada, o de otra aplicación | Emití una nueva (paso 2.3) |
| `403` al crear aplicación o emitir key | Tu usuario no es Admin | Pedile la key a un Admin |
| `409` al emitir key | La aplicación ya tiene una key activa | Revocá la anterior primero |
| `503 queue_full` | Backpressure de la cola de ingesta | Subí `PROBE_INTERVAL_SECONDS` (sondear menos seguido) o reintentá; el siguiente ciclo va solo |
| Todo `http_error` con 404 | La URL mide una ruta que no existe | Corregí `PROBE_TARGET_URL` |
| Todo `timeout`, pero `curl` responde | La sonda corre en una red distinta o el sitio bloquea esa IP | Verificá desde la máquina de la sonda |

## 7. Lo que este instructivo todavía no es

Hoy la URL del sitio se configura **por despliegue** de la sonda
(`PROBE_TARGET_URL`): si mañana otro usuario quiere medir su propio sitio, hace
falta otra instancia de la sonda o cambiar la variable. Que cada usuario cargue
su URL desde la aplicación —y que la plataforma levante la sonda sola para ese
sitio— requiere guardar el target por aplicación y un alta autoservicio. Eso no
está en B.13: es una decisión de producto pendiente.

Fuera de alcance de la v1 por decisión D2: TLS (vencimiento de certificado),
DNS y sondas multi-origen. Están planificadas para R.4 en 2027.
