# PREPROPOSAL — ISS-S2-02: Aplicaciones y credenciales de ingesta

**Artefacto**: `gentle-ai.sdd-preproposal/v1`
**Cambio**: ISS-S2-02 (GitHub #36). **Rama**: `feat/ISS-S2-02`.
**Revision**: `r3`. **Fecha**: 2026-09-16.
**Modo**: openspec (repo-local) + Engram (recuperación). **Idioma**: español neutro técnico.

---

## Exploración

- **Resultado**: "Ready for Proposal" con confirmación previa de D1–D6 (`exploration.md` §7).
- **Referencia OpenSpec**: `openspec/changes/ISS-S2-02/exploration.md`
- **Referencia Engram**: `sdd/ISS-S2-02/explore` (observation #110)

## Investigación (research)

- **Request**: RQ1–RQ5 — autenticación por API key (header y semántica HTTP; generación/almacenamiento; rotación/revocación; desactivación de app y aislamiento multi-tenant; OpenAPI 3.1 + contract testing).
- **Clases solicitadas**: `open-web` (`websearch`/`webfetch`) y `documentation` (Context7).
- **Admisión**: ACEPTADA (re-entrada r3) — el runtime recargó los permisos; ambas clases ejercitadas con éxito. **Outcome**: `done`.
- **Referencias de evidencia**:
  - OpenSpec: `openspec/changes/ISS-S2-02/research.md` (revision `r3`, outcome `done`, 23 sources, 28 claims).
  - Engram: `sdd/ISS-S2-02/research` (revision `r3`, bytes idénticos al archivo OpenSpec).

## Decisiones de producto (orquestador-owned; no autoritativas como evidencia)

| # | Decisión | Resuelve | Estado |
|---|---|---|---|
| a | Guard `require_api_key` reutilizable + `apiKey` en OpenAPI solo a nivel contrato (handlers de `/telemetry/*` en #37) | D1 | confirmed (respaldado por claims C6/C25) |
| b | Una sola key activa por aplicación (`application.api_token_hash`, SHA-256, prefijo `ilp_`) | D2 | confirmed (respaldado por claims C7–C12) |
| c | `is_active` en schemas; app inactiva invalida su key (403) | D3 | confirmed (respaldado por claims C3/C22) |
| d | Regenerar key sobre app con key activa → 409 con revocación explícita | D4 | confirmed (respaldado por claims C14/C17; tensión con overlap documentada en research §5) |
| e | Aislamiento por binding 1:1 credencial→app (el `app_id` del payload nunca se confía) | D5 | confirmed (respaldado por claims C20/C23) |
| f | Se retira `api_token_hash` de `ApplicationRead` (ADR-16) | D6 | confirmed (respaldado por claims C13/C28) |

Las decisiones a–f están confirmadas por el orquestador y ahora cuentan con respaldo de evidencia externa (`research.md` r3).

## proposal_ready

**`true`** — investigación `done` con evidencia válida (23 sources, 28 claims, todos los campos del contrato completos); decisiones confirmadas; referencias de evidencia válidas en ambos stores con revisión y bytes idénticos (hybrid ready). Habilitado para invocar `sdd-propose`.

## Pendiente orquestador-owned

- Elegir el nombre del header para `require_api_key`: `X-API-Key` (convención dominante, S1/S2) vs `Authorization: ApiKey` (estandarizado, redacción en logs, S5). Fork documentado en `research.md` §5; es decisión de producto, no de evidencia.