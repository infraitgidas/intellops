# **Matriz de Trazabilidad Arquitectónica: Modelo de Datos vs. Contenedores**

**Proyecto:** IntellOps (MVP) — Laboratorio GIDAS

**Versión del DER:** V1.2 (PostgreSQL)

**Patrón Arquitectónico:** Monolito Modular Desacoplado (Docker Isolation)

## **1\. Fundamentación del Diseño**

En arquitecturas orientadas a microservicios o módulos aislados, es un error común confundir el almacenamiento físico con la propiedad lógica de los datos. Para garantizar la resiliencia del sistema en hardware de recursos escasos, IntellOps centraliza el estado en una única base de datos transaccional, pero **desacopla estrictamente los permisos y responsabilidades (CRUD) a nivel de contenedor**.

El objetivo de esta matriz es establecer límites claros para el equipo de desarrollo: ningún módulo debe ejecutar operaciones sobre tablas que no le corresponden, evitando así bloqueos de base de datos (deadlocks) y cuellos de botella entre la ingesta masiva de RUM y el procesamiento de Inteligencia Artificial.

## **2\. Capa de Persistencia: postgres-db**

**Responsabilidad Física:** Único punto de almacenamiento de estado (Stateful).

**Justificación de Diseño:** Se migró a PostgreSQL para aprovechar el manejo nativo de índices concurrentes, control de concurrencia multiversión (MVCC) y la flexibilidad del tipo de dato JSONB para la ingesta de metadatos variables, evitando migraciones de esquema constantes.

* **Entidades alojadas:** El 100% del esquema (Tablas: APPLICATION, LAB\_USER, USER\_FAVORITE\_METRIC, USER\_SESSION, RUM\_METRIC, JS\_EXCEPTION, ML\_MODEL, ANOMALY, ALERT).

## **3\. Módulo 1: intellops-core (API de Gestión e Ingesta)**

**Rol:** Motor principal de alta disponibilidad expuesto al cliente.

**Justificación de Diseño:** Debe ser ultraligero y asíncrono (FastAPI). Su única misión es no perder jamás un paquete de telemetría, incluso si el resto del sistema colapsa.

**Asignación para Desarrolladores:** Si el ticket (Issue) menciona alta de usuarios, validación de tokens o recepción de telemetría HTTP, el código pertenece exclusivamente a este contenedor.

| Entidad | Operaciones Permitidas | Justificación Lógica / Reglas de Negocio |
| :---- | :---- | :---- |
| APPLICATION | **CRUD Completo** | El Core gestiona el entorno multi-tenant. Crea y valida los api\_token que identifican de dónde provienen los datos. |
| LAB\_USER | **CRUD Completo** | Gestiona la autenticación, validación del password\_hash y generación de JWT para los investigadores. |
| USER\_FAVORITE\_METRIC | **CRUD Completo** | Maneja las preferencias de visualización del frontend (Dashboards). |
| USER\_SESSION | **Insert / Update** | Registra el inicio de la navegación de un usuario final y calcula la duración al cerrarse. |
| RUM\_METRIC | **Insert (Intensivo)** | Ingesta masiva de métricas (TTFB, FCP, etc.) en tiempo real. **Prohibido hacer operaciones de borrado (Delete)** desde este módulo. |
| JS\_EXCEPTION | **Insert** | Recibe y almacena los stack traces de errores de JavaScript. |

## **4\. Módulo 2: intellops-ai (Motor Matemático y LLM)**

**Rol:** Procesamiento en segundo plano (Background Worker).

**Justificación de Diseño:** El modelo *Isolation Forest* y la inferencia de *Llama 1B* son altamente demandantes de CPU y RAM. Se aísla en su propio contenedor para que, ante un desbordamiento de memoria (OOM Kill), Docker pueda reiniciar el proceso sin afectar la ingesta de telemetría del Core.

**Asignación para Desarrolladores:** Si el ticket implica algoritmos de *scikit-learn*, cálculos estadísticos, prompts generativos o inferencia en CPU, el código pertenece aquí.

| Entidad | Operaciones Permitidas | Justificación Lógica / Reglas de Negocio |
| :---- | :---- | :---- |
| ML\_MODEL | **CRUD Completo** | Gestiona el ciclo de vida, hiperparámetros y estados (*training*, *active*) de los modelos de IA. |
| RUM\_METRIC | **Read (Batch)** | Extrae ventanas de tiempo (ej. últimos 15 min) para analizar varianza. **Prohibido escribir o alterar** métricas originales. |
| ANOMALY | **Insert** | Si el modelo estadístico detecta una desviación del Z-Score, escribe el evento y el confidence\_score asociado. |
| ALERT | **Insert (Estado: Pending)** | Tras analizar la ANOMALY, el LLM traduce el evento a lenguaje natural y crea el registro base para que el módulo de comunicaciones lo despache. |

## **5\. Módulo 3: intellops-comms (Dispatcher de Notificaciones)**

**Rol:** Gestor de salida de red y APIs de terceros.

**Justificación de Diseño:** Las llamadas a APIs externas (como Telegram o servicios de Email) introducen latencia de red e inestabilidad (timeouts, errores 502). Separar esto evita que el hilo de ejecución de la Inteligencia Artificial se quede bloqueado esperando que Telegram responda.

**Asignación para Desarrolladores:** Si el ticket implica webhooks, retries de red o conexión con proveedores de mensajería, pertenece a este módulo.

| Entidad | Operaciones Permitidas | Justificación Lógica / Reglas de Negocio |
| :---- | :---- | :---- |
| ALERT | **Read / Update** | Aplica un patrón de *Polling* (o escucha de eventos). Busca alertas en estado Pending. Tras consumir la API de Telegram, actualiza el status a Sent o Failed y marca el sent\_at. |
| ANOMALY | **Read** | Lectura condicional si requiere enriquecer el mensaje con los valores numéricos (expected\_value, actual\_value). |

## **6\. Reglas de Implementación (EDT) para el Sprint**

Para garantizar la integridad de esta arquitectura, el equipo de desarrollo debe adherirse a los siguientes estándares durante la codificación:

1. **Aislamiento de Módulos (No cross-imports):** El código fuente de intellops-ai no puede importar funciones, clases o modelos ORM (SQLAlchemy) definidos en la carpeta de intellops-core, y viceversa. Si comparten esquema de base de datos, cada módulo declara únicamente los esquemas ORM de las tablas que le corresponden.  
2. **Resiliencia de Red:** El módulo intellops-comms debe implementar políticas de reintento (*Retry Pattern*) con retroceso exponencial (*Exponential Backoff*) para no saturar las APIs externas en caso de caída.  
3. **Manejo de Transacciones:** Las ingestas masivas hacia RUM\_METRIC en el Core deben implementarse mediante inserciones en bloque (*bulk inserts*) para minimizar los bloqueos de escritura (locks) en PostgreSQL.

