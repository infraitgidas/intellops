# Plan de Continuidad — IntellOps

## Propósito

Este documento garantiza la continuidad del proyecto ante rotación de miembros del equipo (fin de prácticas supervisadas, cambios de rol, etc.).

## Principios

1. **Contrato > Código**: Las specs sobreviven a sus autores.
2. **Documentación > Memoria**: Si no está escrito, no existe.
3. **Reproducibilidad > Performance**: Preferir setups reproducibles a optimizaciones frágiles.

## Procedimiento de Handover

Cuando un miembro del equipo se desvincula del proyecto:

### 1. Documentación Obligatoria

El miembro saliente debe completar:

- [ ] ADRs de decisiones tomadas durante su participación.
- [ ] `onboarding/handover-<usuario>.md` con lecciones aprendidas, deudas técnicas, próximos pasos.
- [ ] Actualizar `TEAM_CHARTER.md` si su rol cambia.
- [ ] Actualizar `CHANGELOG.md` con los cambios no liberados.
- [ ] Verificar que sus experimentos ML sean reproducibles (seed fijo, DVC/MLflow).
- [ ] Dejar `docs/research/` con estado actual de su línea de investigación.

### 2. Transferencia de Código

- [ ] Todos los PRs abiertos deben estar documentados con su estado actual.
- [ ] Issues asignadas deben reasignarse o cerrarse con justificación.
- [ ] El código debe pasar tests y linter.
- [ ] Las specs deben estar en `openspec/specs/` y los cambios activos en `openspec/changes/`.

### 3. Conocimiento Tácito

- [ ] Se realiza una sesión de transferencia con el equipo (mínimo 1 hora).
- [ ] Se graba la sesión (si el equipo lo acuerda) y se sube a `docs/handover/`.
- [ ] Se documentan las decisiones no obvias, workarounds y configuración manual.

## Rol de Coordinador

El coordinador (Emanuel Rodriguez) es el punto de continuidad natural. En caso de desvinculación del coordinador:

1. El director (Ing. Leopoldo Nahuel) designa un nuevo coordinador.
2. Se realiza handover extendido de 2 semanas.
3. Se actualiza `TEAM_CHARTER.md` con los nuevos roles.

## Mecanismos de Resiliencia

- **Feature flags**: Las features experimentales se despliegan detrás de flags.
- **Modelos stable vs experimental**: ML tiene modelos estables (producción) y experimentales (investigación).
- **Backup automático**: Rclone sync diario a S3 free-tier.
- **CI/CD autónomo**: El pipeline se autoverifica sin intervención humana.

## Checklist de Continuidad (Mensual)

- [ ] Último backup exitoso verificado.
- [ ] CI/CD verde en `develop`.
- [ ] Todos los ADRs activos tienen estado actualizado.
- [ ] `CHANGELOG.md` refleja cambios recientes.
- [ ] Onboarding documentado y verificable por un nuevo miembro.
- [ ] SBOM actualizado en `governance/sbom.json`.
