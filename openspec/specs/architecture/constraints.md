# Constraints Specification — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Restricciones Técnicas

### 1.1. Restricciones de Recursos

| Restricción | Límite | Fundamento |
|-------------|--------|------------|
| RAM total del sistema | < 2GB (target) / < 3GB (máximo) | Servidores GIDAS existentes (4-8GB, compartidos) |
| CPU | Sin GPU, 2-4 cores | Hardware legacy del laboratorio |
| Disco | < 10GB + datos | SSD disponible limitado |
| Red | Conexión internet intermitente | Laboratorio universitario |
| LLM | < 1GB RAM para inferencia | Deja resto para otros servicios |

### 1.2. Restricciones de Licencia

| Restricción | Detalle |
|-------------|---------|
| Licencia del proyecto | Apache-2.0 |
| Dependencias prohibidas | SSPL, AGPL-3.0 (en producto distribuidble) |
| Dependencias con aviso | AGPL-3.0 (infraestructura sin modificar), GPL-3.0 (evaluar) |
| Dependencias preferidas | MIT, Apache-2.0, BSD, ISC |
| Implicancia | No usar Elasticsearch >7.10, MongoDB >4.4, Grafana modificado |

### 1.3. Restricciones de Plataforma

| Restricción | Detalle |
|-------------|---------|
| Contenerización | Docker Compose obligatorio (sin K8s inicialmente) |
| CI/CD | GitHub Actions (free para repos públicos) |
| Repositorio | GitHub (migrado desde GitLab) |
| OS objetivo | Linux (cualquier distro con Docker) |
| Arquitectura | x86_64 + arm64 (Raspberry Pi) |

## 2. Restricciones de Proceso

### 2.1. Metodológicas

| Restricción | Detalle |
|-------------|---------|
| Desarrollo | Spec-Driven Development (SDD) con OpenSpec |
| Testing | TDD obligatorio (strict mode), coverage ≥ 70% |
| Commits | Conventional Commits |
| Branching | `main` (release) + `develop` (integración) + `feat/*` (cambios) |
| PRs | Mínimo 2 approvals para `develop`, 1 maintainer para `main` |
| Documentación | Todo PR debe actualizar documentación relevante |

### 2.2. De Equipo

| Restricción | Detalle |
|-------------|---------|
| Dedicación | 10 hs/semana por estudiante (PS), variable coordinador |
| Período | Mayo-Diciembre 2026 |
| Modalidad | Híbrida (presencial + remota) |
| Skills iniciales | Python básico, JavaScript básico, Git, Docker aprendiendo |
| Rotación | Fin de PS en Octubre 2026 (Cavallero, Montanari) |

### 2.3. De Investigación

| Restricción | Detalle |
|-------------|---------|
| Publicaciones | Mínimo 1 paper por línea de investigación |
| Reproducibilidad | Experimentos versionados con DVC + MLflow |
| Datos | FAIR principles, datasets con DOI (Zenodo/OSF) |
| Plagio | Toda contribución original, citas obligatorias |
| Ética | Datos anonimizados, consentimiento informado para datos reales |

## 3. Restricciones de Negocio

| Restricción | Detalle |
|-------------|---------|
| Presupuesto | $0/mes operativo, ~$640 total proyecto |
| Monetización | No en fase PI+D+i (posible SaaS freemium post-proyecto) |
| Transferencia | 2+ laboratorios piloto al finalizar |
| Extensión | Demo funcional para visitas al laboratorio |
| Comunidad | Código abierto desde el inicio |

## 4. Principios de Diseño

Estos principios guían todas las decisiones arquitectónicas:

### 4.1. Principios Técnicos

1. **Principio de Menor Sorpresa**: Las APIs y componentes se comportan de la manera más esperada posible. Una consulta GET no modifica estado. Un POST devuelve 201/202.
2. **Principio de Falla Rápida (Fail Fast)**: Si algo está mal configurado, el sistema falla en startup con un mensaje claro, no en producción con un error críptico.
3. **Principio de Default Seguro (Secure by Default)**: Por defecto, todo acceso es denegado. La configuración define explícitamente qué está permitido.
4. **Principio de Migración Transparente**: Las decisiones de almacenamiento (SQLite), LLM (1B → 8B), y despliegue (Compose → K8s) tienen capas de abstracción que permiten migrar sin reescribir.
5. **Principio de Costo Marginal Cero**: Cada feature nueva debe poder ejecutarse sin aumentar el costo operativo. Si requiere cloud pago, es extensión futura.

### 4.2. Principios de Proceso

1. **Contrato > Código**: Si no está en la spec, no se implementa. Si se implementa sin spec, se revierte.
2. **Documentación > Memoria**: Si no está escrito, no existe. Toda decisión arquitectónica tiene un ADR.
3. **Tests > Features**: Una feature sin tests no está completa. Coverage < 70% es deuda técnica.
4. **Reproducibilidad > Performance**: Preferir resultados reproducibles (seed fijo, pipeline versionada) a optimizaciones que no se pueden validar.
5. **Comunicación Asíncrona > Reuniones**: Las decisiones se documentan en issues y PRs, no en reuniones sin minuta.

## 5. Supuestos Arquitectónicos

| Supuesto | Riesgo si es falso | Mitigación |
|----------|-------------------|------------|
| El volumen de métricas no excede 1K/seg | SQLite puede saturarse | Diseño migrable a TimescaleDB |
| Los usuarios tienen conexión a internet intermitente | Dashboard offline puede perder datos | Polling con backoff, cola local |
| El equipo aprende Python/FastAPI rápido | Curva de aprendizaje retrasa entregas | Onboarding estructurado, pair programming |
| Los modelos ML funcionan con datos sintéticos | Falla en datos reales (distribution shift) | Validación cruzada, Evidently drift monitor |
| El LLM 1B es suficiente para RCA útil | RCA de baja calidad insatisfactorio | Fallback a templates pre-definidos |
