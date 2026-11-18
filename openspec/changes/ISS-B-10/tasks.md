# Tasks: ISS-B-10 — Despacho de alertas por Telegram y Email

## Review Workload Forecast

Changed lines (estimado): ≈ 1400, de las cuales ≈ 720 son tests (`test_comms_dispatch.py`,
`test_comms_contract.py`, `test_comms_container.py`), ≈ 560 código de producción con docstrings
(settings, dispatcher, proveedores, repositorio, scheduler, entrypoint y Dockerfile) y el resto
compose, `.env.example`, `CHANGELOG.md`, `brief-v1.md` y los documentos del cambio. Delivery
strategy: work-unit commits por preocupación (configuración → despacho → operación/empaquetado →
contrato), cada uno con sus tests.

Decision needed before apply: No (ADR-0010 ya asigna el despacho a `intellops-comms` y D1–D9
resuelven routing, destinos, retry y transiciones).
Chained PRs recommended: No.
400-line budget risk: High (el despacho y sus tests de retry son el bloque más grande; conviene
revisar por los cuatro slices naturales en lugar de línea por línea).

Dependencias: ISS-B-03 (tabla `alert` y `GET /alerts`), ISS-B-14 (alertas `Pending` del motor).
Lo consumen C.1 (E2E), C.3 (piloto) y C.5 (release).

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (OAS-B10-1..5, CD-1..6, CT-B14-B10), `design.md` y este
      `tasks.md`.

## Fase 1 — Configuración y contratos

- [x] 1.1 `config.py`: `CommsSettings` con alias `INTELLOPS_COMMS_*`, routing validado por
      severidad, credenciales opcionales y `RetryPolicy` derivada (OAS-B10-1..3).
- [x] 1.2 `dispatcher.py`: `PendingAlert`, `CycleSummary`, contrato `AlertProvider` /
      `CommsRepository` y clasificación `Transient`/`PermanentDeliveryError`.
- [x] 1.3 Tests unitarios de settings: defaults del routing, override por env, canal inválido,
      credenciales ausentes, defaults del retry y normalización de `DATABASE_URL`.

## Fase 2 — Despacho

- [x] 2.1 `Dispatcher.run_cycle`: severidades ruteables, reclamo por lote, envío y transición
      (CD-1, CD-2, CD-5).
- [x] 2.2 `Dispatcher._deliver`: backoff exponencial, presupuesto acotado y fallos permanentes
      sin reintento (CD-3, CD-4).
- [x] 2.3 Log de una sola vez por canal sin credenciales, con registro compartido entre ciclos
      (OAS-B10-2, design §6).
- [x] 2.4 `repository.py`: `claim_pending` con `FOR UPDATE SKIP LOCKED` y filtro por severidad,
      `mark_sent` y `mark_failed` (CD-1, CD-5).
- [x] 2.5 `providers.py`: Telegram con `httpx` y Email con `smtplib`/`EmailMessage` en un hilo,
      con clasificación de fallos y sin filtrar secretos (CD-4, OAS-B10-4, D9).
- [x] 2.6 Tests unitarios del despacho con proveedores falsos: cuatro severidades, retry y
      éxito, 4xx permanente, agotamiento, presupuesto, `sent_at`, `recipient`/`channel_id`,
      secuencia de backoff, lote acotado y canal sin credenciales.
- [x] 2.7 Tests de los proveedores reales con transporte falso (`httpx.MockTransport` y
      `smtplib.SMTP` doble): 200/400/403/429/5xx, 5xx SMTP, 4xx SMTP y no fuga de secretos.

## Fase 3 — Ciclo, operación y empaquetado

- [x] 3.1 `scheduler.py` y `entrypoint.py`: ciclo periódico, construcción de proveedores,
      reenganche de canales configurados, SIGTERM/SIGINT y ciclo que no mata el proceso.
- [x] 3.2 `src/comms/Dockerfile` reescrito: `COPY src/ src/`, `ENV PYTHONPATH=/app/src`,
      dependencias del core y `CMD ["python", "-m", "comms.entrypoint"]`.
- [x] 3.3 `docker-compose.yml`: variables del worker con default vacío; `.env.example` con las
      variables y sin valores reales.
- [x] 3.4 `tests/test_comms_container.py`: empaquetado, arranque, compose sin secretos y
      ausencia de puertos.
- [x] 3.5 Prueba de la imagen: build y ejecución contra la base de test en la red
      `intellops-test_default`, con ciclos en el log y apagado limpio por SIGTERM.

## Fase 4 — Contrato y cierre

- [x] 4.1 `tests/test_comms_contract.py` (CT-B14-B10): alerta del motor → `Pending` → `Sent` con
      transporte falso, visible por `GET /alerts`; fallo permanente → `Failed`; `SKIP LOCKED`
      entre dos sesiones reales.
- [x] 4.2 `CHANGELOG.md` y estado de B.10 en `docs/business/brief-v1.md`.
- [x] 4.3 Suite completa (`make test`) y lint (`make lint`).
