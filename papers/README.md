# Papers — IntellOps

> **Propósito**: Repositorio de artículos académicos del proyecto IntellOps.
> Cada paper tiene su propia carpeta con draft, figuras, referencias y estado de submission.

---

## Estado Actual

| Paper | Carpeta | Estado | Autores | Target | Plazo |
|-------|---------|--------|---------|--------|-------|
| Observabilidad UX-Céntrica para Entornos con Recursos Escasos | `divulgacion-intellops/` | 📝 **Borrador completo** | Rodriguez, Cavallero, Monfroglio, Montanari, Nahuel | RASI / Ciencia y Tecnología UTN | Julio 2026 |

---

## Estructura Estándar

Cada paper debe tener:

```
papers/<nombre-corto>/
├── README.md          ← Estado, autores, deadline, target journal
├── articulo.md        ← Borrador del artículo (formato markdown)
├── articulo.pdf       ← Versión compilada (cuando exista)
├── figures/           ← Figuras y diagramas
│   └── *.png / *.pdf
├── references.bib     ← Bibliografía en BibTeX
└── submission/        ← Pruebas de envío
    └── proof.pdf
```

---

## Cómo Contribuir

1. Elegir un paper del roadmap en `docs/divulgacion/articulos-revistas.md`
2. Crear carpeta en `papers/` siguiendo la estructura estándar
3. Escribir el borrador en Markdown
4. Solicitar revisión al coordinador antes de compilar/formatear
5. Una vez aprobado, compilar y enviar

---

*Más información sobre la estrategia de publicaciones en `docs/divulgacion/articulos-revistas.md`*
