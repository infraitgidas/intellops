# ADR 0001: Reemplazo de ELK Stack por Grafana + Loki + Prometheus

- **Estado**: Aceptado
- **Fecha**: 2026-05-27
- **Autores**: Emanuel Rodriguez
- **Decisión relacionada**: Solicitud del coordinador para alinear stack con estándares open-source y restricciones de licencia

## Contexto

El plan de trabajo del Módulo de Seguridad (Federico Cavallero) proponía originalmente una pipeline ELK Stack (Elasticsearch, Logstash, Kibana) para centralización y análisis de logs de seguridad. Sin embargo:

1. **Problema de licencias**: Elasticsearch a partir de la versión 7.10 cambió a licencia **SSPL (Server Side Public License)**, que es incompatible con nuestro objetivo de distribución comercial bajo Apache-2.0. SSPL está explícitamente prohibida en nuestra política de compliance (`governance/compliance.md`).

2. **Problema de recursos**: ELK Stack tiene un footprint elevado (> 4GB RAM recomendado para Elasticsearch solo), lo que contradice nuestro principio de "ingeniería de recursos escasos" (< 2GB RAM total del sistema).

3. **Stack fragmentado**: El brief del proyecto ya define Prometheus para métricas y Grafana como plataforma de visualización. Agregar Kibana significa duplicar la capa de dashboards.

4. **Oportunidad de unificación**: El stack Grafana + Loki + Prometheus (parte del ecosistema LGTM) es el estándar CNCF/de-facto para observabilidad, compatible con OpenTelemetry, y significativamente más liviano.

## Decisión

**Reemplazar ELK Stack por Grafana + Loki + Prometheus** como plataforma de logs, métricas y dashboards de seguridad.

| Componente ELK | Reemplazo | Justificación |
|----------------|-----------|---------------|
| Elasticsearch | **Loki** + Prometheus | Loki es un agregador de logs optimizado para recursos escasos, indexa metadatos en lugar de texto completo, diseñado como companion de Prometheus |
| Logstash | **Promtail** (agente Loki) + scraping nativo Prometheus | Promtail es el recolector oficial de Loki, liviano, configurado para descubrir y enviar logs |
| Kibana | **Grafana** | Grafana ya es nuestro estándar de dashboards, tiene datasource nativo para Loki y Prometheus, dashboards de seguridad listos |

### Stack Resultante para el Módulo de Seguridad

```
Servidores GIDAS → Promtail + Node Exporter → Loki (logs) + Prometheus (métricas)
                                                        ↓
                                                   Grafana
                                              (Dashboards de seguridad)
```

### Actualización de Dashboards de Seguridad (4 vistas)

Los dashboards que Cavallero tenía planificados en Kibana se implementan en Grafana:

1. **Autenticación**: Logs de auth.log vía Loki + métricas de intentos fallidos vía Prometheus
2. **Accesos no autorizados / Brute Force SSH**: Alertas basadas en rate de failed auth desde Prometheus + Loki
3. **Cambios en archivos críticos**: Métricas de auditd + logs de file integrity vía Loki
4. **Alertas automáticas**: Grafana Alerting con notificaciones webhook (Discord/Slack)

## Consecuencias

### Positivas

- **Licencias**: Loki y Grafana son AGPL-3.0, que aunque es restrictiva, se considera aceptable para componentes de infraestructura que no se modifican (se usan "as-is"). El equipo legal de Grafana Labs permite explícitamente su uso como servicio sin requerir distributing modificaciones.
- **Recursos**: Loki es significativamente más liviano que Elasticsearch. Con indexación de metadatos (no texto completo) y almacenamiento en objetos, el footprint se reduce drásticamente.
- **Stack unificado**: Un solo dashboard (Grafana) para métricas, logs y alertas. Los estudiantes de ML (Romeo) y QA (Santiago) también usan Grafana.
- **Estandar CNCF**: Prometheus es proyecto graduated de CNCF, Loki es incubating. Mejor adopción comunitaria y más recursos de aprendizaje.
- **Menor complejidad operativa**: Sin Elasticsearch cluster que mantener, sin Logstash pipelines complejas.

### Negativas / Trade-offs

- **Pérdida de funcionalidad text-search**: Loki no tiene el poder de búsqueda de texto completo de Elasticsearch. Para análisis forense profundo puede ser limitado.
- **Curva de aprendizaje**: El equipo (especialmente Cavallero) tenía experiencia planificada con ELK; ahora necesita aprender Loki/Promtail.
- **AGPL en infraestructura**: Aunque aceptamos AGPL para componentes no modificados, es una licencia más restrictiva que la Apache-2.0 del proyecto. El SBOM debe reflejar esto claramente.
- **Ecosistema de seguridad**: Kibana tiene dashboards de seguridad pre-built (SIEM). En Grafana hay que construirlos desde cero, aunque hay dashboards comunitarios.

### Riesgos

- **Rendimiento de Loki en logs de alta cardinalidad**: Loki puede degradarse con etiquetas de alta cardinalidad. Mitigación: diseñar esquema de etiquetas cuidadosamente y usar `volume` para diagnóstico.
- **AGPL FUD**: Algunos miembros del equipo pueden preocuparse por AGPL. Mitigación: documentar claramente que usamos los binarios sin modificar, lo cual está permitido.

## Alternativas Consideradas

### Alternativa 1: Mantener ELK con Elasticsearch versión pre-SSPL (7.10)

- **Descripción**: Usar Elasticsearch 7.10 (última versión Apache-2.0) con Logstash y Kibana de la misma época.
- **Razón de descarte**: Versiones antiguas sin soporte de seguridad, sin actualizaciones, vulnerabilidades conocidas. No es sostenible para un proyecto académico que busca publicar y transferir tecnología.

### Alternativa 2: Wazuh (fork de OSSEC + ELK)

- **Descripción**: Wazuh es una plataforma SIEM open-source que integra Elasticsearch fork + OSSEC para detección de intrusiones.
- **Razón de descarte**: Wazuh sigue usando Elasticsearch (fork, pero mismo footprint de recursos). Agrega complejidad SIEM que excede los requisitos del módulo de seguridad (que busca hardening + logs, no SIEM completo).

### Alternativa 3: Graylog

- **Descripción**: Plataforma de log management open-source con licencia SSPL desde 2020.
- **Razón de descarte**: Mismo problema de licencia SSPL que Elasticsearch. Además, no se integra tan naturalmente con Prometheus/Grafana como Loki.

### Alternativa 4: Netdata + Journald

- **Descripción**: Usar Netdata para métricas (ya está en el stack) + systemd-journald para logs con `journalctl` como interfaz.
- **Razón de descarte**: Netdata es excelente para métricas pero no reemplaza un sistema de log centralizado. No hay dashboards de seguridad consolidados.

## Recursos / Compatibilidad

- **Stack existente**: Grafana ya estaba contemplado como plataforma de visualización en el brief. Prometheus ya estaba en el stack de métricas. Este cambio fortalece la integración del stack.
- **Recursos**: Loki en modo `single-binary` + Prometheus + Grafana suman aproximadamente 500MB-1GB RAM, contra 2-4GB de Elasticsearch solo.
- **Licencias**: Loki (AGPL-3.0), Grafana (AGPL-3.0), Prometheus (Apache-2.0). Documentar en SBOM.

## Referencias

- [Loki Documentation](https://grafana.com/oss/loki/)
- [Promtail Documentation](https://grafana.com/docs/loki/latest/clients/promtail/)
- [Grafana License](https://grafana.com/licensing/)
- [Elastic License Change FAQ](https://www.elastic.co/licensing/elastic-license-faq)
- [ADR Template](0000-template.md)
