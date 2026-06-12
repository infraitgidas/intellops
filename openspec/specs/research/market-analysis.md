# Market Analysis — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Definición del Mercado

### 1.1. Mercado Total Direccionable (TAM)

El mercado global de observabilidad se estima en **$5.2B USD en 2025** con una CAGR del 18.2% (Gartner, 2025). Segmentos relevantes:

| Segmento | TAM (2025) | CAGR | Driver |
|----------|------------|------|--------|
| Observabilidad IT | $2.8B | 20% | Adopción de cloud-native, OpenTelemetry |
| AIOps | $1.5B | 25% | Adopción de ML para operaciones IT |
| Monitoreo de infraestructura | $900M | 12% | Modernización de legacy |

### 1.2. Mercado Disponible (SAM)

IntellOps apunta a tres sub-segmentos:

1. **Academia latinoamericana**: ~500 laboratorios de ingeniería informática en universidades públicas de LATAM.
2. **PYMEs tecnológicas**: ~50K pequeñas empresas de tecnología en LATAM con necesidad de observabilidad y presupuesto limitado.
3. **Administración pública**: ~1000 organismos públicos con infraestructura legacy y restricciones de licencias.

**SAM estimado**: $50M USD (1% del TAM, enfocado en LATAM + recursos escasos).

### 1.3. Mercado Obtenible (SOM)

Objetivo a 2 años vista:
- **10 laboratorios universitarios** replicando IntellOps (extensión)
- **50 desarrolladores** activos en la comunidad open-source
- **5 artículos académicos** publicados en venues IEEE/ACM/Latin-American

## 2. Análisis Competitivo

### 2.1. Mapa de Posicionamiento

```
Alta IA ↑
        |   Datadog  Dynatrace
        |     ●          ●
        |  New Relic
        |     ●
        |              SigNoz
        |                ●
        |         ● OpenObserve
        |  IntellOps ●
        |                Grafana Stack
        |  Netdata ●      ●
Baja IA ↓
        Bajo Recurso ──────────── Alto Recurso
```

IntellOps se posiciona en el cuadrante **Bajo Recurso + Alta IA**, un nicho sin competidores directos.

### 2.2. Análisis FODA

| Factor | Detalle |
|--------|---------|
| **Fortalezas** | Costo $0, stack 100% open-source, GenIA local, enfoque en recursos escasos, respaldo académico GIDAS, metodología SDD |
| **Debilidades** | Equipo pequeño (3 estudiantes PS + 1 coordinador), sin financiamiento, sin experiencia previa en producción, MVP en etapas tempranas |
| **Oportunidades** | Creciente demanda de observabilidad accesible, auge de LLMs open-source, interés de universidades en herramientas propias, programas de extensión UTN |
| **Amenazas** | Soluciones gratuitas de hyperscalers (AWS CloudWatch free tier), Netdata con ML incorporado, proyectos open-source con mayor comunidad |

### 2.3. Ventajas Competitivas Clave

1. **GenIA local sin costo**: Mientras que Datadog Bits AI cuesta $5/host/mes adicional, IntellOps incluye LLM local sin costo marginal.
2. **Reproducibilidad científica incorporada**: No es un add-on, es parte del diseño (DVC + MLflow + specs versionadas).
3. **Stack unificado**: Prometheus + Loki + Grafana + ML engine + LLM en un solo Docker Compose, < 2GB RAM.
4. **Licencia Apache-2.0**: Permite uso comercial sin restricciones, a diferencia de AGPL/SSPL de competidores.

## 3. Estrategia de Mercado

### 3.1. Canales de Adopción

| Canal | Estrategia | Timeline |
|-------|-----------|----------|
| **Académico** | Publicaciones en conferencias (JAIIO, CACIC, CLEI, ISSRE, SREcon, FSE, ASE) y revistas (JSS, SPE, EMSE, IST, IEEE LATAM, IEEE Software); workshops en universidades | Meses 1-12 |
| **Open-source** | GitHub público, documentación bilingüe, templates de contribución | Meses 1-24 |
| **Extension universitaria** | Demos en laboratorios UTN, convenios con otras facultades | Meses 6-18 |
| **Comercial (futuro)** | SaaS ligero freemium, consultoría de implementación | Meses 18-24+ |

### 3.2. Métricas de Adopción

| Métrica | Target 6 meses | Target 12 meses | Target 24 meses |
|---------|----------------|-----------------|-----------------|
| GitHub stars | 50 | 200 | 500+ |
| Descargas Docker | 100 | 500 | 2000+ |
| Laboratorios piloto | 1 (GIDAS) | 3 | 10+ |
| Papers publicados | 0 | 2 | 5+ |
| Contribuidores externos | 0 | 3 | 15+ |
| Issues/Pull Requests | — | 20+ | 100+ |

## 4. Análisis de Costos

| Concepto | Costo mensual | Anual | Notas |
|----------|--------------|-------|-------|
| Infraestructura GIDAS | $0 | $0 | Existente |
| Cloud free-tier | $0 | $0 | AWS/GCP/Azure free tiers |
| Herramientas open-source | $0 | $0 | GitHub, Docker, etc. |
| Publicaciones (fees) | — | $500 | IEEE/ACM conference fees |
| Hardware adicional | — | $140 | Raspberry Pi 4 (x2) |
| **Total** | **$0/mes** | **~$640/año** | |

## 5. Referencias

- Gartner (2025). Magic Quadrant for Observability Platforms.
- CNCF (2026). Annual Survey 2025. https://www.cncf.io/reports/
- Statista (2025). Observability Platform Market Size.
- Grand View Research (2025). AIOps Market Analysis.
