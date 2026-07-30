# Observabilidad UX-Céntrica para Entornos con Recursos Escasos: El Caso de IntellOps en el Laboratorio GIDAS

## UX-Centric Observability for Resource-Constrained Environments: The IntellOps Case at GIDAS Laboratory

---

**Autores**: Emanuel Rodriguez, Federico Blanco Cavallero, Romeo L. Monfroglio, Santiago Montanari, Leopoldo Nahuel

**Afiliación**: Grupo GIDAS — UTN Facultad Regional La Plata, Argentina
{coord@intellops.gidas.utn.edu.ar}

**Línea de investigación**: Sistemas Inteligentes de Infraestructura IT — Ingeniería de Recursos Escasos

**Tipo de artículo**: Artículo de divulgación científica — Revisión y Caso de Estudio

---

## Resumen

La observabilidad se ha convertido en un pilar fundamental de la ingeniería de software moderna. Sin embargo, las soluciones comerciales líderes (Datadog, Dynatrace, New Relic) tienen costos que las hacen inaccesibles para universidades públicas, PYMEs y organizaciones con presupuestos limitados. Este artículo presenta IntellOps, un proyecto de investigación, desarrollo e innovación (PI+D+i) del grupo GIDAS de la UTN Facultad Regional La Plata, que diseña un sistema de observabilidad predictiva centrado en el usuario real, diseñado para operar en hardware de bajo rendimiento (< 2GB RAM, CPU sin GPU) con costo operativo cero. Se analiza el valor de la observabilidad desde la perspectiva del usuario para una organización, el estado del arte de la observabilidad UX-céntrica, el nicho inexplorado de "Bajo Recurso + Alta Inteligencia Artificial", y las oportunidades académicas y de extensión que un proyecto de esta naturaleza genera para un grupo de investigación universitario.

**Palabras clave**: Observabilidad, UX-Céntrica, Recursos Escasos, OpenTelemetry, ML Liviano, I+D+i, Extensión Universitaria.

---

## Abstract

Observability has become a fundamental pillar of modern software engineering. However, leading commercial solutions (Datadog, Dynatrace, New Relic) have costs that make them inaccessible to public universities, SMEs, and organizations with limited budgets. This article presents IntellOps, a research, development, and innovation project (R&D+i) from the GIDAS group at UTN La Plata Regional Faculty, which designs a predictive observability system centered on the real user, designed to operate on low-performance hardware (< 2GB RAM, CPU without GPU) with zero operational cost. We analyze the value of observability from the user's perspective for an organization, the state of the art of UX-centric observability, the unexplored niche of "Low Resource + High AI", and the academic and extension opportunities that such a project generates for a university research group.

**Keywords**: Observability, UX-Centric, Resource-Constrained, OpenTelemetry, Lightweight ML, R&D+i, University Extension.

---

## 1. Introducción

### 1.1. La Observabilidad como Imperativo de la Industria del Software

En la industria del software actual, la observabilidad ha dejado de ser un lujo para convertirse en una necesidad operativa. A medida que las arquitecturas de software evolucionaron de monolitos a microservicios, y los despliegues pasaron de releases semestrales a múltiples entregas diarias, los equipos de operaciones perdieron la capacidad de entender qué estaba sucediendo dentro de sus sistemas simplemente "mirando los logs" [1].

El concepto de observabilidad, tomado de la teoría de control y popularizado en ingeniería de software por Charity Majors, Cindy Sridharan y otros referentes, se define como la capacidad de inferir el estado interno de un sistema a partir de sus outputs externos [2]. A diferencia del monitoreo tradicional —que responde a la pregunta "¿esto funciona?"—, la observabilidad busca responder "¿por qué esto no funciona?" y, en su estado más maduro, "¿qué va a fallar antes de que falle?".

Este cambio de paradigma llevó al surgimiento de plataformas especializadas como Datadog, Dynatrace y New Relic, que se convirtieron en herramientas indispensables para equipos de infraestructura. Sin embargo, estas soluciones presentan una barrera de entrada significativa: Datadog puede costar entre 500.000 y 2 millones de dólares anuales para organizaciones medianas [3], y Dynatrace requiere infraestructura cloud de alto rendimiento para sus motores de IA causal [4].

### 1.2. El Problema del Acceso

Para una universidad pública argentina, para una PYME local, o para un laboratorio de investigación con presupuesto ajustado, estos costos son prohibitivos. La alternativa open-source (Prometheus + Grafana + Loki) es técnicamente viable pero requiere un esfuerzo de integración manual que pocas organizaciones pueden sostener sin un equipo dedicado de MLOps [5].

Existe, por lo tanto, una brecha entre la necesidad de observabilidad y la capacidad de acceso a ella. Esta brecha no es solo económica —es también técnica y formativa. Las universidades públicas necesitan formar profesionales en observabilidad, pero no pueden pagar las herramientas que la industria utiliza.

### 1.3. El Enfoque Centrado en el Usuario

Paralelamente, la industria está experimentando un segundo cambio de paradigma: de la observabilidad de infraestructura (monitorear servidores) a la observabilidad centrada en el usuario (monitorear la experiencia real de las personas). Google introdujo los Core Web Vitals (LCP, INP, CLS) como métricas estándar de experiencia de usuario [6], y OpenTelemetry se consolidó como el estándar CNCF para instrumentación vendor-neutral [7].

Este enfoque reconoce que un servidor puede estar funcionando perfectamente —CPU al 30%, memoria estable, sin errores 5xx— mientras que el usuario final experimenta una aplicación lenta, errores de JavaScript silenciosos, o una interfaz que no responde. La observabilidad UX-céntrica busca cerrar esa brecha entre "el servidor está bien" y "el usuario está frustrado".

### 1.4. Objetivo de este Artículo

Este artículo presenta IntellOps, un proyecto PI+D+i del grupo GIDAS de la UTN Facultad Regional La Plata, que aborda simultáneamente ambos problemas: (1) la inaccesibilidad económica de las soluciones comerciales, y (2) la necesidad de una observabilidad centrada en el usuario real. Se analiza el contexto de la industria, el valor para la organización y para el grupo de investigación, el nicho de mercado identificado, y las oportunidades académicas y de extensión que genera.

---

## 2. El Valor de la Observabilidad desde la Perspectiva del Usuario

### 2.1. Del Monitoreo de Máquinas a la Medición de Experiencias

Tradicionalmente, las métricas de infraestructura responden a preguntas técnicas: "¿Cuánta RAM está usando el servidor?", "¿Cuál es la latencia p99 del endpoint?". Estas métricas son necesarias pero insuficientes para entender el impacto real en el usuario.

La observabilidad UX-céntrica agrega una capa adicional de preguntas: "¿Cuánto tiempo tardó la página en mostrarle contenido útil al usuario en Salta con conexión 4G?", "¿Cuántos usuarios hicieron clic repetidamente en un botón que no respondía?", "¿Qué errores de JavaScript experimentaron los usuarios antes de abandonar el sistema?".

Estas preguntas revelan una verdad incómoda para muchos equipos de IT: **un sistema puede estar técnicamente saludable y simultáneamente estar fallando para sus usuarios**.

### 2.2. Las 5 Métricas que Definen la Experiencia de Usuario

La investigación en IntellOps identificó 10 métricas fundamentales de observabilidad frontend, de las cuales 5 fueron seleccionadas para el Producto Mínimo Viable (MVP) por su simplicidad técnica, calidad de datos para Machine Learning, y valor diagnóstico [8]:

| Métrica | ¿Qué mide? | ¿Qué frustración del usuario previene? |
|---------|------------|---------------------------------------|
| **TTFB** (Time to First Byte) | Tiempo hasta que el servidor responde | La "pantalla blanca" donde el navegador no recibe datos |
| **FCP** (First Contentful Paint) | Cuándo aparece el primer píxel en pantalla | La "ceguera inicial": el usuario no sabe si la página cargó |
| **XHR/Fetch Latency** | Latencia de llamadas asíncronas | El "spinner infinito": el usuario espera sin saber si la operación progresa |
| **JS Exception Rate** | Errores de JavaScript en el navegador | Los "botones que no funcionan": errores silenciosos que rompen flujos |
| **Rage Clicks** | Clics repetitivos en un mismo elemento | La "frustración explícita": el usuario golpea la interfaz porque no responde |

### 2.3. Impacto Organizacional

Para una organización, adoptar observabilidad UX-céntrica tiene impactos medibles:

1. **Reducción del MTTR (Mean Time to Resolution)**: Poder correlacionar una queja de usuario ("la web está lenta") con una métrica objetiva (LCP > 4 segundos en la región del usuario) reduce el tiempo de diagnóstico de horas a minutos.

2. **Anticipación de reclamos**: La combinación de métricas en tiempo real con modelos de Machine Learning permite detectar degradaciones antes de que los usuarios las reporten. Estudios recientes en AIOps muestran que la detección predictiva puede anticipar entre el 70% y el 85% de los incidentes [9].

3. **Priorización basada en impacto real**: No todos los problemas técnicos tienen el mismo impacto en el usuario. Tener métricas de experiencia permite priorizar la reparación de aquellos componentes que realmente afectan a las personas.

4. **Rendición de cuentas con datos**: Para equipos que deben reportar a autoridades académicas o directivos, tener métricas objetivas de experiencia de usuario permite pasar de "sentimos que el sistema está lento" a "el percentil 75 de LCP aumentó 40% en el último mes".

---

## 3. Estado del Arte y Nicho de Mercado

### 3.1. El Panorama de la Observabilidad en 2026

El mercado de observabilidad en 2026 está dominado por tres categorías de soluciones:

**Soluciones comerciales SaaS** (Datadog, Dynatrace, New Relic): Ofrecen el conjunto más completo de funcionalidades —detección de anomalías con IA, trazabilidad distribuida, dashboards personalizables— pero a costos que las hacen inaccesibles para organizaciones con presupuestos acotados. Datadog, por ejemplo, cotiza en NASDAQ con una capitalización de mercado superior a los 40 mil millones de dólares, y su modelo de negocio se basa en el volumen de datos ingeridos [3].

**Plataformas open-source** (Grafana LGTM, SigNoz, OpenObserve): Ofrecen alternativas gratuitas en licencia pero requieren infraestructura significativa para su operación. El stack Grafana LGTM (Loki, Grafana, Tempo, Mimir) necesita al menos 4-8 GB de RAM para funcionar con un mínimo de utilidad, y su configuración requiere conocimientos especializados que no siempre están disponibles en equipos pequeños [10].

**Soluciones de monitoreo simples** (Netdata, Uptime Kuma): Son livianas y fáciles de instalar, pero carecen de capacidades predictivas avanzadas, trazabilidad distribuida, o inteligencia artificial para análisis de causa raíz.

### 3.2. El Nicho Identificado: "Bajo Recurso + Alta IA"

El análisis del estado del arte reveló un vacío que ninguna solución existente cubre: **la combinación de operación en hardware modesto (< 2GB RAM, CPU dual-core, sin GPU) con inteligencia artificial avanzada (ML predictivo + LLM local para análisis de causa raíz)**.

```
                    ↑ ALTA IA
                    │
          Dynatrace │    ★ IntellOps
          Datadog   │    (Nicho)
          New Relic │
                    │
    ────────────────┼───────────────────→ BAJOS RECURSOS
                    │
      SigNoz        │    Netdata
      OpenObserve   │    Prometheus
      Grafana LGTM  │    Uptime Kuma
                    │
                    ↓ BAJA IA
```

**Figura 1**: Mapa de posicionamiento de soluciones de observabilidad según recursos requeridos vs capacidad de IA.

Este cuadrante —que llamamos "Bajo Recurso + Alta IA"— es donde IntellOps se posiciona. No compite con Datadog en funcionalidades enterprise; compite con la ausencia de observabilidad en organizaciones que hoy no pueden acceder a ninguna solución.

### 3.3. Tendencias de la Industria 2025-2026

La investigación identificó seis tendencias que validan la pertinencia del proyecto [11]:

1. **OpenTelemetry como estándar de facto**: La CNCF consolidó OpenTelemetry como el estándar de instrumentación vendor-neutral, con adopción masiva incluso por parte de los proveedores comerciales.

2. **ML en el edge para observabilidad**: Netdata demostró que es posible ejecutar 18 modelos de ML no supervisados por métrica con menos del 5% de CPU adicional [12].

3. **LLMs locales para SRE**: El avance de modelos cuantizados (Llama 3.2 1B, Phi-3, Gemma 2) permite ejecutar asistentes de IA en CPU con consumo de RAM manejable [13].

4. **Core Web Vitals como estándar regulatorio de facto**: Google convirtió a LCP, INP y CLS en factores de ranking y la industria los adoptó como métricas universales de experiencia de usuario [6].

5. **eBPF para observabilidad sin instrumentación**: Tecnologías como Cilium y Pixie (CNCF) permiten observar sistemas sin modificar el código de las aplicaciones.

6. **Kubernetes ligero para edge**: K3s y MicroK8s demostraron que es posible ejecutar orquestación de contenedores en Raspberry Pi con 512 MB de RAM [14].

---

## 4. IntellOps: Arquitectura y Aportes del Proyecto

### 4.1. Visión General

IntellOps es un sistema de observabilidad predictiva que integra cuatro pilares fundamentales:

1. **Métricas de UX**: Captura de Core Web Vitals (LCP, INP, CLS) más métricas complementarias (TTFB, FCP, errores JS, Rage Clicks) mediante un agente RUM basado en OpenTelemetry JS SDK con bundle inferior a 30KB.

2. **Trazas distribuidas**: Correlación del viaje completo del usuario desde el navegador hasta el backend mediante OpenTelemetry y Grafana Tempo.

3. **ML predictivo**: Detección de anomalías con Isolation Forest + Z-score dinámico + Seasonal Decomposition, operando en menos de 50 MB de RAM.

4. **GenIA local**: Asistente de análisis de causa raíz (RCA) basado en Llama 3.2 1B cuantizado, ejecutándose en CPU con aproximadamente 600 MB de RAM bajo demanda.

### 4.2. Principio de Diseño: Ingeniería de Recursos Escasos

El proyecto adopta explícitamente la **ingeniería de recursos escasos** como restricción de diseño, no como excusa. Esto significa que cada decisión tecnológica se evalúa contra el criterio de "¿puede esto funcionar en un servidor legacy del laboratorio con menos de 2 GB de RAM?".

Esta restricción genera innovaciones que no aparecerían en entornos con recursos abundantes: uso de SQLite con índices temporales en lugar de bases de datos dedicadas, buffers sin middleware de mensajería, modelos ML que ejecutan inferencia en CPU en lugar de GPU, y LLMs cuantizados de 1B de parámetros en lugar de modelos de 70B+.

### 4.3. Stack Tecnológico

| Capa | Tecnología | Alternativa descartada | Justificación |
|------|-----------|----------------------|---------------|
| Instrumentación | OpenTelemetry JS SDK | Agentes propietarios | Estándar CNCF, vendor-neutral |
| Backend | FastAPI + SQLite | Django, PostgreSQL | Async nativo, < 100 MB RAM |
| Trazas | Grafana Tempo | Jaeger, Zipkin | OTel-native, < 256 MB RAM |
| Logs | Grafana Loki | ELK Stack | ADR-0001: licencias SSPL incompatibles |
| Métricas | Prometheus | InfluxDB | Estándar CNCF |
| ML | scikit-learn (Isolation Forest) | PyTorch LSTM | < 50 MB RAM, CPU-only |
| GenIA | Llama 3.2 1B (llama.cpp) | GPT-4 API | 600 MB RAM, sin costo de API |
| Dashboard | Grafana + React estático | Datadog, New Relic | Sin licencias adicionales |
| Contenedores | Docker Compose | Kubernetes | Setup < 30 min, sin orquestación |

**Footprint total del sistema**: < 2 GB RAM | < 2 cores CPU | < 10 GB disco | **$0/mes costo operativo**

### 4.4. Metodología de Desarrollo

El proyecto adopta **Spec-Driven Development (SDD)** como metodología principal, combinado con Agile (Scrum/Kanban híbrido) y DevOps (CI/CD con GitHub Actions). Las especificaciones se mantienen en formato OpenAPI 3.1 + AsyncAPI 3.0 como fuente de verdad, y todo cambio sigue el flujo: Idea → Spec → Review → Código → PR → Archive [15].

---

## 5. Aportes y Oportunidades Académicas y de Extensión

### 5.1. Para el Grupo de Investigación GIDAS

El proyecto IntellOps genera valor para el grupo GIDAS en múltiples dimensiones:

**Formación de recursos humanos**: Cuatro estudiantes desarrollan habilidades en observabilidad, ML, GenIA, DevOps e ingeniería de software a través de Prácticas Profesionales Supervisadas (PPS). Estas competencias son altamente demandadas en la industria y difícilmente adquiribles en el aula sin un proyecto concreto.

**Publicaciones científicas**: El proyecto tiene identificados al menos 6 artículos potenciales para revistas con referato (JSS, EMSE, SPE, IST, IEEE Latin America Transactions) y conferencias (JAIIO, CACIC, CLEI, SREcon, ISSRE), cubriendo desde surveys del estado del arte hasta estudios empíricos con resultados experimentales.

**Reproducibilidad científica**: Todo el código, datos y experimentos son públicos y reproducibles. Cada resultado puede ser verificado por cualquier investigador ejecutando `docker compose up`. Esto es un diferencial importante en un campo donde la mayoría de los estudios se publican sin código ni datos accesibles.

**Fortalecimiento del laboratorio**: El sistema se despliega sobre la infraestructura existente del laboratorio GIDAS, mejorando la capacidad de monitoreo del propio grupo y sirviendo como demo funcional para visitas, ferias de ciencia y actividades de extensión.

### 5.2. Oportunidades de Extensión Universitaria

La extensión universitaria es uno de los tres pilares de la universidad pública argentina (junto con la docencia y la investigación). IntellOps abre varias líneas de extensión:

**Transferencia tecnológica a PYMEs y otras universidades**: El sistema está diseñado para ser replicable en cualquier organización con recursos limitados. La documentación y los scripts de automatización permiten que otro laboratorio o PYME despliegue su propio sistema de observabilidad en menos de 30 minutos.

**Colaboración interinstitucional**: El proyecto puede integrarse con otros grupos de investigación de la UTN y de otras universidades nacionales que enfrentan los mismos problemas de recursos limitados. Cada nuevo laboratorio que adopte IntellOps genera datos comparativos que fortalecen la investigación.

**Formación de comunidad open-source**: Al publicar todo el código bajo licencia Apache-2.0, el proyecto invita a contribuciones externas. Una comunidad activa alrededor de IntellOps multiplica el impacto del proyecto más allá del ciclo de financiamiento inicial.

**Material didáctico**: Los experimentos, dashboards y datasets generados sirven como material educativo para materias de grado vinculadas a infraestructura IT, ingeniería de software, ML y seguridad informática.

### 5.3. Impacto Social

Más allá de lo académico, IntellOps tiene un impacto social concreto: **democratizar el acceso a la observabilidad**. En un contexto donde las herramientas fundamentales para operar infraestructura IT tienen costos prohibitivos para el sector público y las PYMEs, un sistema funcional, gratuito y de código abierto reduce la brecha tecnológica entre organizaciones con recursos y organizaciones sin ellos.

---

## 6. Estado Actual y Trabajo Futuro

### 6.1. Estado del Proyecto (Julio 2026)

A la fecha de este artículo, el proyecto ha completado su **Fase de Documentación e Investigación**:

- Investigación del estado del arte de frontend observability (929 líneas)
- Análisis técnico profundo de agentes RUM y arquitectura OpenTelemetry (1.207 líneas)
- Estudio comparativo de 12 plataformas de observabilidad (845 líneas)
- Catálogo de 50+ venues académicos e industriales para publicación
- Diseño del modelo de datos (DER V1.2) con soporte multi-tenant y MLOps
- Investigación de 10 métricas RUM con selección de 5 para MVP
- Análisis de caso de negocio y especificación de 9+ historias de usuario
- Plan de trabajo detallado con 12+ tareas por contributor

El equipo se encuentra en transición hacia la **Fase de Desarrollo** (Sprint 0), que incluye la implementación del pipeline de datos, el agente RUM, los modelos ML y el dashboard.

### 6.2. Trabajo Futuro

Los próximos hitos del proyecto incluyen:

1. Implementación del pipeline de ingesta de métricas con FastAPI + SQLite
2. Desarrollo del agente RUM con OpenTelemetry JS SDK
3. Entrenamiento y evaluación de modelos ML (Isolation Forest + ensemble)
4. Implementación del dashboard React con D3.js
5. Integración del asistente GenIA local con Llama 3.2 1B
6. Validación experimental de las 7 hipótesis de investigación
7. Publicación de resultados en revistas y conferencias
8. Despliegue en laboratorios piloto de otras universidades

---

## 7. Conclusiones

La observabilidad es una necesidad imperativa en la industria del software actual, pero las soluciones existentes presentan barreras económicas y técnicas significativas para organizaciones con recursos limitados. IntellOps demuestra que es posible construir un sistema de observabilidad predictiva centrado en el usuario real, con inteligencia artificial local y ML liviano, operando en hardware modesto con costo cero.

Para el grupo GIDAS de la UTN Facultad Regional La Plata, el proyecto representa una oportunidad única de formación de recursos humanos, producción científica, transferencia tecnológica y extensión universitaria. El nicho identificado —"Bajo Recurso + Alta IA"— no está cubierto por ninguna solución existente, posicionando a IntellOps como una contribución original tanto en el ámbito académico como en el práctico.

La decisión de adoptar estándares abiertos (OpenTelemetry, OpenAPI, AsyncAPI), código abierto (licencia Apache-2.0) y metodologías modernas (SDD, DevOps) asegura que los resultados del proyecto sean sostenibles, reproducibles y transferibles. En un contexto de restricciones presupuestarias crecientes en el sistema universitario público argentino, IntellOps propone una respuesta concreta: hacer más con menos, pero haciéndolo bien, documentado y compartido.

---

## Referencias

[1] C. Sridharan, "Distributed Systems Observability," O'Reilly Media, 2018.

[2] C. Majors, L. Fong-Ching, y A. Bets, "Observability Engineering," O'Reilly Media, 2022.

[3] Datadog, "Datadog Pricing," https://www.datadoghq.com/pricing/, 2026.

[4] Dynatrace, "Dynatrace Platform Pricing," https://www.dynatrace.com/pricing/, 2026.

[5] CNCF, "Cloud Native Landscape: Observability and Analysis," https://landscape.cncf.io/, 2026.

[6] Google Chrome Team, "Web Vitals," https://web.dev/articles/vitals, 2024.

[7] CNCF, "OpenTelemetry Documentation," https://opentelemetry.io/docs/, 2026.

[8] R. Monfroglio, "Estrategia de Observabilidad: Elección de Métricas Fundamentales para el MVP," IntellOps Research Documents, 2026.

[9] Z. Zhong et al., "A Survey of Time Series Anomaly Detection Methods in the AIOps Domain," arXiv:2308.00393, 2023.

[10] Grafana Labs, "Grafana LGTM Stack Documentation," https://grafana.com/docs/, 2026.

[11] E. Rodriguez, "Observability Tools Industry Analysis with Research Gaps," IntellOps Research Documents, 2026.

[12] Netdata, "Netdata ML Documentation," https://learn.netdata.cloud/docs/ml/, 2026.

[13] Meta AI, "Llama 3.2 Model Card," https://github.com/meta-llama/llama-models, 2024.

[14] CNCF, "K3s - Lightweight Kubernetes," https://k3s.io/, 2026.

[15] E. Rodriguez, "Brief del Proyecto IntellOps Redefinido v2.0," IntellOps Project Documentation, 2026.

[16] Google Chrome Team, "Interaction to Next Paint (INP)," https://web.dev/articles/inp, 2024.

[17] E. Rodriguez, "Frontend Observability State of the Art," IntellOps Research Documents, 2026.

[18] E. Rodriguez, "RUM Agent: Deep Research and Architecture," IntellOps Research Documents, 2026.

---

*Proyecto IntellOps — PI+D+i GIDAS · UTN Facultad Regional La Plata · 2026*
*Código fuente: https://github.com/infraitgidas/intellops*
*Licencia: Apache-2.0*
