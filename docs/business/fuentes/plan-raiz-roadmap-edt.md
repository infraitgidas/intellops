# IntellOps — Plan de Gestión, Roadmap y EDT

Oct 16, 2026 · @Emanuel Rodriguez

## Respuesta a las 5 observaciones de la dirección

Las cinco observaciones son correctas y comparten una causa: el proyecto tiene documentos por persona, pero no una estructura de gestión compartida. La respuesta es un equipo único con tres frentes paralelos, un roadmap con hitos fechados y un EDT cargado como issues.

| # | Observación | Evidencia en el repositorio | Medida propuesta |
| --- | --- | --- | --- |
| 1 | Sin rumbo ni gestión | El charter define dailies, sprints y retros, pero no hay milestones, tablero ni retros documentadas. El PR #7 (+5.399 líneas) no tuvo ninguna revisión. | Product Owner nombrado, tablero con milestones y 5 hitos con criterio de salida (sección 3). |
| 2 | Sin EDT, Gantt ni continuidad | No hay EDT ni cronograma en el repo. La minuta del 20-07 acordó llevar el EDT a Issues; no pude verificar si existe. | EDT de 4 niveles y Gantt semanal (secciones 4 y 5), cargados como issues. |
| 3 | Pasantes sin direccionalidad | El plan de trabajo asigna Fase 1 por persona: auditoría Lynis, hardening CIS, pipeline de logs de seguridad. Ninguna de esas tareas es parte del MVP. | Toda tarea debe colgar de un hito del producto. Lo que no aporta al MVP sale del camino crítico. |
| 4 | Sin roadmap claro | El roadmap del README usa sprints sin fechas. Hay dos definiciones de producto: infraestructura con Python (caso de negocio) y RUM en navegador (HU y brief v2). | Un solo brief de producto y un roadmap por horizontes con fechas (sección 3). |
| 5 | Trabajo en cascada, no colaborativo | El charter exige completar la Fase 1 antes de la Fase 2. En el plan, T2.1 depende de T2.2 y T2.2 depende de T2.1: dependencia circular. | Squad único con 3 frentes paralelos que integran en cada sprint (sección 6). |

Hay además un factor de calendario: según `constraints.md`, las pasantías de dos integrantes terminan en octubre de 2026 y el charter fija septiembre para el tercero. La continuidad deja de ser un riesgo futuro.

## Alcance: primero ver como el usuario y ver al usuario, después predecir

El MVP debe medir desde afuera lo que vive el usuario de un sitio o app; el ML y el LLM entran cuando haya datos etiquetados. Esto unifica las dos definiciones de producto que hoy conviven en el repo: IntellOps es observabilidad del lado del cliente con dos sensores, RUM (usuarios reales) y sondas sintéticas (disponibilidad medida activamente).

| Capacidad pedida | Sensor | Entra en | Estado en el repo |
| --- | --- | --- | --- |
| Uptime y disponibilidad | Sondas HTTP/HTTPS | M1 | No existe |
| Métricas de frontend (TTFB, FCP, errores JS, rage clicks) | Agente RUM | M1 | Investigado, sin código |
| Endpoints y APIs (latencia, errores, XHR) | RUM + sondas de API | M1 | Solo XHR planificado en RUM |
| TLS y DNS | Sondas | M1 | Solo como tiempos del navegador |
| Alertas por mail y Telegram | Alertmanager | M1 básico, M2 por sensibilidad | Planificado |
| Hosting e ISP | Enriquecimiento por ASN y geolocalización | M2 | No existe |
| Escenarios (recorridos de usuario) | Sintético multi-paso | M2 | Planificado solo como QA |
| Analítica preventiva con ML | Detección sobre series | M2 | Hipótesis sin código |
| LLM local que explica anomalías | Llama 3.2 1B + RAG | M3 | Sin código |

Quedan fuera del camino crítico y pasan a un backlog de servicios de extensión: la auditoría Lynis, el hardening CIS con Ansible y el pipeline de logs de seguridad de la Fase 1 de Federico, además de LSTM, Kafka y Redis. Son trabajos valiosos, pero no acercan el MVP.

Las sondas multi-punto necesitan al menos dos redes de origen distintas (por ejemplo el laboratorio y una instancia en un free-tier cloud). Para ISP y ASN hay que verificar la licencia de la base de datos de geolocalización antes de adoptarla.

## Roadmap de producto y de proyecto

&#91;embedded content: roadmap · 5 fases, 5 hitos\]

M1 es el primer hito que la dirección puede ver funcionando: un sitio real medido con RUM y sondas. M2 y M3 exigen un dataset etiquetado como condición de entrada, para que el ML y el LLM no avancen sin datos.

## EDT: paquetes de trabajo

&#91;embedded content: EDT · 6 paquetes, 26 hojas\]

Cada hoja se carga como un issue con etiqueta de hito (M0 a M4) y de frente (F1 a F3). Los paquetes 4, 5 y 6 son los tres frentes de la sección de modelo de trabajo; los paquetes 1 a 3 los conduce el Product Owner con la dirección.

## Cronograma

&#91;embedded content: cronograma · 16 tareas, 5 hitos, oct 2026 a jun 2027\]

Las barras de captura y plataforma empiezan el 2 de noviembre, antes de cerrar la fase A, porque trabajan contra los contratos del sprint 1. La línea punteada marca M1 y la franja gris el receso, durante el cual el piloto sigue midiendo.

## Modelo de trabajo: un equipo, tres frentes, un sprint común

En lugar de un pasante tras otro, el equipo trabaja en tres frentes simultáneos que se integran cada dos semanas en una demo de punta a punta. Lo que permite el paralelismo son los contratos: con la API y los esquemas de telemetría acordados en el primer sprint, Captura y Plataforma avanzan contra mocks, e Inteligencia trabaja sobre un dataset sintético mientras llegan los datos reales.

| Frente | Alcance | Dueño inicial | Respaldo |
| --- | --- | --- | --- |
| F1 Captura | Agente RUM, sondas, escenarios, contexto de red | Federico | Romeo |
| F2 Plataforma | Ingesta, almacenamiento, API, Grafana, alertas, CI y despliegue | Santiago | Federico |
| F3 Inteligencia | Dataset, detección, User Health Score, LLM, evaluación | Romeo | Santiago |
| Producto y arquitectura | Priorización del backlog, revisión, destrabar | Emanuel (Product Owner) | Director del grupo |

La asignación sale de los perfiles que muestra el repo (telemetría, ML y datos, QA y CI) y es una propuesta: hay que validarla con cada persona y con su disponibilidad actual.

**Reglas de integración**

- Sprint de 2 semanas con un único objetivo compartido; cierra con una demo de punta a punta ante la dirección.
- Cada issue lleva una etiqueta de hito y una de frente. Un issue sin hito no entra al sprint.
- Contratos primero: la especificación OpenAPI y los esquemas de telemetría se aprueban en el sprint 1.
- Nadie aprueba su propio PR. Se exige 1 aprobación de alguien de otro frente (hoy el README dice 1 y `constraints.md` dice 2; se unifica en 1).
- Cada persona es dueña de un frente y respaldo de otro desde la primera semana.
- Máximo 2 issues en curso por persona. Daily asíncrono y una sincronización de 30 minutos los lunes.
- Un capitán de integración rotativo por sprint responde por que `main` siempre despliegue.
- Los entregables van en texto versionable (Markdown, PlantUML, Mermaid). Los PDF existentes se convierten antes de nuevos cambios.

## Cronograma de los tres pasantes hasta M1

Cada sprint tiene un trabajo principal por persona y un trabajo de apoyo en el frente de otra, en un ciclo fijo: Federico apoya a Santiago, Santiago apoya a Romeo y Romeo apoya a Federico. Así nadie espera a otro, todos tocan dos disciplinas por sprint y cada frente tiene un respaldo que conoce el código.

| Sprint | Federico (F1) | Romeo (F3) | Santiago (F2) | Entregable integrado |
| --- | --- | --- | --- | --- |
| S1 · 19–30 oct · capitán Santiago | **Principal:** esquemas de telemetría RUM y sondas. **Apoya a Santiago:** revisa OpenAPI v0.1. | **Principal:** ADR de base de datos y modelo desde el DER v1.2. **Apoya a Federico:** valida que los esquemas entren en el modelo. | **Principal:** OpenAPI v0.1, CI real y Docker corregido. **Apoya a Romeo:** ADR de licencias y SBOM. | Contratos aprobados, 3 ADRs, EDT cargado como issues y handover parcial de cada uno. |
| S2 · 2–13 nov · capitán Federico | **Principal:** agente RUM mínimo con TTFB y FCP. **Apoya a Santiago:** primera sonda HTTP a un sitio de prueba. | **Principal:** generador de datos sintéticos de las 5 métricas. **Apoya a Federico:** valida el payload RUM contra el esquema. | **Principal:** colector, ingesta y almacenamiento con tests. **Apoya a Romeo:** carga del dataset sintético a la base. | Cierre de M0 (13 nov) y primer dato de punta a punta visible en Grafana. |
| S3 · 16–27 nov · capitán Romeo | **Principal:** RUM completo con XHR, errores JS y rage clicks. **Apoya a Santiago:** nombres comunes de sitio y métrica para RUM y sondas. | **Principal:** etiquetas de «mala experiencia» y anomalías inyectadas. **Apoya a Federico:** umbrales de rage clicks y errores JS. | **Principal:** sondas TLS y DNS desde 2 redes. **Apoya a Romeo:** dashboards de las 5 métricas con las anomalías inyectadas. | Las 5 métricas RUM y las sondas visibles en Grafana; una anomalía inyectada se ve en el dashboard. |
| S4 · 30 nov–11 dic · capitán Santiago | **Principal:** agente RUM en el sitio piloto (7 dic). **Apoya a Santiago:** sondas al piloto. | **Principal:** regla estadística de anomalías (z-score). **Apoya a Federico:** contrasta datos reales del piloto con las etiquetas. | **Principal:** Alertmanager con mail y Telegram. **Apoya a Romeo:** conecta la regla de anomalías a las alertas. | Piloto midiendo y alerta recibida en Telegram ante una anomalía inyectada. |
| S5 · 14–18 dic · capitán Federico | Prueba de punta a punta en el piloto. | Informe de línea base de detección. | Medición de RAM con `docker stats` y carga básica. | M1 (18 dic): demo ante GIDAS, tests ≥ 70 % sobre código real, handovers al día. |

Con 10 horas semanales por pasante (`constraints.md`), cada sprint ofrece 20 horas por persona y 60 en total: unas 12 horas para el trabajo principal y 8 para el apoyo. S3 es el sprint más ajustado; si no cierra, se difieren XHR y rage clicks a M2 antes de mover M1. El Product Owner cierra el brief único y el EDT en issues durante S1 y S2.

**Rotación de dueños después del receso**

| Fase | F1 Captura | F2 Plataforma | F3 Inteligencia |
| --- | --- | --- | --- |
| B · nov–dic 2026 | Federico | Santiago | Romeo |
| C · mar–abr 2027 | Romeo | Federico | Santiago |
| D · abr–jun 2027 | Santiago | Romeo | Federico |

La rotación ocurre solo en los límites de fase y el dueño anterior pasa a respaldo, así cada persona lidera los tres frentes sin perder el conocimiento acumulado. Si la nueva cohorte llega en marzo, los dueños y respaldos se reparten entre más personas con la misma regla.

**Gantt individual de cada pasante**

Las tres barras de un mismo sprint corren a la vez: la sólida es el trabajo principal y la punteada es el apoyo al frente de otra persona, con el color del frente que se apoya.

&#91;embedded content: Gantt de Federico · S1 a S5\]

&#91;embedded content: Gantt de Romeo · S1 a S5\]

&#91;embedded content: Gantt de Santiago · S1 a S5\]

## Continuidad más allá de las pasantías

La continuidad se apoya en tres medidas: ningún frente depende de una sola persona, el handover es requisito de salida y una nueva cohorte se incorpora en marzo de 2027 a un producto que ya corre.

| Medida | Qué se hace | Cuándo |
| --- | --- | --- |
| Bus factor ≥ 2 | Cada frente tiene dueño y respaldo desde la semana 1. | Octubre 2026 |
| Handover obligatorio | Se exige la lista de `governance/continuity.md`: ADRs, un `handover-<usuario>.md` y una sesión de transferencia de al menos 1 hora. Hoy no existe ningún handover en el repo. | Antes de cada salida |
| Receso con sensores activos | En enero y febrero el piloto sigue generando datos; el equipo reducido hace mantenimiento y redacta. | Ene–feb 2027 |
| Nueva cohorte | Convocatoria en febrero y onboarding de 2 semanas con issues de «primer PR en 5 días». | Feb–mar 2027 |
| Mantenedor técnico | GIDAS designa a un docente o investigador como responsable estable del repo, que no rota con las pasantías. | Antes de M1 |
| Líneas de extensión | Diagnóstico de experiencia de usuario para sitios de terceros y, por separado, la oferta de seguridad (Lynis, CIS) que hoy está en el plan de Fase 1. | Desde M3 |

El calendario supone que el ciclo académico retoma en marzo y que hay receso en enero y febrero; conviene confirmarlo con la dirección, porque desplaza M2 y M3 si no es así.

## Gobernanza, riesgos y decisiones pendientes

La dirección puede juzgar el avance con seis indicadores que salen del tablero de issues, sin informes adicionales.

| Indicador | Meta |
| --- | --- |
| Demo de punta a punta al cierre de cada sprint | 100 % de los sprints |
| PRs con revisión cruzada | 100 % |
| Issues vinculados a un hito | 100 % de los que entran al sprint |
| Frentes con dueño y respaldo | 3 de 3 |
| Cumplimiento del objetivo de sprint | ≥ 80 % |
| Cobertura de tests sobre código real | ≥ 70 %, el umbral que ya fija el charter |

**Riesgos principales**

| Riesgo | Mitigación |
| --- | --- |
| Salida del equipo antes del handover | Handover como requisito de salida y mantenedor técnico estable. |
| El stack no entra en 2 GB de RAM (Grafana, Loki, Tempo, Prometheus, base de datos y LLM) | Medir el consumo real con `docker stats` en M1 y decidir qué servicios se difieren. |
| Alcance que crece hacia ML y LLM antes de tener datos | Los hitos M2 y M3 exigen dataset etiquetado como condición de entrada. |
| Sondas desde una sola red | Al menos dos puntos de origen en M1. |
| Licencia de la base de ASN y geolocalización | Verificarla antes de M2 y registrar la decisión en un ADR. |
| Calendario de receso distinto al supuesto | Confirmarlo con la dirección en esta semana. |

**Decisiones que necesito de la dirección**

1. Nombrar al Product Owner y al mantenedor técnico estable.
2. Confirmar qué pasantes continúan y cuántas personas tendrá la nueva cohorte.
3. Elegir el sitio piloto para M1.
4. Cerrar la base de datos: la minuta del 23-07 resolvió PostgreSQL, pero el brief y `openspec/config.yaml` dicen SQLite y no hay ADR.
5. Confirmar que ISP y hosting entran en M2 y no en el MVP inicial.
