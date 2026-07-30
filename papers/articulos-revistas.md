# Artículos para Revistas con Referato — IntellOps

> **Propósito**: Desarrollar ideas concretas para publicar artículos de divulgación científica en revistas con referato que den prestigio y visibilidad al proyecto IntellOps.
> **Grupo**: InfraIT · GIDAS · UTN FRLP
> **Fecha**: 2026-07-30

---

## Tabla de Contenidos

1. [Estrategia General](#1-estrategia-general)
2. [Artículo A: Survey — Observabilidad UX-Céntrica en Recursos Escasos](#2-artículo-a-survey)
3. [Artículo B: Tool Paper — Agente RUM Liviano con OTel](#3-artículo-b-tool-paper)
4. [Artículo C: Estudio Empírico — Predicción de Reclamos con ML](#4-artículo-c-estudio-empírico)
5. [Artículo D: Experiencia — Quality Gates OTel en I+D+i](#5-artículo-d-experiencia)
6. [Artículo E: Caso de Estudio — Seguridad Zero-Cost en Laboratorios](#6-artículo-e-caso-de-estudio)
7. [Artículos Cortos para Revistas Regionales](#7-artículos-cortos-regionales)
8. [Alternativas de Títulos y Enfoques para el Primer Artículo](#8-alternativas-de-títulos-y-enfoques-para-el-primer-artículo-de-divulgación)
   - 8.1. [Ingenio Tecnológico](#81-para-ingenio-tecnológico-utn-frlp)
   - 8.2. [RASI](#82-para-rasi--revista-argentina-de-sistemas-de-información)
   - 8.7. [Captación de interesados](#87-para-captación-de-interesados-y-búsqueda-de-apoyo-institucional) ⭐
9. [Roadmap de Publicaciones 2026-2028](#9-roadmap-de-publicaciones-2026-2028)
10. [Siguientes Pasos Concretos](#10-siguientes-pasos-concretos)

---

## 1. Estrategia General

### 1.1. Principios

| Principio | Explicación |
|-----------|-------------|
| **Publicar temprano, publicar seguido** | No esperar a tener el producto terminado. Resultados parciales válidos = papers |
| **Revista primero, conferencia después** | Las revistas tienen mayor factor de impacto y prestigio académico |
| **Un paper por hipótesis** | Cada hipótesis (H1-H7) puede generar al menos un artículo |
| **Colaboración > autor único** | Artículos con 2-3 autores del equipo tienen más chances de aceptación |
| **Datos abiertos + reproducible** | Incluir DOI de datasets, código en GitHub, badges de reproducibilidad |

### 1.2. Taxonomía de Artículos

| Tipo | Extensión | Revistas target | Esfuerzo | Impacto |
|------|-----------|----------------|----------|---------|
| **Survey / SLR** | 15-30 págs | ACM CSUR, JSS, IST | Alto (3-6 meses) | Muy alto |
| **Tool paper** | 8-12 págs | SPE, IEEE Software, JWE | Medio (2-3 meses) | Alto |
| **Estudio empírico** | 15-20 págs | EMSE, JSS, IST | Alto (3-6 meses) | Alto |
| **Experience report** | 8-12 págs | IEEE Software, SPE | Medio (2-3 meses) | Medio-Alto |
| **Caso de estudio** | 10-15 págs | JSS, IST, IEEE Access | Medio (2-4 meses) | Medio |

### 1.3. Priorización por Contributor

| Contributor | Artículo primario | Revista target | Plazo |
|-------------|-------------------|---------------|-------|
| **Emanuel** (coordinador) | A — Survey + B — Tool paper | ACM CSUR / SPE | 6-8 meses |
| **Federico** | B — Tool paper + E — Caso seguridad | SPE / IEEE Latin America | 4-6 meses |
| **Romeo** | C — Estudio empírico ML | EMSE / JSS / IEEE Access | 4-6 meses |
| **Santiago** | D — Experience report QA | IST / JSS / JAIIO | 4-6 meses |

---

## 2. Artículo A: Survey — Observabilidad UX-Céntrica en Recursos Escasos

### 2.1. Ficha Técnica

| Campo | Detalle |
|-------|---------|
| **Título tentativo** | *"UX-Centric Observability for Resource-Constrained Environments: A Systematic Literature Review"* |
| **Tipo** | Systematic Literature Review (SLR) / Survey |
| **Revistas target** | **ACM Computing Surveys** (IF ~23.0) > **JSS** (IF ~3.0) > **IST** (IF ~3.5) |
| **Autores** | Rodriguez, Monfroglio, Cavallero, Montanari, Nahuel |
| **Línea** | L5 — Observabilidad UX-Céntrica |
| **Esfuerzo** | Alto (3-6 meses) |

### 2.2. Problema de Investigación

**RQ1**: ¿Cuál es el estado del arte de la observabilidad centrada en el usuario (frontend/RUM) en entornos con recursos computacionales limitados (< 2GB RAM, CPU-only)?

**RQ2**: ¿Qué técnicas de ML liviano se han aplicado a la detección de anomalías en experiencia de usuario real?

**RQ3**: ¿Qué brechas existen entre las soluciones comerciales (Datadog, Dynatrace) y las alternativas open-source para entornos académicos?

### 2.3. Material Existente

Este artículo **ya tiene el 60% del contenido listo** en los documentos de investigación:

| Documento | Líneas | Aporta al artículo |
|-----------|--------|-------------------|
| `frontend-observability.md` | 929 | Secciones 3 (pilares frontend), 4 (métricas UX), 5 (Core Web Vitals), 7 (RUM vs Synthetic) |
| `rum-agent-deep-dive.md` | 1.207 | Secciones 3 (implementación de métricas), 4 (Browser APIs), 5 (OTel Browser SDK) |
| `observability-tools-analysis.md` | 845 | Secciones 2 (comparativa de 12 herramientas), 3 (tendencias), 4 (gaps de investigación) |
| `publication-venues.md` | 189 | Sección de referencias bibliográficas indexadas |

### 2.4. Estructura Propuesta

```
1. Introducción (2 págs)
   - Contexto: observabilidad en 2026, crecimiento del mercado
   - Problema: soluciones existentes no alcanzan a entornos con recursos escasos
   - Preguntas de investigación (RQ1-RQ3)

2. Metodología de Revisión (3 págs)
   - Protocolo SLR adaptado de Kitchenham & Charters
   - Fuentes: IEEE Xplore, ACM DL, Scopus, arXiv
   - Términos de búsqueda, criterios de inclusión/exclusión
   - Extracción de datos y síntesis

3. Marco Conceptual (4 págs)
   - Observabilidad clásica vs frontend
   - Core Web Vitals y RUM
   - RED Method para frontend
   - User Health Score

4. Estado del Arte — Herramientas (5 págs)
   - Soluciones comerciales (Datadog, Dynatrace, New Relic)
   - Plataformas open-source (Grafana LGTM, SigNoz, OpenObserve)
   - Agentes RUM open-source (OTel Browser, Faro, OpenReplay)
   - Matriz comparativa por recursos, features, licencias

5. Estado del Arte — ML para Observabilidad (4 págs)
   - Detección de anomalías en series temporales
   - LLMs para RCA (Root Cause Analysis)
   - ML en edge/recursos escasos

6. Brechas y Oportunidades (3 págs)
   - Mapa de posicionamiento: cuadrante "Bajo Recurso + Alta IA"
   - 5 campos abiertos de investigación
   - El nicho de IntellOps

7. Conclusión y Trabajo Futuro (2 págs)

8. Referencias (30-50 refs, ya tenemos 30+)
```

### 2.5. Ventana de Publicación

| Hito | Fecha |
|------|-------|
| Inicio de escritura | Agosto 2026 |
| Borrador completo | Octubre 2026 |
| Submission a ACM CSUR | Noviembre 2026 |
| *Plan B: Submission a JSS* | *Enero 2027* |

### 2.6. Por qué ACM Computing Surveys

- **Factor de impacto**: ~23.0 (el más alto en ingeniería de software)
- **Visibilidad**: Es la revista más leída en CS
- **Formato**: Acepta surveys extensos (hasta 30 págs)
- **Nuestro diferencial**: El nicho "Bajo Recurso + Alta IA" NO está cubierto en surveys existentes
- **Riesgo**: Revisión lenta (12-18 meses). Alternativa: JSS (3-6 meses, IF ~3.0)

> **📌 Decisión clave**: Recomiendo apuntar a **JSS primero** (revisión más rápida, IF respetable) y si es aceptado, expandir para CSUR después. O enviar a CSUR directamente y mientras tanto publicar resultados parciales en conferencias.

---

## 3. Artículo B: Tool Paper — Agente RUM Liviano con OTel

### 3.1. Ficha Técnica

| Campo | Detalle |
|-------|---------|
| **Título tentativo** | *"A Lightweight OpenTelemetry RUM Agent for Real User Monitoring in Resource-Constrained Environments"* |
| **Tipo** | Tool paper / Experience report |
| **Revistas target** | **SPE — Software: Practice and Experience** (IF ~2.5) > **IEEE Software** (IF ~4.0) > **JWE** (IF ~1.0) |
| **Autores** | Cavallero, Rodriguez, Nahuel |
| **Línea** | L5 — H5 (User Telemetry & Tracing) |

### 3.2. Contribución

- Diseño e implementación de un agente RUM basado en OpenTelemetry JS SDK con bundle < 30KB
- Captura de Core Web Vitals (LCP, INP, CLS) + trazas distribuidas + errores JS + Rage Clicks
- Estrategias de optimización: tree-shaking, lazy loading, custom exporter
- Evaluación de overhead: impacto en LCP, bundle size, throughput

### 3.3. Cuándo Escribirlo

**Requiere implementación primero.** Estimar:

| Fase | Qué | Cuándo |
|------|-----|--------|
| Implementación del agente RUM | Código funcionando con OTel JS SDK | Sprint 3-4 (Sep 2026) |
| Mediciones de overhead | Lighthouse con/sin agente, bundle size | Sprint 5-6 (Oct 2026) |
| Borrador del paper | Resultados + discusión | Oct-Nov 2026 |
| Submission | A SPE (revisión rápida: 3-6 meses) | Nov 2026 |

### 3.4. Por qué SPE

- **Velocidad de revisión**: 3-6 meses (la más rápida entre las indexadas SCI-E)
- **Alineación**: Publica experiencia práctica con herramientas y frameworks
- **Extensión**: Papers de 8-12 páginas, manejable para un equipo de estudiantes
- **IF**: 2.5, respetable para una primera publicación en revista

---

## 4. Artículo C: Estudio Empírico — Predicción de Reclamos con ML

### 4.1. Ficha Técnica

| Campo | Detalle |
|-------|---------|
| **Título tentativo** | *"Predicting User Complaints from Observability Signals: An Empirical Study with Lightweight ML in Resource-Constrained Environments"* |
| **Tipo** | Estudio empírico |
| **Revistas target** | **EMSE — Empirical Software Engineering** (IF ~4.0) > **JSS** (IF ~3.0) > **IEEE Access** (IF ~3.5) |
| **Autores** | Monfroglio, Rodriguez, Nahuel |
| **Línea** | L1 + L6 — H1 + H6 (ML liviano + Agentes IA) |

### 4.2. Contribución

- **Dataset**: Generación de dataset sintético de trazas OTel con reclamos etiquetados
- **Modelos**: Comparación de Isolation Forest, Random Forest, Z-score, y ensemble
- **Métrica estrella**: User Health Score (propuesta de algoritmo propio)
- **Contexto único**: Todo el pipeline corriendo en < 100MB RAM + CPU-only

### 4.3. Diseño Experimental

| Experimento | Qué mide | Baseline |
|-------------|----------|----------|
| EXP-AI-01 | Clasificador de reclamos (RF) sobre features OTel | Threshold manual |
| EXP-AI-03 | User Health Score vs reclamos reales | Correlación de Pearson |
| EXP-001 a 003 | Isolation Forest ensemble sobre series temporales | Z-score simple |

### 4.4. Ventana de Publicación

| Hito | Fecha |
|------|-------|
| Experimentos ML ejecutados | Sprint 5-8 (Oct-Nov 2026) |
| Borrador del paper | Nov-Dic 2026 |
| Submission a EMSE | Enero 2027 |
| *Plan B: Submission a IEEE Access* | *Feb 2027* |

### 4.5. Por qué EMSE

- **Factor de impacto**: ~4.0
- **Alineación**: Publica estudios empíricos en ingeniería de software
- **Relevancia**: Un estudio que mide predicción de reclamos desde señales de observabilidad es novedoso en el área
- **Riesgo**: Revisión 6-12 meses. Alternativa: IEEE Access (1-3 meses, OA, APC $1850)

> **📌 Para el equipo**: Este es el paper más importante de Romeo. Es su contribución principal al proyecto. Sugiero enfocar todos los experimentos ML de Fase 2 para alimentar este paper.

---

## 5. Artículo D: Experience Report — Quality Gates OTel en I+D+i

### 5.1. Ficha Técnica

| Campo | Detalle |
|-------|---------|
| **Título tentativo** | *"Observability-Driven Quality Gates in Academic Research Projects: An Experience Report"* |
| **Tipo** | Experience report / Short paper |
| **Revistas target** | **IST — Information and Software Technology** (IF ~3.5) > **IEEE Software** (IF ~4.0) |
| **Autores** | Montanari, Rodriguez, Nahuel |
| **Línea** | L4 + L7 — H4 + H7 (DevOps + QA-driven observability) |

### 5.2. Contribución

- Implementación de quality gates basados en señales OTel (latencia p99, error rate, trazas completas)
- Integración en CI/CD de un proyecto I+D+i con equipo pequeño (< 5 personas)
- Comparación contra tests funcionales tradicionales
- Lecciones aprendidas: overhead, falsos positivos, valor para el equipo

### 5.3. Ventana de Publicación

| Hito | Fecha |
|------|-------|
| Pipeline CI/CD real funcionando | Sprint 1-2 (Sep 2026) |
| Quality gates OTel implementados | Sprint 3-4 (Oct 2026) |
| Recolección de métricas de efectividad | Sprint 5-6 (Nov 2026) |
| Borrador del paper | Dic 2026 |
| Submission | Enero 2027 |

### 5.4. Por qué IST

- **Factor de impacto**: ~3.5
- **Enfoque**: Tecnología de software, QA, testing — alineación perfecta
- **Formato**: Acepta experience reports de 8-12 páginas
- **Diferenciación**: No hay muchos reports de quality gates con OTel en proyectos académicos pequeños

---

## 6. Artículo E: Caso de Estudio — Seguridad Zero-Cost en Laboratorios

### 6.1. Ficha Técnica

| Campo | Detalle |
|-------|---------|
| **Título tentativo** | *"Zero-Cost Security Hardening for Academic Laboratories: A Case Study with Ansible and the GLP Stack"* |
| **Tipo** | Caso de estudio |
| **Revistas target** | **IEEE Latin America Transactions** (SCI-E, Scopus) > **RASI** (LatIndex) > **Ciencia y Tecnología UTN** |
| **Autores** | Cavallero, Rodriguez, Nahuel |
| **Línea** | L3 — H3 (Seguridad con recursos cero) |

### 6.2. Contribución

- Metodología de hardening CIS Level 1 con Ansible para laboratorios universitarios
- Pipeline de monitoreo de seguridad con Grafana + Loki + Prometheus (GLP)
- Resultados medibles: Lynis score pre/post, tiempo de detección, costo ($0)
- Reproducible: playbooks de Ansible públicos, dashboards exportables

### 6.3. Por qué IEEE Latin America Transactions

- **Indexación**: SCI-E, Scopus, IEEE Xplore
- **Idioma**: Acepta español/portugués (además de inglés)
- **Visibilidad regional**: Importante para la presencia del grupo GIDAS en Latinoamérica
- **Costo**: Sin APC para miembros IEEE

---

## 7. Artículos Cortos para Revistas Regionales

Además de las revistas internacionales, hay venues regionales con **menor exigencia y revisión más rápida** que sirven para:

1. **Resultados parciales** que no alcanzan para revista internacional
2. **Primeras publicaciones** de los contributors (importante para su currículum)
3. **Difusión en español** para la comunidad académica local

### 7.1. RASI — Revista Argentina de Sistemas de Información

| Propuesta | Título tentativo | Contenido |
|-----------|-----------------|-----------|
| **Artículo 1** | *"IntellOps: Sistema de Observabilidad Predictiva para Laboratorios Universitarios con Recursos Escasos"* | Visión general del proyecto, arquitectura, primeras lecciones aprendidas |
| **Autores** | Todo el equipo | |
| **Extensión** | 6-8 páginas | |
| **Plazo** | 2-3 meses | |

### 7.2. Ciencia y Tecnología — UTN FrLP

| Propuesta | Título tentativo | Contenido |
|-----------|-----------------|-----------|
| **Artículo 2** | *"Observabilidad UX-Céntrica para Infraestructura Académica: Estado del Arte y Desafíos"* | Resumen de la investigación de frontend observability adaptado a público general |
| **Autores** | Rodriguez, Cavallero | |
| **Extensión** | 4-6 páginas | |
| **Plazo** | 1-2 meses | |

| Propuesta | Título tentativo | Contenido |
|-----------|-----------------|-----------|
| **Artículo 3** | *"Selección de Métricas RUM para Monitoreo de Experiencia de Usuario en Entornos Académicos"* | La investigación de Romeo sobre las 5 métricas del MVP, en español |
| **Autores** | Monfroglio | |
| **Extensión** | 4-6 páginas | |
| **Plazo** | 1-2 meses | |

### 7.3. Anales de JAIIO (SCA/SciELO Ar.)

Los anales de JAIIO están indexados en SCA (Scielo Argentina) y son una excelente puerta de entrada:

| Propuesta | Título tentativo | Simposio |
|-----------|-----------------|----------|
| **Artículo 4** | *"DevOps y Quality Gates en Proyectos de Investigación: Lecciones Aprendidas de IntellOps"* | SLCARS (Ing. de Software) |
| **Autores** | Montanari, Rodriguez | |
| **Plazo** | Submission Jul-Ago 2026 para JAIIO Oct 2026 | |

---

## 8. Alternativas de Títulos y Enfoques para el Primer Artículo de Divulgación

El artículo ya escrito en `papers/divulgacion-intellops/articulo.md` puede adaptarse con diferentes títulos, énfasis y estructuras según la revista target. Acá van las variantes:

### 8.1. Para Ingenio Tecnológico (UTN FrLP)

| Campo | Detalle |
|-------|---------|
| **ISSN** | 2618-4931 |
| **Indexación** | LatIndex, DOAJ, Google Scholar, Dialnet, AmeliCA, MALENA (Caicyt-Conicet) |
| **Estilo** | Divulgación científico-tecnológica en español, audiencia de ingeniería general |
| **Extensión** | 6-10 páginas |
| **Licencia** | CC BY-NC-SA 4.0 |

**Título sugerido**: *"IntellOps: Un Sistema de Observabilidad Predictiva para Infraestructura Universitaria con Recursos Escasos"*

**Enfoque**: 
- Énfasis en el **origen institucional**: proyecto de la UTN FrLP, grupo GIDAS, laboratorio InfraIT
- Lenguaje accesible para **ingenieros de todas las especialidades** (no solo informáticos)
- Destacar el **impacto en la comunidad**: herramienta para PYMEs, universidades públicas, extensión
- Incluir **fotos del laboratorio** y del equipo trabajando (valor editorial)
- Mostrar la **aplicación práctica**: "cómo monitoreamos nuestros propios servidores"

**Estructura propuesta**:
```
1. El problema: ¿Por qué es tan cara la observabilidad?
2. ¿Qué es IntellOps? (menos técnico, más conceptual)
3. El laboratorio GIDAS como caso de estudio
4. Resultados esperados e impacto en la comunidad UTN
5. Oportunidades de colaboración y extensión
```

**Diferencias con el artículo actual**:
- Sacar sección 4.3 (stack tecnológico detallado) — muy técnico
- Sacar tabla de limitaciones vs Datadog — no relevante para esta audiencia
- Agregar fotos del laboratorio GIDAS
- Agregar sección de "cómo participar" para otros grupos UTN
- Referencias: menos papers académicos, más fuentes institucionales

---

### 8.2. Para RASI — Revista Argentina de Sistemas de Información

| Campo | Detalle |
|-------|---------|
| **Indexación** | LatIndex, SCA |
| **Estilo** | Sistemas de información, gestión de TI, academia |
| **Extensión** | 6-8 páginas |

**Título sugerido A**: *"Observabilidad UX-Céntrica como Herramienta de Gestión de Infraestructura IT en Organizaciones con Recursos Limitados"*

**Enfoque A**:
- Énfasis en **gestión de sistemas de información**
- Valor para la **toma de decisiones organizacional** (directores de TI, CTOs)
- La observabilidad como **función estratégica**, no solo técnica
- Caso de aplicación en el laboratorio GIDAS

**Título sugerido B**: *"IntellOps: Democratizando la Observabilidad Predictiva para el Sector Público y las PYMEs"*

**Enfoque B**:
- Ángulo de **acceso y equidad tecnológica**
- Brecha entre soluciones enterprise y capacidades del sector público
- Propuesta de valor social y económica

---

### 8.3. Para Ciencia y Tecnología (UTN FrLP)

| Campo | Detalle |
|-------|---------|
| **Indexación** | LatIndex |
| **Estilo** | Divulgación científica breve, extensión universitaria |
| **Extensión** | 4-6 páginas |

**Título sugerido**: *"Formación de Recursos Humanos en Observabilidad IT a través de un Proyecto I+D+i en la UTN FrLP"*

**Enfoque**:
- Énfasis en el **aspecto formativo**: 4 estudiantes de PPS aprendiendo tecnologías de vanguardia
- La observabilidad como **competencia profesional demandada**
- Metodología SDD + Agile como **innovación pedagógica**
- Menos énfasis técnico, más en el **proceso de aprendizaje**

---

### 8.4. Para CLEI (Conferencia Latinoamericana de Informática)

| Campo | Detalle |
|-------|---------|
| **Indexación** | Scopus, IEEE Xplore |
| **Idioma** | Español o inglés |
| **Extensión** | 8-12 páginas |

**Título sugerido**: *"UX-Centric Observability for Resource-Constrained Environments: A Case Study from a Latin American University Lab"*

**Enfoque**:
- Énfasis en el **contexto latinoamericano**: restricciones presupuestarias, realidades regionales
- Comparación con soluciones del norte global
- El nicho "Bajo Recurso + Alta IA" como **oportunidad para la región**
- Resultados preliminares de la implementación

---

### 8.5. Para WICC (Workshop de Investigadores en Ciencias de la Computación)

| Campo | Detalle |
|-------|---------|
| **Estilo** | Trabajos en progreso, primeros resultados |
| **Extensión** | 4-6 páginas |
| **Plazo** | Mayo-Junio (anual) |

**Título sugerido**: *"IntellOps: Avances en Observabilidad Predictiva con ML Liviano y GenIA Local para Entornos Académicos"*

**Enfoque**:
- Paper de **progreso**: qué hicimos, qué aprendimos, qué falta
- Resultados parciales de la investigación
- Oportunidad para presentar al equipo y recibir feedback temprano

---

### 8.6. Para SREcon / ObservabilityCON (Eventos de Industria)

| Campo | Detalle |
|-------|---------|
| **Estilo** | Talk / Lightning talk / Poster |
| **Audiencia** | Ingenieros de infraestructura, SREs, practitioners |

**Título sugerido**: *"How We Built a $0/Month Observability Stack with Local AI and ML for a University Lab"*

**Enfoque**:
- Orientado a **practicantes** que enfrentan el mismo problema
- Demo en vivo del sistema
- Lecciones aprendidas, errores cometidos
- Código abierto y replicable

---

### 8.7. Para Captación de Interesados y Búsqueda de Apoyo Institucional

| Campo | Detalle |
|-------|---------|
| **Tipo** | Artículo comercial / White paper / Nota institucional |
| **Publicación target** | **Revista de Extensión UTN**, **Boletín GIDAS/InfraIT**, **Blog institucional UTN FrLP**, **LinkedIn Pulse**, **Revista Gerencia & Tecnología** |
| **Estilo** | Persuasivo, orientado a valor institucional, ROI, impacto social |
| **Extensión** | 4-6 páginas |
| **Audiencia** | Autoridades académicas (decano, secretarios), directores de laboratorios, posibles sponsors, empresas partners, entes de financiamiento |

**Título sugerido A**: *"IntellOps: Un Proyecto Estratégico para la Soberanía Tecnológica en Observabilidad IT"*

**Enfoque A — Soberanía tecnológica**:
- **Problema**: Las universidades públicas argentinas dependen de software privado extranjero costoso para monitorear su infraestructura. Datadog, Dynatrace y New Relic exigen miles de dólares que el sistema universitario no tiene.
- **Propuesta**: IntellOps demuestra que podemos construir nuestras propias herramientas de clase mundial con recursos locales.
- **Llamado a la acción**: Necesitamos financiamiento para equipamiento (servidores, Raspberry Pis), becas para estudiantes investigadores, y espacio físico en el laboratorio.
- **Valor político**: Soberanía tecnológica, recursos públicos bien invertidos, formación de RRHH en tecnologías estratégicas.

**Título sugerido B**: *"Del Aula a la Industria: Cómo un Proyecto I+D+i de la UTN FrLP Puede Transformar la Gestión de Infraestructura IT en PYMEs y Organismos Públicos"*

**Enfoque B — Transferencia y extensión**:
- **Problema**: Las PYMEs y organismos públicos no tienen acceso a herramientas de observabilidad porque las soluciones comerciales están diseñadas para empresas con presupuestos enterprise.
- **Propuesta**: IntellOps es una herramienta gratuita, open-source, que cualquier organización puede implementar en 30 minutos.
- **Valor para el inversor/sponsor**: 
  - **Visibilidad**: Sponsorear un proyecto de código abierto con proyección internacional
  - **RRHH**: Acceso temprano a estudiantes formados en tecnologías de vanguardia
  - **Responsabilidad social**: Apoyar la democratización tecnológica en el sector público
- **Llamado a la acción**: Donación de equipamiento (servidores, equipamiento de red), becas de investigación, pasantías para estudiantes del equipo.

**Título sugerido C**: *"Observabilidad Predictiva Hecha en Argentina: El Caso de IntellOps en la UTN La Plata"*

**Enfoque C — Prensa/Divulgación masiva**:
- **Tono**: Nota periodística, estilo Newsletter o blog institucional
- **Estructura**:
```
1. Título gancho: "¿Sabías que tu facultad podría estar monitoreando sus servidores con inteligencia artificial sin pagar un peso?"
2. El problema en criollo: las herramientas de monitoreo comerciales son carísimas
3. La solución: un grupo de estudiantes y docentes de la UTN La Plata construyó su propia herramienta
4. El diferencial: corre en PCs viejas, tiene IA, es gratis
5. Qué necesitan: más recursos para escalar y llevar esto a otras instituciones
6. Cómo ayudar: contacto, donaciones, colaboración
```

**Estructura propuesta (para revista institucional)**:
```
1. El contexto: ¿Por qué una universidad pública necesita observabilidad?
2. El proyecto: IntellOps en palabras simples
3. El equipo: 4 estudiantes + 2 docentes investigadores
4. Resultados alcanzados: investigación, métricas, modelo de datos
5. Impacto potencial: otras facultades, PYMEs, organismos públicos
6. Necesidades y cómo apoyar:
   - Equipamiento (servidores, Raspberry Pi para edge computing)
   - Becas de investigación para estudiantes
   - Espacio físico en el laboratorio
   - Vinculación con empresas del sector
7. Conclusión: invertir en I+D+i universitario es invertir en el futuro tecnológico del país
```

**Qué incluir que no está en el artículo académico**:
- Fotos del equipo y del laboratorio (valor humano)
- Testimonios de estudiantes (valor social)
- Cotizaciones comparativas: "esto cuesta en el mercado vs. lo que cuesta acá"
- Logros concretos en lenguaje de gestión: "4 estudiantes formados", "3 documentos de investigación", "5 métricas identificadas"
- Datos de contacto para interesados en apoyar

**Dónde publicarlo**:
| Canal | Por qué |
|-------|---------|
| **Revista de Extensión UTN** | Llega a autoridades de toda la UTN |
| **Boletín GIDAS/InfraIT** | Audiencia interna del grupo de investigación |
| **LinkedIn (publicación del equipo)** | Visibilidad profesional, posibles sponsors |
| **Nota en el sitio de la UTN FrLP** | Prensa institucional, difusión masiva |
| **Presentación en Consejo Directivo** | Búsqueda de aval institucional y recursos |
| **Revista Gerencia & Tecnología** | Llega a decisores de empresas |
| **Foros de innovación educativa** | Conexión con otras unidades académicas |

---

### 8.8. Tabla Comparativa de Enfoques

| Revista | Ángulo principal | Audiencia | Tono | Técnico? | Ideal para |
|---------|-----------------|-----------|------|----------|------------|
| **Ingenio Tecnológico** | Institucional + extensión | Ingenieros general | Divulgativo | Bajo | Primer paper del equipo |
| **RASI** | Gestión de SI + equidad | Académicos SI | Académico medio | Medio | Difusión en sistemas |
| **Ciencia y Tecnología UTN** | Formación RRHH + PPS | Comunidad UTN | Divulgativo | Bajo | Visibilidad local |
| **CLEI** | Contexto latinoamericano | Académicos regionales | Académico alto | Alto | Paper con referato Scopus |
| **WICC** | Trabajo en progreso | Investigadores jóvenes | Académico medio | Medio | Feedback temprano |
| **SREcon** | Practitioner + demo | SREs, industria | Técnico coloquial | Alto | Networking + visibilidad |

---

## 9. Roadmap de Publicaciones 2026-2028

### 9.1. Timeline Visual

```
2026                             2027                             2028
┌────┬────┬────┬────┬────┬────┐ ┌────┬────┬────┬────┬────┬────┐ ┌────┬────┐
│Q3  │Q4  │Q1  │Q2  │Q3  │Q4  │
                                                                                 
[A.Survey] ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
          JSS submission        Revisions         Published
                  
[B.Tool]   ░░░░████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
          Implementación        SPE submission    Revisions   Published

[C.ML]    ░░░░░░░░████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░
          Experimentos          EMSE submission    Revisions  Published

[D.QA]    ░░░░░░░░░░░░████████████░░░░░░░░░░░░░░░░░░░░░░░░
          Pipeline CI listo     IST submission    Revisions  Published

[E.Seg]   ░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
          Hardening + GLP       Submission IEEE Latin America

[Regional] ██░░██░░██░░██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
          RASI, UTN, JAIIO — artículos cortos intercalados
```

### 9.2. Tabla de Prioridades

| Prioridad | Artículo | Revista | Plazo submission | Autor principal |
|-----------|----------|---------|-----------------|-----------------|
| 🔴 **Inmediata** | Comercial 1: "IntellOps: captación de interesados" | Revista de Extensión UTN / LinkedIn | **Agosto 2026** | Emanuel |
| 🔴 **Inmediata** | Regional 1: "IntellOps: visión general" | Ingenio Tecnológico / RASI | **Agosto 2026** | Emanuel |
| 🔴 **Inmediata** | Regional 2: "Selección de métricas RUM" | Ciencia y Tecnología UTN | **Agosto 2026** | Romeo |
| 🔴 **Inmediata** | JAIIO 2026: "DevOps en I+D+i" | Anales JAIIO (SLCARS) | **Jul-Ago 2026** | Santiago |
| 🟡 **Corto plazo** | Artículo E: "Seguridad zero-cost" | IEEE Latin America Trans. | **Oct 2026** | Federico |
| 🟡 **Mediano** | Artículo A: Survey | JSS → ACM CSUR | **Nov 2026** | Emanuel |
| 🟡 **Mediano** | Artículo B: Tool paper RUM | SPE | **Nov 2026** | Federico |
| 🟢 **Mediano-largo** | Artículo C: Predicción reclamos | EMSE → IEEE Access | **Ene 2027** | Romeo |
| 🟢 **Mediano-largo** | Artículo D: Quality gates OTel | IST → IEEE Software | **Ene 2027** | Santiago |

### 9.3. Estrategia de Autores

| Artículo | Primer autor | Coautores | Orden propuesto |
|----------|-------------|-----------|-----------------|
| A — Survey | Rodriguez | Monfroglio, Cavallero, Montanari, Nahuel | Rodriguez, Monfroglio, Cavallero, Montanari, Nahuel |
| B — Tool RUM | Cavallero | Rodriguez, Nahuel | Cavallero, Rodriguez, Nahuel |
| C — ML predictivo | Monfroglio | Rodriguez, Nahuel | Monfroglio, Rodriguez, Nahuel |
| D — QA OTel | Montanari | Rodriguez, Nahuel | Montanari, Rodriguez, Nahuel |
| E — Seguridad | Cavallero | Rodriguez, Nahuel | Cavallero, Rodriguez, Nahuel |

> **Nota**: El orden de autores sigue el estándar del grupo: primer autor = quien hace el trabajo principal. El director (Nahuel) va al final como supervisor. El coordinador (Rodriguez) va enmedio como guía metodológica.

---

## 10. Siguientes Pasos Concretos

### 10.1. Acciones para Esta Semana

| # | Acción | Responsable | Tiempo estimado |
|---|--------|-------------|-----------------|
| 1 | Elegir 1 artículo regional para escribir YA | **Equipo** | Discutir en Sprint 0 |
| 2 | Crear carpeta `papers/` en el repo con estructura estándar | **Emanuel** | 30 min |
| 3 | Definir template de paper (IEEE/ACM/Elsevier según target) | **Emanuel** | 1 hora |
| 4 | Armar esquema del paper regional 1 | **Equipo** | 2 horas |

### 10.2. Estructura de Carpeta Propuesta

```
papers/
├── README.md                     ← Instrucciones y estado de cada paper
├── templates/
│   ├── ieee-conference.tex       ← Template IEEE para conferencias
│   ├── elsevier-journal.tex      ← Template Elsevier para revistas
│   └── acm-sigconf.tex           ← Template ACM
├── 2026-survey-ux-observability/ ← Artículo A
│   ├── README.md                 ← Estado, autores, deadline
│   ├── outline.md                ← Esquema detallado
│   ├── figures/                  ← Figuras y diagramas
│   ├── references.bib            ← Bibliografía
│   ├── draft-v1.tex              ← Borrador en evolución
│   └── submission/               ← Versión final + proof of submission
├── 2026-tool-rum-agent/          ← Artículo B
├── 2027-ml-complaint-prediction/ ← Artículo C
└── ...
```

### 10.3. Checklist para Cada Paper

Cada paper debe tener:

- [ ] **Outline aprobado** por el equipo antes de escribir
- [ ] **Figuras y tablas** definidas primero (ayudan a clarificar la historia)
- [ ] **Abstract de 200 palabras** que responda: problema, método, resultado, contribución
- [ ] **Datos y código** con DOI (Zenodo/OSF) para reproducibilidad
- [ ] **Revisión interna** por al menos 1 miembro del equipo que no sea autor
- [ ] **Proofreading** de inglés (si aplica) por hablante nativo o herramienta
- [ ] **Submission** con todos los metadatos correctos

### 10.4. Recursos Necesarios

| Recurso | Costo | Notas |
|---------|-------|-------|
| Overleaf (colaborativo) | Gratis | 1 proyecto compartido por paper |
| Zenodo DOI para datasets | Gratis | Vinculado a GitHub |
| Grammarly / LanguageTool | Gratis | Proofreading básico |
| IEEE membership | ~$50/año | Descuento en submission fees |
| APC IEEE Access | $1.850 | Solo si no hay otra opción |

---

## Apéndice: Matriz de Elegibilidad por Revista

| Revista | IF | Indexación | Idioma | APC | Revisión | Fit para IntellOps |
|---------|----|------------|--------|-----|----------|-------------------|
| **ACM CSUR** | ~23.0 | SCI-E, Scopus | Inglés | $0 (opcional) | 12-18 meses | Survey general |
| **IEEE TSE** | ~7.0 | SCI-E, Scopus | Inglés | $0 (opcional) | 6-12 meses | Papers de IS profundo |
| **IEEE Software** | ~4.0 | SCI-E, Scopus | Inglés | $0 (opcional) | 2-4 meses | Tool papers cortos |
| **EMSE** | ~4.0 | SCI-E, Scopus | Inglés | $0 (opcional) | 6-12 meses | Estudios empíricos |
| **IST** | ~3.5 | SCI-E, Scopus | Inglés | $0 (opcional) | 4-8 meses | QA, testing |
| **JSS** | ~3.0 | SCI-E, Scopus | Inglés | $0 (opcional) | 4-8 meses | Herramientas, surveys |
| **IEEE Access** | ~3.5 | SCI-E, Scopus | Inglés | $1.850 | 1-3 meses | Plan B rápido |
| **SPE** | ~2.5 | SCI-E, Scopus | Inglés | $0 (opcional) | 3-6 meses | Tool papers |
| **IEEE LATAM** | ~1.5 | SCI-E, Scopus | Español/Inglés | $0 (miembro) | 3-6 meses | Casos regionales |
| **JWE** | ~1.0 | Scopus | Inglés | $0 (opcional) | 2-4 meses | RUM, frontend |
| **RASI** | — | LatIndex | Español | $0 | 3-6 meses | Primeros papers |
| **Ciencia y Tecnología UTN** | — | LatIndex | Español | $0 | 2-4 meses | Divulgación local |

---

*Documento vivo. Versión 1.0 — Julio 2026. Equipo InfraIT GIDAS — UTN FrLP.*
