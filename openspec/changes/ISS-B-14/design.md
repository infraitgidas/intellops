# Design: ISS-B-14 — Motor determinístico de reglas de umbral

Base: `proposal.md`, ADR-0010, ADR-0012, D1, S4.

## 1. Dónde vive el motor

ADR-0010 ya asigna la escritura de `ALERT` Pending a `intellops-ai-engine` ("Worker batch: lee
RUM_METRIC, detecta anomalías y escribe ANOMALY/ALERT en estado Pending") y el CRUD de la API a
`intellops-core`. B.11 (score ML) se difirió a M3, así que en la v1 ese contenedor queda dedicado
al motor determinístico. No hace falta un quinto contenedor ni cambiar el compose: `intellops-ai-engine`
ya recibe `DATABASE_URL`.

Alternativas descartadas:

- **`intellops-comms`**: su límite es "polling de ALERT Pending y despacho". Evaluar reglas ahí
  mezcla dominio con transporte y le da a un contenedor de 150 MB trabajo de agregación SQL.
- **Un contenedor nuevo**: excede el presupuesto de 4 contenedores y el límite de RAM del MVP.

## 2. Configuración: tabla `alert_rule`

Una regla es un umbral sobre una métrica de una aplicación:

| Columna | Tipo | Restricción |
|---|---|---|
| `rule_id` | UUID | PK |
| `application_id` | UUID | FK `application` RESTRICT, NOT NULL |
| `metric_type_id` | SMALLINT | FK `metric_type` RESTRICT, NOT NULL |
| `comparison` | TEXT | CHECK `IN ('gt','lt')`, NOT NULL |
| `threshold` | NUMERIC | NOT NULL; la finitud la valida el servicio |
| `window_minutes` | INTEGER | CHECK `BETWEEN 1 AND 10080` |
| `min_samples` | INTEGER | CHECK `>= 1` |
| `cooldown_minutes` | INTEGER | CHECK `>= 1` |
| `severity` | TEXT | CHECK `IN ('low','medium','high','critical')` |
| `is_active` | BOOLEAN | NOT NULL DEFAULT TRUE |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT `now()` |

Índices: `idx_alert_rule_app_active (application_id, is_active)` para el ciclo, y
`uq_alert_rule_key (application_id, metric_type_id, comparison, threshold)` para que reintentar
la configuración no duplique reglas equivalentes.

`NUMERIC` y no `DOUBLE PRECISION` porque el umbral es un valor de contrato que se muestra en el
mensaje y se compara con el observado; con punto flotante la comparación inclusiva (S4) queda a
merced del redondeo.

La finitud del umbral la valida el servicio (`InvalidAlertRuleError`, 422) y no un CHECK de la
tabla: PostgreSQL no tiene `isfinite` para `NUMERIC`, y un CHECK contra `'NaN'` no cubre
`'Infinity'`. El único escritor es la API de configuración, así que la regla se sostiene en el
borde donde entra el dato.

## 3. Columnas de regla en `alert`

`alert` gana tres columnas nullable, en la migración `0008`:

- `rule_id` FK `alert_rule` RESTRICT — NULL para las alertas de ML (M3).
- `threshold` NUMERIC — el umbral vigente al disparar.
- `observed_value` NUMERIC — el valor que lo disparó.

Se guardan en la alerta y no se derivan de la regla al leer: si mañana se edita el umbral, la
alerta histórica tiene que seguir explicando por qué se disparó. Es el mismo criterio que ADR-0008
usa para anclar la anomalía a la serie.

## 4. Agregación por tipo de métrica

La agregación se deriva del `metric_type`, no se configura: una regla que pidiera "p95 de la
disponibilidad" no tiene sentido.

| Métrica | Agregación | Muestras |
|---|---|---|
| `TTFB`, `FCP`, `XHR_LATENCY` | `percentile_cont(0.95)` de `rum_metric.value` | filas de `rum_metric` en la ventana |
| `JS_EXCEPTION_RATE` | `count(js_exception) / count(user_session)` | sesiones iniciadas en la ventana |
| `AVAILABILITY` | `AVG(rum_metric.value)` (0/1 → uptime) | corridas de la sonda en la ventana |
| `RAGE_CLICK` | `percentile_cont(0.95)` de `rum_metric.value` | filas de `rum_metric` |

`percentile_cont` corre en PostgreSQL: traer las muestras al worker para calcular el percentil
inflaría el consumo del contenedor y duplicaría la lógica de agregación.

`percentile_cont` interpola sobre `float8`, así que el observado se cuantiza a 6 decimales antes
de compararlo: sin eso, un p95 que debería ser exactamente el umbral puede llegar como
`954.9999999999999` y la comparación inclusiva (S4) fallaría por un artefacto binario del cálculo,
no por el dato.

## 5. Comparación inclusiva

`gt` dispara con `observado >= umbral`; `lt` con `observado <= umbral`. La igualdad dispara porque
un umbral es el límite del SLO, no un valor que haya que superar estrictamente: con disponibilidad
`lt 0.99`, un uptime exacto de 0,99 ya incumple. Es el caso borde que pide S4 y queda fijado por
test para los dos sentidos, con `NUMERIC` exacto en el límite.

## 6. Datos insuficientes

Si la ventana tiene menos de `min_samples` muestras, el ciclo no crea alerta y cuenta la regla
como `insufficient`. No es un error: recién arrancado un piloto, la mayoría de las ventanas van a
estar vacías y una alerta por "no hay datos" sería un falso positivo garantizado. Una métrica sin
ninguna fila también cae acá (`samples = 0`).

## 7. Cooldown

Antes de insertar, el motor consulta si existe una alerta de la misma `rule_id` con
`created_at > now() - cooldown_minutes`. Si existe, la omite y la cuenta como `cooled`. El cooldown
se mide contra `alert` y no contra estado en memoria: el worker puede reiniciarse y no debe perder
la noción de la última alerta emitida. Índice de apoyo: `idx_alert_rule_created (rule_id, created_at DESC)`.

## 8. Mensaje

Determinístico y legible por una persona, sin datos de configuración ni secretos:

```
TTFB p95 912,4 ms supera el umbral de 800,0 ms en los últimos 15 min.
```

Un decimal en las magnitudes y en el umbral, el nombre de la métrica tal como está en el catálogo
y la ventana en minutos. El formato se fija por test: es lo que llega por Telegram en M2.

## 9. Contrato de la API de configuración

- `POST /alerts/config` con `require_role("Admin")`: crea la regla; si ya existe una equivalente
  (`application_id`, `metric_type_id`, `comparison`, `threshold`), la actualiza y responde 200 en
  vez de duplicar.
- `GET /alerts/config` con `require_role("Admin", "Researcher")`: lista las reglas de la
  aplicación pedida.
- `application_id` va en el cuerpo (POST) y en el query (GET), y el servicio verifica que exista:
  la autenticación por rol no deriva tenant de una API key, así que el tenant es explícito, como
  en `/applications/{application_id}/api-key`.
- Validaciones semánticas → 422 `invalid_alert_rule` con `ErrorResponse`; `metric_type`
  inexistente → 404 `metric_type_not_found`; aplicación inexistente → 404 `application_not_found`.

El stub actual de `/alerts/config` (`rule: string`, `condition: object`) no tenía esquema ni
implementación: se reemplaza, que es exactamente lo que ADR-0012 §6 dejó anotado como pendiente
de B.14.

## 10. Ciclo

`RuleScheduler` repite `RulesEngine.run_cycle()` cada `INTELLOPS_RULES_INTERVAL_SECONDS`
(default 60). El ciclo:

1. Lee las reglas activas.
2. Por regla: agrega, decide (disparar / cooled / insufficient / ok) y crea la alerta.
3. Loguea el resumen del ciclo (evaluadas, disparadas, cooled, insufficient).

El scheduler se duplica en `src/ml/rules/scheduler.py` en lugar de importar el de `src/probe`:
ADR-0010 prohíbe cross-imports entre módulos de contenedores distintos. Son 25 líneas con su
propio ciclo de tests; el acoplamiento entre contenedores costaría más.

## 11. Alternativas consideradas

- **Evaluar en la ingesta (core)**: la ingesta es el camino caliente (≤ 500 ms, C.3); agregar un
  `percentile_cont` por regla por request degrada exactamente lo que C.3 mide.
- **Reglas en variables de entorno**: no cumplen "por aplicación y por métrica" sin reiniciar el
  stack y sin persistencia.
- **Alertas por "sin datos"**: descartado en §6 por falsos positivos.
