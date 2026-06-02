## Fecha

2026-06-02

## Agente responsable

Backend - Codex CLI

## Objetivo

Disenar e implementar `src/schema.sql` como fuente de verdad SQLite para clientes, asesores, polizas e intentos de contacto, respetando el alcance documentado y la regla de negocio de renovaciones.

## Archivos modificados

- `src/schema.sql`
- `ai_history/02_implementacion.md`

## Cambios realizados

- Se crearon las tablas `advisors`, `clients`, `policies` y `contact_attempts`.
- Se definieron claves primarias autoincrementales y relaciones mediante claves foraneas.
- Se agregaron restricciones basicas de integridad para canales de contacto, estado de renovacion y fechas.
- Se agregaron indices para consultas por asesor, cliente, poliza, vencimiento y estado de renovacion.
- Se valido el archivo con SQLite en memoria usando el modulo `sqlite3` de Python mediante `py`.

## Endpoints creados o modificados

No aplica. En esta tarea no se implemento codigo Flask ni endpoints.

## Formato de request

No aplica. No se crearon endpoints ni contratos HTTP en esta tarea.

## Formato de response

No aplica. No se crearon endpoints ni contratos HTTP en esta tarea.

## Cambios en base de datos

- `advisors`: almacena el asesor responsable de la cartera.
- `clients`: almacena clientes y los relaciona con `advisors`.
- `policies`: almacena polizas, tipo de seguro, aseguradora, fecha de vencimiento y estado de renovacion.
- `contact_attempts`: almacena llamadas, correos y mensajes asociados a una poliza, cliente y asesor.
- `policies.renewal_status` permite distinguir polizas pendientes de gestion frente a polizas renovadas.
- `policies.renewed_at` queda obligatorio cuando la poliza esta en estado `renewed`.

## Decisiones tomadas

- La prioridad operativa no se almacena como columna porque debe calcularse en backend a partir de `expiration_date` y `renewal_status`.
- Se agrego `renewal_status` con valores `pending` y `renewed` para representar la regla de negocio donde una poliza renovada no requiere gestion.
- Se mantuvo SQLite como fuente de verdad: toda informacion critica queda persistida en tablas relacionales.
- Se usaron `ON DELETE RESTRICT` para evitar borrar registros con historial asociado.

## Riesgos identificados

- `docs/03_modelo_datos.md` y `docs/04_clasificacion_prioridades.md` estaban vacios al momento de la revision; el esquema se baso en `spec.md` como fuente superior.
- El CLI `sqlite3` no esta instalado en el entorno; la validacion se hizo con el modulo SQLite de Python usando `py`.

## Pendientes para Frontend

- No consumir datos simulados como fuente de verdad.
- Esperar a que el backend implemente `GET /api/dashboard` para recibir polizas ya clasificadas.
- Considerar `renewal_status = renewed` como poliza sin gestion pendiente cuando el endpoint lo exponga.

## Pendientes generales

- Implementar `seed.sql` con datos de prueba coherentes.
- Implementar `db.py`.
- Implementar los endpoints definidos en `spec.md`.
- Implementar tests de clasificacion y renovacion.

## Fecha

2026-06-02

## Agente responsable

Backend - Codex CLI

## Objetivo

Implementar `src/seed.sql` con datos de prueba realistas que permitan validar todas las reglas de negocio de clasificacion de polizas y renovaciones.

## Archivos modificados

- `src/seed.sql`
- `ai_history/02_implementacion.md`

## Cambios realizados

- Se creo un seed idempotente para poblar la base SQLite desde cero.
- Se inserto 1 asesor de prueba.
- Se insertaron 8 clientes asociados al asesor.
- Se insertaron 8 polizas, una por cliente.
- Se distribuyeron las polizas en cuatro grupos operativos: proxima a vencer, ventana critica, nueva contratacion y renovada.
- Se validaron los datos cargando `src/schema.sql` y `src/seed.sql` en SQLite en memoria.

## Endpoints creados o modificados

No aplica. En esta tarea no se implemento codigo Flask ni endpoints.

## Formato de request

No aplica. No se crearon endpoints ni contratos HTTP en esta tarea.

## Formato de response

No aplica. No se crearon endpoints ni contratos HTTP en esta tarea.

## Cambios en base de datos

- `advisors`: 1 registro de prueba para Maria Gonzalez.
- `clients`: 8 clientes realistas asociados al asesor.
- `policies`: 8 polizas con fechas relativas a `date('now')`.
- Distribucion de polizas:
  - 2 proximas a vencer: vencen dentro de los proximos 30 dias.
  - 2 en ventana critica: vencieron entre 1 y 30 dias atras.
  - 2 como nueva contratacion: vencieron hace mas de 30 dias.
  - 2 renovadas: tienen `renewal_status = 'renewed'` y `renewed_at` informado.

## Decisiones tomadas

- Se usaron fechas relativas de SQLite para que el seed siga siendo util sin importar el dia de ejecucion.
- Se mantuvo una poliza por cliente para facilitar pruebas manuales y lectura del dashboard.
- No se insertaron `contact_attempts` porque la tarea pidio especificamente asesor, clientes y polizas.
- Las polizas renovadas usan fecha de vencimiento futura y `renewed_at` no nulo para cumplir las restricciones del schema.

## Riesgos identificados

- El seed borra datos existentes antes de insertar los registros de prueba; debe usarse solo en entornos de desarrollo o pruebas.
- Las categorias se validan correctamente siempre que la logica de backend respete `expiration_date` y excluya `renewal_status = 'renewed'` de la gestion pendiente.

## Pendientes para Frontend

- Usar estos datos como base de visualizacion cuando el backend exponga `GET /api/dashboard`.
- Mostrar las categorias provenientes del backend, no recalcularlas en JavaScript.

## Pendientes generales

- Implementar `db.py`.
- Implementar los endpoints definidos en `spec.md`.
- Implementar tests automatizados para clasificacion y renovacion.
