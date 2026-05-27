# Estado del Arte — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Metodología de Revisión

Esta revisión del estado del arte sigue el método **Systematic Literature Review (SLR)** adaptado de Kitchenham & Charters (2007):

- **Período de búsqueda**: 2020-2026
- **Fuentes**: IEEE Xplore, ACM Digital Library, arXiv, Google Scholar, CNCF landscape
- **Términos de búsqueda**: "observability", "AIOps", "anomaly detection infrastructure", "LLM for SRE", "edge ML monitoring", "open-source observability"
- **Criterios de inclusión**: Artículos en inglés/español, conferencias indexadas (IEEE/ACM), proyectos open-source con > 1000 estrellas GitHub
- **Criterios de exclusión**: Soluciones propietarias sin documentación pública, artículos pre-2020 sin actualizaciones

## 2. Evolución de la Observabilidad

### 2.1. Monitoreo Tradicional (pre-2018)

- **Características**: Thresholds estáticos, dashboards pre-definidos, alertas reactivas
- **Herramientas**: Nagios, Zabbix, SolarWinds
- **Limitaciones**: Alto ruido de alertas, sin correlación entre señales, sin contexto de negocio
- **Estado**: Superado — no considerado para IntellOps

### 2.2. Observabilidad Moderna (2018-2024)

- **Características**: Los 3 pilares (logs, métricas, traces), estándares abiertos, vendor-neutral
- **Estándares**: OpenTelemetry (CNCF graduated), OpenMetrics, W3C Trace Context
- **Herramientas**: Prometheus + Grafana, ELK Stack, Jaeger, Tempo
- **Investigación activa**: Correlación automática de señales, reducción de ruido, detección de anomalías
- **Limitaciones**: Análisis post-incidente, correlación manual, AI incipiente

**Referencias clave**:
- Sridharan, C. (2018). *Distributed Systems Observability*. O'Reilly.
- OpenTelemetry Documentation. CNCF. https://opentelemetry.io/docs/
- Prometheus Monitoring Systems. CNCF Graduated Project.

### 2.3. AIOps (2020-presente)

- **Características**: ML para detección de anomalías, clustering de logs, correlación de incidentes
- **Técnicas predominantes**: Isolation Forest, Prophet, Autoencoders, LSTM, Random Forest
- **Herramientas**: Datadog Watchdog, Dynatrace Davis AI, Netdata ML, Elastic ML
- **Investigación activa**:
  - Detección de anomalías en series temporales (Gorilla, Twitter's AnomalyDetection)
  - Root Cause Analysis (RCA) basado en grafos de dependencias
  - Reducción de alertas con ML supervisado
- **Limitaciones**: Falsos positivos, falta de explicabilidad, alto costo computacional

**Referencias clave**:
- Dang, Y. et al. (2019). AIOps: Real-World Challenges and Research Innovations. *IEEE/ACM ICSE-SEIP*.
- Notaro, P. et al. (2021). A Systematic Mapping Study on AIOps. *Journal of Systems and Software*.
- Schmid, P. et al. (2024). Anomaly Detection in Time Series: A Comprehensive Evaluation. *Proc. VLDB Endowment*.

### 2.4. GenIA para SRE / AI-Augmented Observability (2023-presente)

- **Características**: LLMs para RCA semántica, query en lenguaje natural, generación de runbooks
- **Modelos**: GPT-4, Claude, Llama 3, Mistral, Gemma
- **Técnicas**: RAG sobre documentación SRE, fine-tuning para dominios específicos, prompt engineering
- **Herramientas**: GitHub Copilot for Ops, Amazon Q Developer, Datadog Bits AI
- **Investigación activa**:
  - LLMs para análisis causal de incidentes (Microsoft Research)
  - Generación automática de post-mortems (Google SRE)
  - Auto-remediación guiada por LLM
- **Limitaciones**: Alucinaciones, latencia, costo de inferencia, dependencia de vendor

**Referencias clave**:
- Ahmed, T. et al. (2024). Towards Incident Response with Large Language Models. *arXiv:2401.08754*.
- Jiang, Y. et al. (2023). LLM-based Root Cause Analysis for Cloud Incidents. *ACM SIGOPS*.
- Chen, Z. et al. (2024). Auto-Remediation with LLMs: A Case Study. *IEEE/ACM ICSE*.

## 3. Análisis de Plataformas de Observabilidad

### 3.1. Plataformas Comerciales

| Plataforma | Licencia | Footprint | AI/ML | Self-Host | Costo anual (est.) |
|------------|----------|-----------|-------|-----------|-------------------|
| Datadog | Propietaria | Cloud | Watchdog + Bits AI | No | $500K-$2M |
| Dynatrace | Propietaria | Cloud/On-prem | Davis AI (causal) | Limitado | $500K+ |
| New Relic | Propietaria | Cloud | AI Monitoring | No | $50K-$200K |
| Splunk | Propietaria | Cloud/On-prem | Splunk ML | Sí | $1M+ |

### 3.2. Plataformas Open-Source

| Plataforma | Licencia | Footprint (RAM) | AI/ML | Integración OTel |
|------------|----------|-----------------|-------|------------------|
| Grafana + Prometheus + Loki | AGPL-3.0 / Apache-2.0 | ~1-2GB | Plugin-based | ✅ Nativa |
| SigNoz | MIT | ~2-4GB | Básico | ✅ Nativa |
| OpenObserve | AGPL-3.0 | ~1-2GB | O2 SRE Agent | ✅ Nativa |
| Netdata | GPL-3.0 | ~150MB | ML at edge (< 5% CPU) | ❌ Parcial |
| Uptrace | Apache-2.0 | ~1-2GB | AI-driven insights | ✅ Nativa |

### 3.3. Nicho de Mercado Identificado

**Brecha detectada**: Ninguna plataforma combina simultáneamente:

1. **Operación en hardware modesto** (< 2GB RAM, sin GPU)
2. **GenIA local funcional** (sin dependencia de APIs externas)
3. **UX diseñada para contextos académicos** (no enterprise SRE)
4. **Costo operativo $0/mes** (self-hosted + free-tier cloud)
5. **Reproducibilidad científica** (stack containerizado, specs versionadas, datos exportables)

**Posicionamiento de IntellOps**: Cuadrante "Bajo Recurso + Alta AI" — nicho inexplorado por soluciones existentes.

## 4. Estándares y Frameworks de la Industria

| Estándar | Organización | Aplicación en IntellOps |
|----------|-------------|------------------------|
| **OpenTelemetry** | CNCF (graduated) | Ingesta vendor-neutral de métricas, logs, traces |
| **OpenAPI 3.1** | OpenAPI Initiative | Especificación contract-first de APIs REST |
| **AsyncAPI 3.0** | Linux Foundation | Especificación de APIs event-driven |
| **Prometheus Exposition Format** | CNCF | Formato de métricas para scraping |
| **W3C Trace Context** | W3C | Propagación de traces distribuidos |
| **CloudEvents** | CNCF | Estandarización de eventos cloud |
| **SLSA** | OpenSSF | Seguridad de supply chain |
| **OWASP Top 10** | OWASP | Seguridad de aplicaciones web y APIs |
| **FAIR Principles** | FORCE11 | Datos académicos: Findable, Accessible, Interoperable, Reusable |
| **ISO/IEC 25010** | ISO | Atributos de calidad del software |
| **DORA Metrics** | Google | MTTR, Lead Time, Deployment Frequency, Change Failure Rate |

## 5. Investigación Activa Relacionada

Las siguientes líneas de investigación activas (2024-2026) son relevantes para IntellOps:

- **Edge ML para observabilidad**: Netdata demuestra inferencia ML en edge con < 5% CPU y 150MB RAM, 18 modelos unsupervised por métrica (Netdata, 2025)
- **LLM para SRE**: GitHub Copilot for Ops, Amazon Q y proyectos académicos exploran auto-remediación con LLMs
- **eBPF para observabilidad kernel**: Cilium, Pixie (CNCF) y Falco habilitan observabilidad sin instrumentación manual
- **Kubernetes ligero para edge**: K3s y MicroK8s corren en Raspberry Pi 4B con 512MB RAM, validados en investigación de campo

## 6. Referencias

### Académicas

- Kitchenham, B. & Charters, S. (2007). Guidelines for performing Systematic Literature Reviews in Software Engineering. *EBSE Technical Report*.
- Hevner, A. R. et al. (2004). Design Science in Information Systems Research. *MIS Quarterly*.
- Dang, Y. et al. (2019). AIOps: Real-World Challenges and Research Innovations. *IEEE/ACM ICSE-SEIP*.
- Notaro, P. et al. (2021). A Systematic Mapping Study on AIOps. *Journal of Systems and Software*.
- Ahmed, T. et al. (2024). Towards Incident Response with Large Language Models. *arXiv:2401.08754*.
- Schmid, P. et al. (2024). Anomaly Detection in Time Series: A Comprehensive Evaluation. *Proc. VLDB Endowment*.

### Técnicas

- OpenTelemetry Specification v1.33.0. CNCF. https://opentelemetry.io/docs/specs/otel/
- OpenAPI 3.1 Specification. OpenAPI Initiative. https://spec.openapis.org/oas/v3.1.0
- AsyncAPI 3.0 Specification. Linux Foundation. https://www.asyncapi.com/docs/reference/specification/v3.0.0
- SLSA (Supply-chain Levels for Software Artifacts). OpenSSF. https://slsa.dev/spec/v1.0/
- FAIR Principles. GO FAIR. https://www.go-fair.org/fair-principles/

### Mercado

- Gartner (2025). Magic Quadrant for Observability Platforms.
- CNCF (2026). Cloud Native Survey. https://www.cncf.io/reports/
- Netdata (2025). Edge AI Observability Benchmark. *Netdata Blog*.
