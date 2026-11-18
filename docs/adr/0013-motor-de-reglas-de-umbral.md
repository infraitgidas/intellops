# ADR 0013: Motor determinístico de reglas de umbral en el `ai-engine`

- **Estado**: Aceptado
- **Fecha**: 2026-11-18
- **Decisión relacionada**: Issue #74 (B.14), D1, ADR-0010 (4 contenedores), ADR-0012 (alerta
  independiente), `openspec/changes/ISS-B-14/`

## Contexto

D1 difirió la detección ML a M3, pero M2 exige una alerta real por Telegram. La v1 necesita un
motor determinístico que evalúe umbrales sobre las métricas RUM y la disponibilidad de la sonda, y
cree `ALERT` en estado Pending. B.14 sustituye en la v1 al motor basado en score ML (B.11).

Al diseñarlo aparecen tres preguntas que el código no puede responder solo:

1. **Dónde corre.** ADR-0010 fija cuatro contenedores y asigna la escritura de `ALERT` Pending a
   `intellops-ai-engine`, pero ese contenedor se describió para el detector de anomalías. Sin una
   decisión explícita, el motor de umbrales podría terminar en `intellops-core` (camino caliente de
   ingesta) o en `intellops-comms` (transporte).
2. **Dónde vive la configuración.** "Umbrales configurables por métrica y por aplicación" no tiene
   lugar en variables de entorno: no son por aplicación ni sobreviven a un reinicio.
3. **Qué se guarda en la alerta.** ADR-0012 §3 dejó anotado que el umbral, el valor observado y el
   id de la regla los agrega B.14, sin fijar si viven en la regla o en la alerta.

## Decisión

1. **El motor corre en `intellops-ai-engine`**, como worker batch sin puertos, con su propio ciclo
   periódico. Es el contenedor que ADR-0010 ya define como escritor de `ALERT` Pending y el que
   queda con presupuesto libre al diferirse B.11 a M3. No se agrega un quinto contenedor ni se
   toca el compose: el servicio ya recibe `DATABASE_URL`.
2. **La configuración vive en una tabla nueva, `alert_rule`**, con umbral, comparación, ventana,
   muestras mínimas, cooldown y severidad por (`application_id`, `metric_type_id`). Se expone por
   `POST`/`GET /alerts/config` en `intellops-core` con auth por rol (JWT), porque es CRUD de
   administración de la aplicación, no lectura de tenant por API key.
3. **El umbral y el valor observado se copian en cada alerta** (`alert.threshold`,
   `alert.observed_value`) además de la referencia `alert.rule_id`. Una alerta histórica tiene que
   explicar por qué se disparó aunque el umbral se haya editado después, con el mismo criterio con
   el que ADR-0008 ancla la anomalía a la serie.
4. **La agregación se deriva del tipo de métrica**, no se configura: latencia por
   `percentile_cont(0.95)`, disponibilidad por `AVG` del 0/1 de la sonda, tasa de errores por
   `count(js_exception) / count(user_session)`. Se calcula en PostgreSQL para no traer muestras
   crudas al worker.
5. **La comparación es inclusiva**: `gt` dispara con `observado >= umbral` y `lt` con
   `observado <= umbral`. Un umbral es el límite del SLO, no un valor a superar estrictamente.
6. **Datos insuficientes no generan alerta.** Con menos de `min_samples` muestras la regla se
   omite y el ciclo la cuenta como `insufficient`: una alerta por "no hay datos" es un falso
   positivo garantizado en un piloto recién arrancado.

## Consecuencias

Positivas:

- La ingesta no paga la agregación: el camino caliente conserva el presupuesto de C.3 (≤ 500 ms).
- El motor es testeable sin base: la decisión (comparar, cooldown, insuficiencia) es una función
  pura y la agregación se prueba contra Postgres real.
- La alerta es autosuficiente para el dispatcher: B.10 no necesita leer `alert_rule` para decidir
  canal ni texto.
- Con B.11 en M3, el motor de umbrales y el detector de anomalías comparten contenedor sin competir
  por el mismo ciclo.

Negativas / Trade-offs:

- `intellops-ai-engine` gana un tercer rol (umbrales, anomalías y LLM) y su límite de 1000 MB pasa a
  cubrir también el ciclo de reglas. El costo es acotado: una consulta de agregación por regla activa.
- El scheduler de `src/probe` no se reutiliza (ADR-0010 prohíbe cross-imports entre contenedores):
  hay 25 líneas duplicadas, con sus propios tests.
- `alert.threshold` y `alert.observed_value` son `NUMERIC` y no punto flotante: la comparación
  inclusiva no queda a merced del redondeo, a costa de una conversión en la capa de presentación.

## Riesgos

- **Crecimiento de `alert`** con cooldowns cortos: el índice `idx_alert_rule_created` y un cooldown
  mínimo de 1 minuto lo acotan; C.4 mide los falsos positivos con datos reales.
- **Reglas sin muestras** en el arranque del piloto: se cubre con `min_samples` y el contador
  `insufficient` del ciclo, visible en el log.
