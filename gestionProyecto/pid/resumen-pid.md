# PID de Observabilidad — Síntesis para IntellOps

**Documento**: `pid/resumen-pid.md`
**Fuente primaria**: `PID/Nahuel - Proyecto.pdf` (formulario oficial, copia del 19/05/2026)
**Fecha**: 2026-09-11
**Autor**: Coordinación InfraIT — Emanuel Rodríguez

---

## 1. Identificación del PID

| Campo | Valor |
|---|---|
| **Título** | Observabilidad de Infraestructura IT en la era de Producción de Software asistido por IA: métodos y plataformas tecnológicas |
| **Código / Tipo** | PID Equipos Consolidados (PID TC) — Incentivado |
| **Convocatoria** | 2026 |
| **Programa** | Sistemas de Información e Informática |
| **Actividad** | Investigación Aplicada |
| **Facultad** | UTN Facultad Regional La Plata (UTN-FRLP) |
| **UCT** | GIDAS — Grupo de Investigación y Desarrollo Aplicado a Sistemas Informáticos y Computacionales |
| **Duración** | 3 años — 01/04/2027 al 31/03/2030 |

## 2. Equipo del PID

| Rol | Nombre | Categoría | Hs/sem |
|---|---|---|---|
| Director | Nahuel, Eduardo Leopoldo | B | 10 |
| Co-director | Rocca, Leandro | C | 10 |
| Investigador formado | Álvarez Ferrando, Agustín | D | 10 |
| Investigador formado | Peñalva, Mirta del Carmen | D | 10 |
| Investigador formado | Marchesini, Javier | D | 10 |
| Becario BINID | Cáceres Petkowicz, Rafael Hernán | G | 20 |
| Becario alumno | Bernal, Enmanuel | — | 10 |
| Correlatos | Zoe Quiroz (divulgación) · Romeo Monfroglio (PPS 2026) | — | — |

> **Nota de acoplamiento**: Emanuel Rodríguez y Romeo Monfroglio son mencionados en el histórico del PID
> como formados en InfraIT (ex Fierreros IT). El coordinador técnico del área es el Mg. Leandro Rocca (ciclo 2025+).

## 3. Resumen Técnico del PID

El PID parte del diagnóstico: el **monitoreo clásico** (CPU, memoria, servidor activo) ya no alcanza para
sistemas distribuidos y dinámicos. La **observabilidad** (correlación de métricas, logs y trazas) explica
*qué ocurre, por qué ocurre y cómo impacta en el negocio*. En la era de producción de software asistida
por IA, la infraestructura IT requiere métodos y plataformas de observabilidad **capacidad de deducir el
estado interno de sistemas complejos**.

**Objetivo de fondo**: diseñar y validar metodologías para detectar cuellos de botella, anticipar fallas
y optimizar recursos en entornos híbridos y distribuidos → **prototipo de plataforma tecnológica que
integre observabilidad avanzada con herramientas de IA**.

## 4. Objetivo General (formulario)

> Generar un prototipo de plataforma tecnológica que combine **observabilidad avanzada con Inteligencia
> Artificial** en infraestructuras IT híbridas y distribuidas, con el fin de optimizar la detección de
> cuellos de botella, anticipar fallas y mejorar la eficiencia, confiabilidad y agilidad en los procesos
> de producción de software.

## 5. Objetivos Específicos

| # | Objetivo específico |
|---|---|
| OE1 | Diseñar metodologías de recolección y correlación de métricas, logs y trazas en infraestructuras IT híbridas y distribuidas. |
| OE2 | Explorar técnicas de IA aplicadas a operaciones de TI (AIOps) para anticipar fallas y detectar anomalías. |
| OE3 | Integrar estándares abiertos de observabilidad en el marco del prototipo, favoreciendo trazabilidad y métricas unificadas en microservicios y contenedores. |
| OE4 | Evaluar el impacto potencial del prototipo en eficiencia, confiabilidad y agilidad de procesos de producción de software. |

## 6. Metodología del PID (etapas oficiales)

| Etapa | Período | Contenido |
|---|---|---|
| **E1 — Estado del arte y exploración** | 2027 | Relevamiento bibliográfico/técnico (observabilidad, AIOps, IA en software); estándares abiertos; diseño metodológico de experimentos en GIDAS; ensayos exploratorios; informes preliminares y artículos |
| **E2 — Experimentación y validación** | 2028 | Configuración y experimentación con IA aplicada a infra (AIOps, detección de anomalías, correlación); pruebas de integración m/l/t; validación de técnicas; evaluación de impacto en performance y UX; implementación inicial del prototipo |
| **E3 — Prototipado, escalabilidad y transferencia** | 2029 | Puesta a punto y escalabilidad; evaluación de impacto y documentación de metodologías; transferencia ampliada (empresas, pymes, organismos, UTN); artículos finales y propiedad intelectual; talleres de RRHH y cierre |

**Cronograma oficial (hitos clave del formulario)**:

| Actividad | Inicio | Fin |
|---|---|---|
| Estado del arte de soluciones (AIOps, infra IT con IA) | 04/2027 | 08/2027 |
| Exploración de herramientas (OTel, Prometheus, Grafana, ELK) | 07/2027 | 10/2027 |
| Diseño metodológico y planificación de experimentos | 09/2027 | 11/2027 |
| Ensayos exploratorios integrando métodos y herramientas en GIDAS | 10/2027 | 01/2028 |
| Experimentación con IA para infra GIDAS | 02/2028 | 05/2028 |
| Pruebas de integración y correlación m/l/t | 08/2028 | 11/2028 |
| Evaluación de impacto en performance y UX de infra GIDAS | 10/2028 | 12/2028 |
| Implementación inicial del prototipo (calidad de servicios IT) | 11/2028 | 02/2029 |
| Puesta a punto y escalabilidad del prototipo | 02/2029 | 05/2029 |
| Transferencia ampliada y validación con adoptantes | 07/2029 | 10/2029 |
| Cierre, talleres, informe final, PI | 11/2029 | 03/2030 |

## 7. Presupuesto


## 8. Vinculación con IntellOps (cómo leer este PID)

**IntellOps es la materialización de producto de este PID.** La relación es la siguiente:

| Etapa PID | Estado | Aporte de IntellOps (PPS 2026) |
|---|---|---|
| E1 (2027) | Adelantada | La investigación ya hecha (`docs/research/*`, brief-v2, papers) cubre el estado del arte |
| E2 (2028) | En curso de preparación | Detección de anomalías (Romeo), seguridad (Federico), QA/calidad (Santiago) son los experimentos de IntellOps |
| E3 (2029) | Futuro | El prototipo IntellOps evoluciona a la plataforma formal del PID |

**Implicancias**:
1. El objetivo de IntellOps (UX-céntrico) **complementa** el foco infra del PID: le da la dimensión de
   *experiencia de usuario* que el PID menciona como "impacto" pero no desarrolla como producto.
2. Las entregas de las PPS 2026 son **evidencia técnica publicable** que el PID usará en E2/E3.
3. La coherencia documento-papel es requisito: nada de lo que se escriba en IntellOps debe contradecir
   el marco del PID (de ahí el `equipo/analisis-pps-acoplamiento.md`).

## 9. Referencias del PID (bibliografía clave)

- [1] Brewer, Observability Engineering, O'Reilly, 2021.
- [3] García-García et al., "Observabilidad y monitorización en microservicios," RET vol. 15, 2023.
- [4] Rodríguez & Sánchez, "SRE y observabilidad...", Rev. Iberoamericana Ing. Soft., 2024.
- [5][6] CNCF, OpenTelemetry Standards & Practices, 2025.
- [7][8] Vilches Pávez (AIOps, 2022); Gupta (AIOps, Springer, 2021).
- [9] Gartner, AIOps and the Future of IT Operations, 2024.
- [10] Microsoft Research, LLMs in Software Engineering, 2025.
- [11] CABASE, Mapa de Infraestructura para la IA en Argentina, 2026.

---

*Documento de síntesis elaborado para la gestión del proyecto. La fuente oficial es el PDF en `PID/`.*