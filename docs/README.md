# Documentación de IntellOps

Este directorio contiene la documentación técnica, científica y de divulgación del proyecto.

## Estructura

| Directorio | Propósito | Formato |
|------------|-----------|---------|
| `adr/` | Architecture Decision Records (formato Nygard) | `NNNN-titulo-breve.md` |
| `research/` | Notas científicas, hipótesis, metodología, papers | Markdown + LaTeX |
| `divulgation/` | Notas de divulgación para público general y extensión | Markdown |

## ADRs

Los Architecture Decision Records documentan decisiones técnicas significativas. Cada ADR:

- Sigue el formato [Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- Se numera secuencialmente: `0001-titulo.md`, `0002-titulo.md`, ...
- Tiene estado: `propuesto`, `aceptado`, `deprecado`, `supersedido`
- Se crea como parte del flujo SDD (fase de diseño)

### ADRs Activos

| # | Título | Estado | Fecha |
|---|--------|--------|-------|

*Los ADRs se listan aquí a medida que se crean.*

## Research

Las notas de investigación incluyen:

- Hipótesis y preguntas de investigación
- Metodología experimental
- Resultados preliminares
- Revisiones de literatura
- Borradores de papers

Ver `research/RESEARCH.md` para el índice de investigación activa.

## Divulgación

Contenido para público general:

- Explicaciones del proyecto para visitantes del laboratorio
- Material para extensión universitaria
- Posters y resúmenes para conferencias
- Contenido para redes sociales y blog

---

*La documentación es un artefacto vivo. Todo PR debe actualizar la documentación relevante.*
