# Benchmarking Specification — IntellOps

- **Versión**: 1.0
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez, Equipo InfraIT GIDAS

## 1. Propósito

Establecer la metodología, métricas y criterios para el benchmarking de componentes del sistema IntellOps, tanto contra alternativas del mercado como contra líneas base internas.

## 2. Dimensiones de Benchmarking

### 2.1. Benchmarking de Plataformas de Observabilidad

**Objetivo**: Comparar IntellOps contra soluciones existentes para validar el posicionamiento en el nicho identificado.

| Dimensión | Métrica | IntellOps (target) | Grafana Stack | SigNoz | Netdata |
|-----------|---------|--------------------|---------------|--------|---------|
| Footprint RAM (idle) | MB | < 500 | ~800-1200 | ~1000-2000 | ~150 |
| Footprint RAM (full) | MB | < 2000 | ~4000+ | ~4000+ | ~300 |
| Tiempo de setup | minutos | < 30 | 30-60 | 60-120 | < 5 |
| Throughput ingesta | métricas/seg | > 1000 | > 10000 | > 5000 | > 10000 |
| Latencia detección anomalías | segundos | < 5 | N/A (plugin) | N/A | < 1 |
| GenIA local | Sí/No | Sí (Llama 3.2 1B) | No | No | No |
| Costo mensual | USD | $0 | $20K+ (cloud) | $30K+ (cloud) | $0 (self) |
| Licencia | — | Apache-2.0 | AGPL-3.0 / Apache | MIT | GPL-3.0 |

### 2.2. Benchmarking de Modelos ML

**Objetivo**: Evaluar y seleccionar modelos de detección de anomalías para el pipeline ML.

#### 2.2.1. Detección de Anomalías

| Modelo | Precisión (target) | Recall (target) | F1 (target) | Latencia (target) | RAM (target) |
|--------|-------------------|-----------------|-------------|-------------------|--------------|
| Isolation Forest | > 0.85 | > 0.75 | > 0.80 | < 100ms | < 50MB |
| Z-score dinámico | > 0.70 | > 0.65 | > 0.67 | < 10ms | < 5MB |
| Seasonal Decomposition | > 0.75 | > 0.70 | > 0.72 | < 50ms | < 20MB |
| LSTM (extensión futura) | > 0.90 | > 0.85 | > 0.87 | < 500ms | > 500MB |

**Criterios de selección**:

1. Si Isolation Forest cumple F1 > 0.80 en validación → seleccionado como modelo principal.
2. Si no cumple → ensamble con Z-score dinámico + reglas de threshold.
3. LSTM como extensión futura cuando recursos lo permitan (GPU > 6GB VRAM).

#### 2.2.2. Modelos de Lenguaje (LLM) para GenIA

| Modelo | Parámetros | Cuantización | RAM | Velocidad (tok/s) | Precisión factual (target) |
|--------|-----------|--------------|-----|-------------------|---------------------------|
| Llama 3.2 1B | 1B | Q4_K_M GGUF | ~600MB | 5-10 tok/s | > 80% |
| Gemma 2 2B | 2B | Q4_K_M GGUF | ~1.2GB | 3-5 tok/s | > 85% |
| Phi-3 Mini 3.8B | 3.8B | Q4_K_M GGUF | ~2.5GB | 2-3 tok/s | > 90% |
| TinyLlama 1.1B | 1.1B | Q4_K_M GGUF | ~700MB | 6-12 tok/s | > 75% |

**Criterios de selección**:

1. Priorizar Llama 3.2 1B por mejor balance velocidad/precisión en < 1GB RAM.
2. TinyLlama como alternativa si se necesita mayor velocidad.
3. Phi-3 como upgrade si los recursos lo permiten (> 2GB RAM disponibles).

### 2.3. Benchmarking de Bases de Datos para Métricas

| Sistema | Tipo | RAM mínima | Throughput | Consulta (< 1s) | Compresión | Licencia |
|---------|------|-----------|------------|-----------------|------------|----------|
| SQLite + time-index | Embedded | < 10MB | ~5K ops/s | < 10K rows | Baja | Public Domain |
| TimescaleDB (PG) | Relacional + time-series | ~512MB | ~50K ops/s | < 1M rows | Alta (x10) | Apache-2.0/Timescale |
| Prometheus | TSDB | ~256MB | ~1M samples/s | Nativo | Media | Apache-2.0 |
| VictoriaMetrics | TSDB | ~256MB | ~1M samples/s | Nativo | Alta (x20) | Apache-2.0 |

**Estrategia**: Comenzar con SQLite para MVP-0 (footprint mínimo). Migrar a TimescaleDB o Prometheus si el volumen lo requiere. Diseño migrable desde el inicio.

## 3. Metodología de Benchmarking

### 3.1. Principios

1. **Reproducibilidad**: Todos los benchmarks se ejecutan con seeds fijos, scripts versionados, y entornos containerizados.
2. **Aislamiento**: Cada benchmark se ejecuta en un entorno limpio (nuevo contenedor).
3. **Múltiples corridas**: Cada benchmark se ejecuta 5 veces, se reporta media y desviación estándar.
4. **Condiciones realistas**: Los benchmarks simulan condiciones del laboratorio GIDAS (CPU 2-4 cores, RAM 4-8GB, sin GPU).

### 3.2. Herramientas

| Herramienta | Propósito |
|-------------|-----------|
| k6 | Pruebas de carga para APIs de ingesta |
| Locust | Pruebas de carga distribuidas |
| `time` + `perf` | Medición de latencia y uso de CPU |
| `docker stats` | Monitoreo de recursos (RAM, CPU, disco) |
| MLflow + `mlflow.evaluate` | Evaluación de modelos ML |
| `prometheus-benchmark` | Benchmarking de almacenamiento de métricas |

### 3.3. Datasets de Benchmark

| Dataset | Tipo | Tamaño | Uso | Origen |
|---------|------|--------|-----|--------|
| GIDAS-Synth-Metrics-2026 | Métricas sintéticas | 1M filas | Benchmark de ingesta y ML | Generado sintéticamente |
| GIDAS-Real-Logs-2026 (anon) | Logs de seguridad anonimizados | 100K filas | Benchmark de pipeline de logs | Laboratorio GIDAS |
| SWaT (Secure Water Treatment) | Dataset público de anomalías | ~500K filas | Validación de detección ML | iTrust Lab |
| Yahoo S5 | Anomalías en series temporales | ~300K filas | Benchmark académico ML | Yahoo Research |

## 4. Reporte de Resultados

Cada benchmark produce un reporte en `openspec/changes/archive/<benchmark-date>/benchmark-report.md` con:

- **Resumen ejecutivo**: Resultados principales y conclusiones.
- **Metodología**: Parámetros, entorno, herramientas.
- **Resultados**: Tablas comparativas, gráficos (Mermaid).
- **Análisis**: Interpretación de resultados, factores que afectan el rendimiento.
- **Recomendaciones**: Acciones basadas en los resultados.
- **Reproducibilidad**: Comandos exactos, seeds, versiones.
