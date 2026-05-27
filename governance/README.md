# Governance — IntellOps

Este directorio contiene artefactos de gobierno, compliance y continuidad del proyecto.

## Estructura

| Archivo | Propósito | Formato | Actualización |
|---------|-----------|---------|---------------|
| `sbom.json` | Software Bill of Materials (SBOM) en formato CycloneDX | JSON | Automática (CI) |
| `sbom.md` | Resumen legible de licencias y dependencias | Markdown | Por release |
| `compliance.md` | Políticas de licencia, seguridad y estándares | Markdown | Trimestral |
| `continuity.md` | Plan de continuidad para rotación de equipo | Markdown | Por cambio de miembros |

## SBOM

El SBOM se genera automáticamente en cada build de CI usando `anchore/sbom-action`.

### Licencias Compatibles

El proyecto usa licencia **Apache-2.0**. Las dependencias deben tener licencias compatibles:

- ✅ MIT, Apache-2.0, BSD, ISC
- ✅ MPL-2.0 (con aviso)
- ❌ SSPL (MongoDB, Elasticsearch >7.10)
- ⚠️ AGPL-3.0 (Grafana >8.x, Loki) — permitido para infraestructura sin modificar, ver `compliance.md`
- ⚠️ GPL-2.0/3.0 (evaluar caso por caso)

### Dependencias Permitidas por Capa

| Capa | Licencia | Alternativa si es restrictiva |
|------|----------|-------------------------------|
| FastAPI | MIT | — |
| SQLite | Public Domain | — |
| scikit-learn | BSD-3 | — |
| Llama.cpp | MIT | — |
| Llama 3.2 | Llama 3.2 Community | Gemma 2 (Apache-2.0) |
| sentence-transformers | Apache-2.0 | — |
| ChromaDB | Apache-2.0 | — |
| React | MIT | — |
| D3.js | ISC | — |
| Netdata | GPL-3.0 | Evaluar |
| Grafana | AGPL-3.0 | Usar as-is sin modificar |
| Loki | AGPL-3.0 | Usar as-is sin modificar |
| Promtail | AGPL-3.0 | Usar as-is sin modificar |

## Compliance Checklist (Pre-Release)

- [ ] SBOM generado y verificado
- [ ] Sin dependencias SSPL o AGPL
- [ ] Todas las dependencias tienen licencia conocida
- [ ] `CITATION.cff` actualizado
- [ ] Changelog actualizado
- [ ] ADRs revisados
- [ ] Experimentos ML versionados
