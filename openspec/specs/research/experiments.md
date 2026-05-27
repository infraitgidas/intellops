# Experiments Specification — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Metodología Experimental

Todos los experimentos en IntellOps siguen estos principios:

### 1.1. Reproducibilidad

1. **Seed fijo**: Cada experimento usa un seed aleatorio fijo. El seed se registra en los metadatos del experimento.
2. **Pipeline versionada**: DVC rastrea datasets, parámetros y pipelines completos.
3. **Entorno containerizado**: Docker Compose con versiones pinned de dependencias.
4. **MLflow tracking**: Cada run registra: parámetros, métricas, artefactos, código fuente, entorno.

### 1.2. Validación

1. **Split estratificado**: Train/val/test con estratificación para mantener distribución de clases.
2. **Cross-validation**: 5-fold cross-validation para modelos ML.
3. **Baseline**: Todo experimento compara contra un baseline (sin ML, o modelo más simple).
4. **Análisis estadístico**: Reportar media y desviación estándar de 5 corridas.

### 1.3. Registro

Cada experimento se registra en MLflow con:

```yaml
experiment:
  name: "EXP-XXX-description"
  seed: 42
  tags:
    hypothesis: "H1"
    responsible: "nombre"
    dataset: "swat-v2"
    model: "isolation-forest"
  params:
    contamination: 0.1
    n_estimators: 100
    max_samples: "auto"
  metrics:
    f1: 0.85
    precision: 0.88
    recall: 0.82
    latency_ms: 45
```

## 2. Catálogo de Experimentos

### 2.1. ML — Detección de Anomalías

| ID | Nombre | Hipótesis | Estado | Prioridad |
|----|--------|-----------|--------|-----------|
| EXP-001 | Isolation Forest baseline | H1 | Planificado | Alta |
| EXP-002 | Ensamble IF + Z-score | H1 | Planificado | Alta |
| EXP-003 | Ensamble completo + Seasonal Decomp | H1 | Planificado | Alta |
| EXP-004 | Benchmark latencia CPU limitado | H1 | Planificado | Media |

### 2.2. GenIA — Asistente Local

| ID | Nombre | Hipótesis | Estado | Prioridad |
|----|--------|-----------|--------|-----------|
| EXP-101 | RAG baseline sin fine-tuning | H2 | Planificado | Alta |
| EXP-102 | RAG con prompt engineering | H2 | Planificado | Alta |
| EXP-103 | Comparación Llama 3.2 vs TinyLlama | H2 | Planificado | Media |

### 2.3. Seguridad

| ID | Nombre | Hipótesis | Estado | Prioridad |
|----|--------|-----------|--------|-----------|
| EXP-201 | Auditoría baseline + hardening CIS | H3 | Planificado | Alta |
| EXP-202 | Pipeline GLP para logs de seguridad | H3 | Planificado | Alta |
| EXP-203 | Dashboards de seguridad (4 vistas) | H3 | Planificado | Alta |

### 2.4. QA/DevOps

| ID | Nombre | Hipótesis | Estado | Prioridad |
|----|--------|-----------|--------|-----------|
| EXP-301 | Pipeline CI/CD baseline | H4 | Planificado | Alta |
| EXP-302 | Contract testing con schemathesis | H4 | Planificado | Media |
| EXP-303 | Pipeline time vs coverage trade-off | H4 | Planificado | Baja |

## 3. Template de Experimentos

Cada experimento en `ml/experiments/EXP-XXX/` debe incluir:

```
ml/experiments/EXP-XXX-nombre/
├── README.md           ← Descripción, hipótesis, metodología
├── config.yaml         ← Parámetros del experimento
├── run.py              ← Script principal
├── requirements.txt    ← Dependencias específicas
├── results/
│   ├── metrics.json    ← Métricas del experimento
│   ├── plots/          ← Gráficos generados
│   └── model/          ← Artefactos del modelo
└── report.md           ← Reporte ejecutivo (generado post-ejecución)
```

## 4. Criterios de Aceptación

| Criterio | Estándar | Verificación |
|----------|----------|--------------|
| Reproducible | Seed fijo + DVC | `make reproduce EXP-XXX` |
| Documentado | README + reporte | Revisión por PO |
| Versionado | MLflow run completa | MLflow UI |
| Baseline | Comparación contra baseline | Reporte incluye Δ |
| Estadística | 5 corridas, media + std | `results/metrics.json` |

## 5. Referencias

- DVC Documentation. https://dvc.org/doc
- MLflow Documentation. https://mlflow.org/docs/latest/index.html
- Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*.
- RStudio Team (2020). Tidyverse: reproducibility best practices.
