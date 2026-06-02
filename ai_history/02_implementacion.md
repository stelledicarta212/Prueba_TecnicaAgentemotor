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
