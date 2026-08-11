# Especificación Completa de Historias de Usuario - Proyecto IntellOps

**Fecha de emisión:** 22 de julio de 2026
**Destinatario:** Responsable del Proyecto / Comité de Aprobación de Backlog
**Estado del documento:** Listo para aprobación y estimación técnica (Ready for Development)

Este documento contiene el bloque completo de Historias de Usuario (HUs) del sistema de observabilidad y rendimiento APM IntellOps, reestructuradas, expandidas y corregidas conforme a los estándares ágiles más exigentes y las necesidades de arquitectura de software distribuidas.

## HU-001: Inicio de Sesión Institucional

Como Usuario del laboratorio,

Quiero iniciar sesión mediante mis credenciales básicas (correo institucional y contraseña)

Para acceder de forma segura al entorno de observabilidad de IntellOps sin fricciones de doble factor.

### Precondiciones:

- El usuario debe estar previamente registrado en el sistema.

### Flujo Principal:

1. El usuario navega a la interfaz de inicio de sesión de IntellOps.
2. El usuario introduce su dirección de correo electrónico y contraseña.
3. El sistema encripta la contraseña y valida las credenciales contra el almacén de identidades.
4. El sistema genera una sesión y un token de acceso seguro (JWT).
5. El usuario es redirigido al Dashboard General.

### Criterios de Aceptación:

- Si el correo o la contraseña son incorrectos, se debe mostrar un mensaje de error genérico: "Credenciales inválidas". No se debe especificar cuál campo falló para evitar minería de datos.
- La contraseña ingresada en el formulario debe enmascararse automáticamente en la interfaz visual.
- La sesión web activa debe expirar automáticamente tras 30 minutos continuos de inactividad del usuario, requiriendo una nueva autenticación.

### Poscondiciones:

El usuario obtiene un estado autenticado válido y un token de sesión activo.

## HU-002: Cierre de Sesión

Como usuario,

Quiero cerrar mi sesión,

Para proteger la información de mi cuenta.

### Precondiciones:

- El usuario debe encontrarse autenticado.

### Flujo Principal:

1. El usuario selecciona "Cerrar sesión".
2. El sistema invalida la sesión.
3. Se eliminan los datos temporales.
4. El usuario vuelve a la pantalla de inicio.

### Criterios de Aceptación:

- El sistema deberá finalizar la sesión activa.
- No deberá permitirse acceder nuevamente a recursos protegidos utilizando la sesión finalizada.
- El usuario deberá ser redirigido al inicio.
- La sesión también deberá finalizar por tiempo de inactividad configurado.

### Poscondiciones:

El usuario deja de estar autenticado.

## HU-03: Gestión de Perfil Simplificado

Como Usuario autenticado,

Quiero gestionar mis datos mínimos

Para personalizar mi visualización de laboratorio sin configuraciones complejas de cuenta.

### Precondiciones:

- El usuario debe poseer una sesión activa y válida en la plataforma.

### Flujo Principal:

1. El usuario accede a la sección de "Configuración de Perfil".
2. El sistema recupera e interactúa mostrando los valores actuales del usuario.
3. El usuario modifica los campos editables permitidos.
4. El usuario hace clic en "Guardar Cambios".
5. El sistema valida los datos, actualiza la base de datos y despliega una notificación de éxito.

### Criterios de Aceptación:

- El usuario solo tiene permitido modificar los campos: Nombre y Apellido, rol y mail.
- Los campos críticos como ID_Usuario asignado deben mostrarse como de solo lectura.
- El sistema debe desplegar un mensaje emergente (Toast) confirmando: "Perfil actualizado con éxito" tras persistir los datos de manera correcta.

### Poscondiciones:

Los datos del perfil se actualizan en caliente y se reflejan inmediatamente en la interfaz.

## HU-04: Consultar Aplicaciones

Como usuario,

Quiero visualizar todas mis aplicaciones registradas,

Para seleccionar cuál analizar.

### Criterios de Aceptación:

- El sistema deberá listar únicamente las aplicaciones del usuario autenticado.
- Deberá mostrar nombre y estado.
- Permitirá ordenar el listado.
- Permitirá realizar búsquedas por nombre.
- Permitirá acceder al detalle de cada aplicación.

### Poscondiciones:

El usuario selecciona una aplicación para trabajar.

## HU-05: Validar Instrumentación

Como usuario,

Quiero conocer si mi aplicación quedó correctamente instrumentada,

Para asegurarme de que se están enviando datos.

### Precondiciones:

- El usuario debe haber iniciado sesión y seleccionado una aplicación específica de su listado.

### Criterios de Aceptación:

- El sistema deberá verificar la recepción de telemetría.
- Deberá indicar si la configuración es válida.
- En caso de error, deberá informar la posible causa.
- El usuario podrá volver a ejecutar la validación.
- El estado deberá actualizarse automáticamente cuando se detecte nueva información.

### Poscondiciones:

El usuario conoce el estado de la instrumentación.

## HU-06: Recepción de Métricas

Como usuario,

Quiero que IntellOps almacena automáticamente las métricas recibidas,

Para analizarlas posteriormente.

### Precondiciones:

- La aplicación debe encontrarse instrumentada correctamente.

### Flujo Principal:

1. La aplicación envía métricas.
2. IntellOps recibe la información.
3. El sistema valida el formato.
4. Las métricas se almacenan.
5. Quedan disponibles para su visualización y análisis.

### Criterios de Aceptación:

- El sistema deberá recibir métricas provenientes de aplicaciones instrumentadas.
- Cada métrica deberá almacenarse junto con su fecha y hora de recepción.
- Las métricas inválidas deberán descartarse e informar el error correspondiente.
- La información deberá quedar disponible para el Dashboard y los módulos de análisis.
- El sistema deberá preservar la integridad de los datos almacenados.
- La recepción de nuevas métricas no deberá afectar la disponibilidad de la plataforma.

### Poscondiciones:

Las métricas quedan registradas para su posterior procesamiento.

## HU-07: Recepción e Ingesta de Logs de Telemetría

Como Desarrollador,

Quiero recibir y almacenar los logs enviados por aplicaciones instrumentadas mediante OpenTelemetry,

Para permitir su consulta y análisis dentro de la plataforma.

### Precondiciones:

- El servicio de origen de la aplicación debe estar operativo y apuntando al endpoint de ingesta de IntellOps.

### Criterios de Aceptación:

- El tamaño máximo permitido para cada solicitud será de 5 MB.
- Los logs válidos deberán almacenarse utilizando el backend de registros configurado (Loki o equivalente).
- Los logs deberán conservarse durante 14 días antes de su eliminación automática.
- El procesamiento podrá ejecutarse de forma asíncrona para evitar bloquear las peticiones del usuario.
- En caso de error durante el almacenamiento, el sistema registrará el evento para su posterior diagnóstico.

### Poscondiciones:

- Los registros de logs válidos son almacenados en el backend persistente con una retención de 15 días.

## HU-08: Recepción de Trazas

Como usuario,

Quiero que IntellOps almacene automáticamente las trazas distribuidas,

Para reconstruir el recorrido de las solicitudes realizadas por mi aplicación.

### Precondiciones:

- La aplicación debe estar instrumentada con OpenTelemetry.

### Flujo Principal:

1. La aplicación envía una traza.
2. IntellOps recibe la información.
3. El sistema valida la estructura.
4. La traza es almacenada.
5. Queda disponible para su consulta.

### Criterios de Aceptación:

- Cada traza deberá poseer un identificador único.
- El sistema deberá registrar la duración de la solicitud.
- Deberán almacenarse los servicios involucrados.
- Las trazas deberán relacionarse con la aplicación correspondiente.
- El sistema deberá permitir su posterior visualización.

### Poscondiciones:

Las trazas quedan almacenadas.

## HU-09: Dashboard de Métricas

Como Desarrollador / Investigador del laboratorio,

Quiero visualizar el comportamiento en tiempo real de las 5 métricas deterministas clave de la aplicación,

Para analizar la experiencia real del cliente y auditar las fallas del código de manera directa.

### Precondiciones:

- La aplicación seleccionada debe estar enviando telemetría compatible con el modelo de datos.

### Criterios de Aceptación:

- El panel frontend debe renderizar única y obligatoriamente las siguientes 5 métricas específicas cuyos datos crudos se extraen de la tabla RUM_METRIC:
  - TTFB (Time To First Byte)
  - FCP (First Contentful Paint)
  - XHR Latency (Latencia en llamadas de red / Fetch masivos)
  - Tasa de Excepciones JS (Errores en tiempo de ejecución del cliente)
  - Rage Clicks (Métrica de frustración basada en clicks repetitivos en un mismo elemento)
- El agente de recolección (SDK) del cliente debe capturar de forma transparente los errores no controlados de JavaScript e inyectarlos directamente en la tabla JS_EXCEPTION. El dashboard consumirá este conteo para calcular la Tasa de Excepciones JS.

## HU-10: Visualizar Métricas de Rendimiento

Como usuario,

Quiero consultar métricas de rendimiento,

Para identificar degradaciones en la aplicación.

### Criterios de Aceptación:

- El sistema deberá mostrar las métricas disponibles para la aplicación.
- Las métricas deberán representarse mediante gráficos e indicadores.
- El usuario podrá consultar valores históricos.
- El sistema permitirá filtrar la información por rango de fechas.
- Las métricas deberán actualizarse automáticamente cuando existan nuevos datos.

### Poscondiciones:

El usuario puede evaluar el rendimiento de su aplicación.

## HU-11: Consultar Detalle de una Métrica

Como usuario,

Quiero visualizar el detalle de una métrica,

Para comprender su comportamiento.

### Criterios de Aceptación:

- El sistema deberá mostrar el valor actual de la métrica.
- Deberá mostrar su evolución histórica.
- Deberá indicar la fecha y hora de la última actualización.
- El sistema deberá mostrar información descriptiva de la métrica.
- El usuario podrá regresar al Dashboard sin perder el contexto.

### Poscondiciones:

El usuario obtiene información detallada sobre la métrica seleccionada.

## HU-12: Consultar Logs

Como usuario,

Quiero visualizar los logs registrados,

Para detectar errores ocurridos durante la ejecución de mi aplicación.

### Precondiciones:

- Deben existir logs almacenados.

### Flujo Principal:

1. El usuario accede al módulo de logs.
2. El sistema consulta los registros.
3. Se muestran los resultados.

### Criterios de Aceptación:

- El sistema deberá mostrar fecha, hora, severidad, origen y descripción.
- Los registros deberán mostrarse ordenados cronológicamente.
- Solo se visualizarán logs pertenecientes a la aplicación seleccionada.
- El sistema deberá permitir acceder al detalle de cada registro.
- La consulta deberá responder en un tiempo adecuado.

### Poscondiciones:

El usuario obtiene acceso al historial de eventos.

## HU-13: Filtrar Logs

Como usuario,

Quiero filtrar los logs registrados,

Para encontrar eventos específicos.

### Criterios de Aceptación:

- El usuario podrá filtrar por fecha.
- El usuario podrá filtrar por severidad.
- El usuario podrá filtrar por texto.
- Los filtros podrán combinarse entre sí.
- El sistema deberá actualizar el listado inmediatamente después de aplicar un filtro.

### Poscondiciones:

El usuario obtiene únicamente los registros solicitados.

## HU-14: Consultar Trazas

Como usuario,

Quiero visualizar las trazas distribuidas,

Para analizar el recorrido completo de una solicitud.

### Precondiciones:

- Deben existir trazas registradas.

### Flujo Principal:

1. El usuario selecciona una aplicación.
2. Ingresa al módulo de trazas.
3. El sistema recupera la información.
4. Se muestran las trazas disponibles.

### Criterios de Aceptación:

- Cada traza deberá mostrar un identificador único.
- El sistema deberá mostrar la duración total de la solicitud.
- Deberán visualizarse todos los servicios involucrados.
- Las trazas deberán poder ordenarse por fecha o duración.
- El usuario podrá acceder al detalle de cualquier traza.

### Poscondiciones:

El usuario obtiene una visión completa de las solicitudes procesadas.

## HU-15: Consultar Detalle de una Traza

Como usuario,

Quiero visualizar el detalle de una traza,

Para identificar el componente que produjo un problema.

### Criterios de Aceptación:

- El sistema deberá mostrar cada uno de los spans que componen la traza.
- Deberá indicar el tiempo consumido por cada servicio.
- El sistema deberá identificar los errores ocurridos durante la ejecución.
- El usuario podrá visualizar la secuencia completa de llamadas entre servicios.
- La información deberá corresponder únicamente a la traza seleccionada.

### Poscondiciones:

El usuario puede identificar el origen de un problema de rendimiento o ejecución.

## HU-16: Obtener Predicciones

Como usuario,

Quiero visualizar predicciones de incidentes,

Para actuar preventivamente antes de que afecten a los usuarios finales.

### Precondiciones:

- Debe existir un análisis previamente ejecutado.

### Flujo Principal:

1. El usuario accede al módulo de predicciones.
2. El sistema consulta los resultados del análisis.
3. Se muestran las predicciones disponibles.

### Criterios de Aceptación:

- El sistema deberá mostrar el nivel de riesgo estimado.
- Cada predicción deberá indicar su probabilidad de ocurrencia.
- El sistema deberá mostrar las métricas utilizadas para generar la predicción.
- Las predicciones deberán estar asociadas a la aplicación seleccionada.
- El usuario podrá consultar el historial de predicciones.
- El sistema deberá indicar la fecha y hora del análisis realizado.

### Poscondiciones:

El usuario conoce los riesgos potenciales detectados.

## HU-17: Consultar Explicación de la IA

Como usuario,

Quiero conocer por qué la Inteligencia Artificial generó una determinada predicción,

Para comprender el análisis realizado y facilitar la toma de decisiones.

### Precondiciones:

- Debe existir una predicción disponible.

### Flujo Principal:

1. El usuario selecciona una predicción.
2. Solicita visualizar su explicación.
3. El sistema recupera la información.
4. Se presenta la justificación correspondiente.

### Criterios de Aceptación:

- El sistema deberá mostrar una explicación comprensible para el usuario.
- La explicación deberá indicar las métricas que influyeron en el resultado.
- Deberá presentarse el nivel de confianza de la predicción.
- La explicación deberá corresponder exclusivamente a la predicción seleccionada.
- El usuario podrá regresar fácilmente al listado de predicciones.

### Poscondiciones:

El usuario comprende la causa de la predicción generada.

## HU-18: Visualizar Recomendaciones

Como usuario,

Quiero consultar las recomendaciones generadas por IntellOps,

Para mejorar la calidad, el rendimiento y la experiencia de usuario de mi aplicación.

### Precondiciones:

- Debe existir un análisis inteligente ejecutado.

### Flujo Principal:

1. El usuario accede al módulo de recomendaciones.
2. El sistema recupera las recomendaciones disponibles.
3. Se muestran ordenadas por prioridad.

### Criterios de Aceptación:

- El sistema deberá mostrar una lista de recomendaciones para la aplicación seleccionada.
- Cada recomendación deberá incluir una descripción detallada.
- El sistema deberá indicar la prioridad (Alta, Media o Baja).
- Cada recomendación deberá incluir una justificación basada en el análisis realizado.
- Las recomendaciones deberán mostrarse ordenadas por prioridad de forma predeterminada.
- El usuario podrá acceder al detalle de cualquier recomendación.

### Poscondiciones:

El usuario dispone de acciones sugeridas para mejorar su aplicación.

## HU-19: Consultar Prioridad de una Recomendación

Como usuario,

Quiero conocer la prioridad de cada recomendación,

Para decidir cuáles implementar primero.

### Criterios de Aceptación:

- Cada recomendación deberá indicar claramente su prioridad.
- El sistema deberá explicar el criterio utilizado para asignar dicha prioridad.
- El usuario podrá ordenar las recomendaciones por prioridad.
- El nivel de prioridad deberá mantenerse consistente entre consultas.
- Las prioridades deberán actualizarse luego de cada nuevo análisis.

### Poscondiciones:

El usuario identifica fácilmente las recomendaciones más importantes.

## HU-20: Configuración de Canales y Sensibilidad de Alertas

Como Usuario de IntellOps,

Quiero configurar el nivel de tolerancia del motor de anomalías y vincular mis medios de contacto,

Para ser notificado únicamente de incidentes reales traducidos por la IA sin lidiar con falsos positivos por umbrales rígidos.

### Precondiciones:

- El usuario debe estar autenticado en la plataforma con una sesión activa.

### Criterios de Aceptación:

- El usuario seleccionara la configuración de la regla de un nivel de Sensibilidad mediante opciones cerradas: Alta, Media o Baja
- El formulario permitirá asociar de forma exclusiva los canales de despacho disponibles: Dirección de correo electrónico o telegram.

## HU-21: Visualizar Alertas

Como usuario,

Quiero consultar las alertas generadas,

Para detectar rápidamente problemas en mis aplicaciones.

### Precondiciones:

- El usuario debe estar autenticado en la plataforma con una sesión activa.

### Criterios de Aceptación:

- El sistema deberá mostrar únicamente las alertas correspondientes al usuario.
- Cada alerta deberá indicar fecha, severidad y descripción.
- El sistema deberá mostrar la métrica que originó la alerta.
- Las alertas deberán ordenarse por fecha de generación.
- El usuario podrá acceder al detalle de cada alerta.

### Poscondiciones:

El usuario visualiza las alertas activas e históricas.

## HU-22: Historial de Alertas

Como usuario,

Quiero consultar el historial de alertas ocurridas,

Para analizar incidentes registrados anteriormente.

### Precondiciones:

- Deben existir alertas registradas.

### Flujo Principal:

1. El usuario accede al historial.
2. El sistema recupera las alertas almacenadas.
3. Se presentan ordenadas cronológicamente.

### Criterios de Aceptación:

- El historial deberá mostrar fecha, severidad, aplicación y estado.
- El usuario podrá realizar búsquedas por aplicación.
- El usuario podrá filtrar por rango de fechas.
- El sistema permitirá consultar el detalle de cualquier alerta.
- El historial deberá conservar todas las alertas registradas.

### Poscondiciones:

El usuario dispone del historial completo de incidentes detectados.
