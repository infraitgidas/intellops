# IntellOps en 5 minutos

## ¿Qué es IntellOps?

IntellOps es un **sistema de observabilidad predictiva** diseñado para funcionar en hardware modesto y presupuesto cero. Su objetivo es ayudar a equipos de IT a detectar anomalías en infraestructura tecnológica **antes de que afecten a los usuarios**.

## ¿Qué problema resuelve?

Hoy, las herramientas de monitoreo tradicionales:
- Reaccionan **después** de que algo falla
- Son **caras** (Datadog cuesta miles de dólares al año)
- Requieren **hardware potente** (GPU, mucha RAM)
- Generan **alertas falsas** que abruman a los operadores

IntellOps ataca estos problemas combinando:
- **ML liviano** (modelos que corren en CPU con < 2GB RAM)
- **IA local** (un asistente conversacional que funciona sin internet)
- **Costo cero** (todo open-source, Docker Compose, free-tier cloud)

## ¿Cómo funciona?

```
Sistema monitoreado → Agente OTel → Backend FastAPI → ML Engine → Dashboard
                                              ↓
                                        Asistente IA
                                        (RCA en lenguaje natural)
```

1. Un **agente liviano** recolecta métricas del sistema (CPU, RAM, latencia)
2. Un **backend** procesa y almacena las métricas
3. Un **motor ML** detecta anomalías automáticamente
4. Un **asistente IA** explica los problemas en lenguaje natural
5. Un **dashboard** muestra todo en tiempo real

## ¿Quién lo usa?

| Persona | ¿Qué gana? |
|---------|------------|
| **Estudiante SRE** | Auto-RCA en lenguaje natural, explicaciones contextuales |
| **Docente/Investigador** | Datos exportables para papers, experimentos reproducibles |
| **Admin de infraestructura** | Vista unificada de 20+ servicios en un solo panel |
| **Visitante del laboratorio** | Demo funcional sin acceso a sistemas internos |

## ¿Por qué es diferente?

| Característica | IntellOps | Datadog | Grafana Stack |
|----------------|-----------|---------|---------------|
| **Costo** | $0/mes | $500K+/año | $20K+/año |
| **RAM** | < 2GB | N/A (cloud) | > 8GB |
| **GPU** | No necesita | Cloud | No necesita |
| **IA local** | ✅ | ❌ | ❌ |
| **Código abierto** | ✅ Apache-2.0 | ❌ | ✅ AGPL |
| **Setup** | 30 min | Días | Horas |

## ¿Dónde funciona?

- **Servidores legacy** del laboratorio (4-8GB RAM)
- **Raspberry Pi** (edge computing)
- **Free-tier cloud** (AWS, GCP, Azure)
- **Laptop de un estudiante** (dev/demo)

## Impacto esperado

- **Académico**: Papers en IEEE/ACM, datasets públicos, datos para tesis
- **Social**: Herramienta gratuita para PYMEs y universidades públicas
- **Técnico**: Demostrar que la observabilidad avanzada no requiere grandes recursos

## ¿Querés saber más?

- Repositorio: [github.com/gidas/intellops](https://github.com/gidas/intellops)
- Laboratorio: GIDAS — UTN Facultad Regional La Plata
- Contacto: [coordinador del proyecto]

---

*IntellOps es un proyecto PI+D+i del grupo GIDAS (UTN FrLP).*
*Código y documentación abiertos bajo licencia Apache-2.0.*
