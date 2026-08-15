# **Justificación Arquitectónica: De un Entorno de Recursos Escasos hacia un Modelo SaaS Escalable**

**Proyecto:** IntellOps (Observabilidad Predictiva UX-Céntrica)

**Área:** Grupo de I\&D Aplicado a Sistemas informáticos y computacionales (GIDAS) \- UTN FRLP

**Autores:** Equipo de Infraestructura IT (InfraIT)

## **1\. Introducción y Planteamiento del Problema**

El desarrollo de plataformas de observabilidad predictiva (AIOps) se enfrenta a un dilema arquitectónico fundamental cuando opera bajo la premisa de la ingeniería de recursos escasos. La ingesta de telemetría (Real User Monitoring) es un proceso caracterizado por la alta concurrencia y la necesidad de latencias mínimas. Por el contrario, la ejecución de modelos de Inteligencia Artificial —tales como la inferencia matemática en *Isolation Forest* y la generación de texto mediante Modelos de Lenguaje Grandes (LLMs) como *Llama 3.2 1B*— representa una carga computacional asimétrica, propensa a consumir un alto porcentaje de los recursos de CPU y memoria RAM disponibles.

Si ambos dominios (ingesta y procesamiento inteligente) coexistieran bajo un paradigma de monolito tradicional fuertemente acoplado, un pico de demanda en el motor de Inteligencia Artificial podría agotar la memoria del servidor. Esto resultaría en la caída total del sistema, bloqueando la recepción de nueva telemetría y dejando a la infraestructura 'ciega'.

El presente documento justifica la adopción de una arquitectura de **Monolito Modular aislado por contenedores**, respaldada por un motor relacional robusto (PostgreSQL) desde el día cero, garantizando la alta disponibilidad del núcleo de ingesta y trazando un camino directo hacia un modelo comercial de *Software as a Service* (SaaS).

## **2\. Diseño Arquitectónico Propuesto**

Para mitigar los riesgos de colapso en el hardware institucional (e.g., servidor Lenovo ThinkServer SR530), se descarta el uso de microservicios distribuidos a través de la red pública debido a la penalización en latencia. En su lugar, se adopta un entorno orquestado mediante Docker Compose, dividiendo las cargas de trabajo en contenedores lógicamente aislados sobre una misma red privada interna (Bridge Network):

### **2.1. Contenedor 1: El Núcleo Inmutable (intellops-core)**

Aloja el motor de ingesta desarrollado en FastAPI. Su única responsabilidad es recibir el tráfico asíncrono de los agentes RUM, autenticar los orígenes (mediante el token de la entidad APPLICATION), y persistir los eventos masivos.

* **Restricción de Recursos:** Confinado a un uso máximo de \~250 MB de RAM.  
* **Justificación:** Al no realizar cálculos matemáticos pesados, garantiza que el sistema siempre responda con un estado HTTP 200 al navegador del cliente, incluso bajo estrés, asegurando cero pérdida de paquetes.

### **2.2. Contenedor 2: El Motor Analítico Aislado (intellops-ai-engine)**

Ejecuta el pipeline de Machine Learning e Inteligencia Artificial Generativa.

* **Restricción de Recursos:** Límite estricto de memoria (ej. 1000 MB).  
* **Justificación:** Si el modelo Llama 1B local experimenta un desbordamiento de memoria (OOM \- *Out Of Memory*), Docker reiniciará únicamente este contenedor. El núcleo de ingesta (intellops-core) permanecerá inalterado.

### **2.3. Contenedor 3: Base de Datos Relacional (intellops-db \- PostgreSQL)**

Se adopta PostgreSQL como fuente de verdad desde la fase MVP, descartando bases livianas como SQLite.

* **Justificación:** El Modelo de Datos de IntellOps depende críticamente de campos JSONB (para las propiedades dinámicas en RUM\_METRIC.metadata y ML\_MODEL.hyperparameters). PostgreSQL ofrece indexación y búsqueda nativa de alto rendimiento sobre JSONB. Aún más crítico, su Control de Concurrencia Multiversión (MVCC) permite que el *Core* inserte miles de métricas por segundo sin aplicar bloqueos de escritura (locks) al motor de IA que realiza consultas analíticas de lectura simultáneas.

### **2.4. Contenedor 4: Despachador de Alertas (intellops-comms)**

Microproceso liviano encargado de escuchar asíncronamente las anomalías y despachar los mensajes generados por la IA a las APIs de Telegram, WhatsApp o Email.

## **3\. Protocolos de Comunicación Inter-Contenedor**

El aislamiento exige una estrategia de comunicación eficiente. La red puente de Docker (Bridge Network) actúa como frontera de seguridad; únicamente el contenedor intellops-core expone puertos al mundo exterior (80/443). La comunicación interna fluye de la siguiente manera:

1. **Flujo de Ingesta (Internet \-\> Core \-\> DB):** El agente RUM envía métricas vía HTTP/REST al contenedor intellops-core. Este, utilizando un *Connection Pool* asíncrono (ej. SQLAlchemy \+ asyncpg), vuelca los datos masivamente a PostgreSQL.  
2. **Flujo de Análisis (AI Engine \<-\> DB):** Para mantener un desacoplamiento estricto, el contenedor de IA no recibe tráfico web. Opera como un *Background Worker* que consulta a PostgreSQL (o a una API interna y privada expuesta por el Core) requiriendo únicamente las "ventanas de tiempo" de métricas recientes no analizadas.  
3. **Flujo de Detección y Traducción:** Tras calcular el Z-Score matemático y detectar una desviación, el ai-engine invoca localmente a Llama 1B, genera el reporte en lenguaje natural y persiste la anomalía directamente en las tablas ANOMALY y ALERT.  
4. **Flujo de Notificación (Comms \-\> APIs Externas):** El contenedor de comunicaciones hace *polling* ligero (o usa notificaciones nativas de Postgres como LISTEN/NOTIFY) sobre la tabla ALERT y realiza las llamadas HTTP de salida hacia los servidores de Telegram.

## **4\. Pasos Críticos y Consideraciones de Implementación**

Para asegurar la viabilidad técnica y evitar cuellos de botella durante el Sprint 0 y el posterior desarrollo, el equipo deberá observar las siguientes directivas críticas:

1. **Gestión del Pool de Conexiones (PgBouncer/SQLAlchemy):** Al usar PostgreSQL en un entorno de alta concurrencia (como es el caso del tráfico RUM), el intellops-core debe limitar el número de conexiones simultáneas. Se requerirá configurar un *Pool Size* adecuado (ej. pool\_size=20, max\_overflow=10) para evitar agotar la memoria del contenedor de base de datos.  
2. **Límites Físicos en el Orquestador (Cgroups):** En el archivo docker-compose.yml, es imperativo utilizar la directiva deploy.resources.limits en el contenedor ai-engine. Si no se limita la memoria a nivel del kernel de Linux (cgroups), el modelo LLM podría consumir toda la RAM del nodo anfitrión, provocando un colapso de todo el servidor Lenovo del laboratorio.  
3. **Volúmenes Persistentes para Pesos de IA (.gguf):** El peso de los modelos fundacionales cuantizados (archivos .gguf de Llama 1B) oscila entre 1 GB y 2 GB. Estos archivos deben residir obligatoriamente en un volumen montado de Docker (volumes), para evitar que el contenedor los descargue repetidamente de la red en cada reinicio.  
4. **Gestión de Secretos:** Variables sensibles introducidas en el nuevo esquema DER, tales como credenciales de PostgreSQL, *Tokens* de APIs (Telegram) y *Salts* para el password\_hash de los usuarios, jamás deben ser versionadas en código duro. Deben ser inyectadas en tiempo de ejecución mediante archivos .env declarados en el .gitignore.

## **5\. Evolución al Modelo SaaS (Conclusiones)**

La virtud primordial de este diseño arquitectónico radica en que no constituye un prototipo descartable, sino una base de grado empresarial (*Enterprise-grade*) directamente escalable hacia un modelo comercial de *Software as a Service* (SaaS).

Al haber incorporado la entidad APPLICATION para soporte Multi-Tenancy y al haber elegido PostgreSQL desde el primer día, la transición a un servicio alojado en la nube será un proceso de expansión infraestructural y no de reescritura de código:

* **Orquestación Cloud-Native:** En un entorno de producción masiva, el docker-compose.yml será reemplazado por manifiestos de Kubernetes (K8s), permitiendo un *Auto-Escalado Horizontal (HPA)* del contenedor intellops-core ante picos de tráfico de los clientes.  
* **Persistencia Orientada a Big Data:** PostgreSQL actuará como un pilar fundamental. En la fase de escalabilidad masiva, solo será necesario instalarle la extensión **TimescaleDB**. Esto convertirá de forma transparente la tabla RUM\_METRIC en una hypertabla particionada, acelerando drásticamente el análisis de series temporales de millones de registros sin cambiar el motor relacional base.  
* **Mensajería Distribuida:** La comunicación entre el motor de IA y el despachador de alertas podrá evolucionar hacia un bus de mensajes dedicado (RabbitMQ o Apache Kafka), garantizando el procesamiento en tiempo real a escala industrial.

En conclusión, la adopción de PostgreSQL y la segmentación modular en contenedores aíslan la inteligencia artificial de las tareas críticas de ingesta, protegiendo los recursos limitados del laboratorio actual, mientras que al mismo tiempo sientan cimientos tecnológicos definitivos para su inminente comercialización como plataforma SaaS.