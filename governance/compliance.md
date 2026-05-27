# Compliance — IntellOps

## Política de Licencias

IntellOps se distribuye bajo **Apache-2.0**. Todas las contribuciones deben aceptar este término.

### Criterios de Aceptación de Dependencias

1. **Licencia conocida**: Toda dependencia debe tener una licencia OSI-approved claramente identificada.
2. **Licencia compatible**: Preferir MIT, Apache-2.0, BSD, ISC. Evitar SSPL, AGPL.
3. **Atribución**: Mantener todos los archivos de licencia y atribuciones de dependencias.
4. **Transitividad**: Verificar licencias de dependencias transitivas (no solo directas).

### Dependencias Prohibidas

| Licencia | Riesgo | Alternativa |
|----------|--------|-------------|
| SSPL v1 | No compatible con distribución comercial | Apache-2.0 / MIT |
| AGPL v3 | Requiere distribuir código fuente si se usa como servicio | Apache-2.0 / MIT |
| WTFPL | Sin protección legal | MIT |

## Política de Seguridad

1. **SAST**: Escaneo estático en cada PR (bandit para Python).
2. **Secretos**: Prohibido commitear tokens, claves o credenciales. Usar `.env` + `.env.example`.
3. **Dependencias**: `pip-audit` o `safety` en CI para vulnerabilidades conocidas.
4. **Hardening**: Seguir CIS Benchmark Level 1 para servidores de producción.

## Estándares Aplicables

- **ISO/IEC 25010**: Atributos de calidad del software
- **ISO/IEC 12207**: Procesos de ciclo de vida del software
- **IEEE 829**: Documentación de pruebas
- **FAIR Principles**: Datos académicos (Findable, Accessible, Interoperable, Reusable)
- **CARE Principles**: Datos de personas (Collective Benefit, Authority, Responsibility, Ethics)
- **OWASP Top 10**: Seguridad en aplicaciones web
- **SLSA**: Supply chain security

## Política de Datos

1. **Datos sintéticos**: Preferir datasets sintéticos para desarrollo y CI.
2. **Datos reales**: Solo con consentimiento informado y anonimización previa.
3. **Retención**: Política configurable, default 90 días para métricas.
4. **Exportación**: Todos los datos exportables en formatos abiertos (CSV, Parquet, JSON).
