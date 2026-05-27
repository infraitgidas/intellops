# Onboarding — IntellOps

Bienvenido al equipo IntellOps. Este documento te guía en los primeros pasos para que puedas contribuir al proyecto en menos de 30 minutos.

## Requisitos del Sistema

- **RAM**: ≥ 4GB (recomendado 8GB)
- **CPU**: Cualquier x86_64 o arm64
- **Disco**: ≥ 10GB libres
- **OS**: Linux (recomendado), macOS, WSL2 en Windows
- **GPU**: No necesaria (todo corre en CPU)

## Dependencias

### Esenciales

```bash
# Git
git --version  # >= 2.30

# Docker + Docker Compose
docker --version       # >= 24
docker compose version # >= 2.20

# Make
make --version  # >= 4.0
```

### Python (Backend + ML)

```bash
python --version   # >= 3.11
pip --version      # >= 24
```

Recomendado: usar `uv` para gestión de dependencias más rápida:

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Node.js (Agente RUM + Dashboard)

```bash
node --version  # >= 20 LTS
npm --version   # >= 10
```

## Setup en 5 Pasos

### 1. Clonar el Repositorio

```bash
git clone https://github.com/gidas/intellops.git
cd intellops
```

### 2. Configurar Entorno Virtual

```bash
# Con uv (recomendado)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Con pip estándar
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configurar Pre-commit Hooks

```bash
pre-commit install
```

### 4. Levantar el Entorno

```bash
make setup   # Construye imágenes, corre migraciones, carga datos de ejemplo
make up      # Levanta servicios con Docker Compose
```

Verificar que funciona:

```bash
curl http://localhost:8000/health
# → {"status": "ok", "version": "0.1.0"}
```

### 5. Correr los Tests

```bash
make test
# → Todos los tests pasan ✅
make test-cov
# → Coverage report
```

## Recursos de Aprendizaje

| Recurso | Descripción |
|---------|-------------|
| `TEAM_CHARTER.md` | Carta del equipo, valores, acuerdos |
| `openspec/config.yaml` | Configuración SDD del proyecto |
| `docs/brief-v2.md` | Brief técnico-científico completo |
| `docs/adr/` | Decisiones arquitectónicas registradas |
| `onboarding/` | Esta guía + documentos de soporte |
| `ml/experiments/` | Experimentos ML (MLflow) |

## Estructura del Proyecto

```
observabilidad/
├── openspec/         ← Artefactos SDD (changes, specs, config)
├── src/              ← Código fuente
│   ├── api/          ← FastAPI backend
│   ├── agent/        ← Agente RUM (JS/TS)
│   ├── dashboard/    ← React frontend
│   └── ml/           ← Modelos ML (serving)
├── ml/               ← Experimentos, datasets, entrenamiento
├── tests/            ← Suites de pruebas
├── docs/             ← Documentación técnica y científica
├── onboarding/       ← Guías de onboarding
└── governance/       ← SBOM, compliance, continuidad
```

## Próximos Pasos

1. Leé el [brief del proyecto](../docs/brief-v2.md) para entender el contexto completo.
2. Revisá los ADRs activos en `docs/adr/` para entender decisiones pasadas.
3. Identificá tu primer cambio siguiendo el [flujo SDD](../CONTRIBUTING.md#flujo-de-trabajo-sdd).
4. Creá un issue de tipo "change proposal" describiendo tu primer cambio.

## ¿Problemas?

- **Setup no funciona**: Abrí un issue con label `setup`
- **Duda técnica**: Buscá en `docs/adr/` o preguntá en un Discussion
- **Urgente**: Contactá al coordinador

---

*Tiempo estimado de onboarding: ≤ 30 minutos.*
*Si te tomó más, abrí un issue para mejorar esta guía.*
