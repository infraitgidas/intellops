---
name: ML Experiment
about: Registrar un nuevo experimento de Machine Learning
title: "[ml] descripción del experimento"
labels: ml-experiment
assignees: ''
---

## Hipótesis

<!-- ¿Qué queremos probar? -->

## Método

<!-- Descripción del diseño experimental -->

## Dataset

- **Origen**: [sintético / real]
- **Tamaño estimado**: [número de muestras, features]
- **Split**: [train/val/test]

## Modelo

- **Arquitectura**: [Isolation Forest / LSTM / Prophet / etc.]
- **Hiperparámetros iniciales**: [lista]
- **Seed fijo**: [sí/no, cuál número]

## Métricas Target

| Métrica | Target | Baseline Actual |
|---------|--------|-----------------|
| F1 | — | — |
| Precision | — | — |
| Recall | — | — |
| MAPE | — | — |
| Latencia inferencia | — | — |

## Recursos Necesarios

- **RAM**: [GB]
- **CPU**: [cores]
- **GPU**: [sí/no, VRAM]
- **Tiempo estimado**: [horas]

## Reproducibilidad

- [ ] Seed fijo definido
- [ ] DVC pipeline configurada
- [ ] MLflow experiment configurado
- [ ] Requirements con versiones pinned

## Relación con Paper

<!-- ¿Este experimento alimenta alguna publicación planificada? -->
