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

## Fecha

2026-06-02

## Agente responsable

Backend - Codex CLI

## Objetivo

Implementar `src/db.py` como punto unico de acceso a SQLite para centralizar la interaccion con la fuente de verdad del sistema.

## Archivos modificados

- `src/db.py`
- `ai_history/02_implementacion.md`

## Cambios realizados

- Se creo la configuracion central de rutas para `database.sqlite`, `schema.sql` y `seed.sql`.
- Se implemento la conexion SQLite con `PRAGMA foreign_keys = ON`.
- Se habilito un row factory que devuelve filas como diccionarios.
- Se agregaron funciones para inicializar el schema y cargar datos seed.
- Se agregaron funciones auxiliares reutilizables para consultas de lectura y escritura.
- Se valido `db.py` creando una base temporal, cargando schema + seed y consultando registros.
- Se valido la sintaxis con `py -m py_compile src/db.py`.

## Endpoints creados o modificados

No aplica. En esta tarea no se implemento Flask ni endpoints.

## Formato de request

No aplica. No se crearon endpoints ni contratos HTTP en esta tarea.

## Formato de response

No aplica. No se crearon endpoints ni contratos HTTP en esta tarea.

## Cambios en base de datos

No se modifico la estructura de base de datos.

Funciones creadas en `src/db.py`:

- `dict_factory(cursor, row)`: convierte filas SQLite en diccionarios.
- `get_db_connection(db_path=DATABASE_PATH)`: abre una conexion SQLite configurada con claves foraneas y row factory.
- `read_sql_file(path)`: lee archivos SQL desde disco.
- `execute_script(script_path, db_path=DATABASE_PATH)`: ejecuta scripts SQL y confirma la transaccion.
- `initialize_schema(db_path=DATABASE_PATH)`: crea la estructura definida en `schema.sql`.
- `load_seed(db_path=DATABASE_PATH)`: carga los datos de prueba definidos en `seed.sql`.
- `initialize_database(db_path=DATABASE_PATH, with_seed=False)`: inicializa schema y opcionalmente seed.
- `fetch_one(query, params=None, db_path=DATABASE_PATH)`: ejecuta una consulta de lectura y devuelve un diccionario o `None`.
- `fetch_all(query, params=None, db_path=DATABASE_PATH)`: ejecuta una consulta de lectura y devuelve una lista de diccionarios.
- `execute_query(query, params=None, db_path=DATABASE_PATH)`: ejecuta una escritura y devuelve `lastrowid` y `rowcount`.

## Decisiones tomadas

- Se mantuvo `src/db.py` sin dependencias de Flask para que pueda reutilizarse desde endpoints y tests.
- Se uso `src/database.sqlite` como ruta por defecto de la base persistida local.
- Todas las conexiones habilitan claves foraneas para respetar las relaciones definidas en `schema.sql`.
- Las funciones aceptan `db_path` opcional para facilitar pruebas con bases temporales sin tocar la base real.
- Los helpers devuelven diccionarios para que la API pueda construir respuestas sin depender de objetos internos de SQLite.

## Riesgos identificados

- `load_seed()` borra datos existentes porque ejecuta `seed.sql`; debe usarse solo para desarrollo o pruebas.
- Aun no existe capa Flask ni endpoints, por lo que ningun flujo HTTP consume `db.py` todavia.

## Pendientes para Frontend

- No hay cambios de contrato HTTP para consumir todavia.
- Esperar a que Backend implemente `GET /api/dashboard` usando `db.py` como fuente unica de datos.
- Mantener el frontend sin estado critico propio; toda informacion operativa debe venir de la API cuando exista.

## Pendientes generales

- Implementar `GET /api/dashboard`.
- Implementar `POST /api/contact-attempts`.
- Implementar `POST /api/policies/{id}/renew`.
- Implementar tests automatizados de clasificacion y renovacion.

## Fecha

2026-06-02

## Agente responsable

Backend - Codex CLI

## Objetivo

Implementar `src/app.py` con Flask y los tres endpoints definidos en `spec.md`, manteniendo SQLite como fuente de verdad y `src/db.py` como unica via de acceso a la base de datos.

## Archivos modificados

- `src/app.py`
- `requirements.txt`
- `ai_history/02_implementacion.md`

## Cambios realizados

- Se implemento una aplicacion Flask simple y ejecutable localmente.
- Se creo `GET /api/dashboard`.
- Se creo `POST /api/contact-attempts`.
- Se creo `POST /api/policies/<id>/renew`.
- Se implemento la clasificacion de prioridad en backend usando `expiration_date` y `renewal_status`.
- Se centralizo todo acceso a SQLite mediante las funciones de `src/db.py`.
- Se agrego Flask a `requirements.txt`.
- Se valido la app con el cliente de pruebas de Flask usando datos de `seed.sql`.

## Endpoints creados o modificados

- `GET /api/dashboard`: retorna resumen y listado de polizas clasificadas.
- `POST /api/contact-attempts`: registra una gestion comercial asociada a una poliza.
- `POST /api/policies/<id>/renew`: renueva una poliza, actualiza fecha de vencimiento y marca estado `renewed`.

## Formato de request

`GET /api/dashboard`

No requiere body.

`POST /api/contact-attempts`

```json
{
  "policy_id": 1,
  "channel": "call",
  "result": "Cliente interesado",
  "notes": "Solicita propuesta",
  "attempted_at": "2026-06-02T17:30:00"
}
```

Campos obligatorios:

- `policy_id`
- `channel`: `call`, `email` o `message`
- `result`

Campos opcionales:

- `notes`
- `attempted_at`

`POST /api/policies/<id>/renew`

```json
{
  "expiration_date": "2027-06-02"
}
```

## Formato de response

`GET /api/dashboard`

```json
{
  "summary": {
    "total": 8,
    "proxima_a_vencer": 2,
    "ventana_critica": 2,
    "nueva_contratacion": 2,
    "renovada": 2,
    "sin_prioridad": 0
  },
  "policies": []
}
```

Cada poliza incluye:

- datos de poliza
- `priority`
- datos de cliente
- datos de asesor

`POST /api/contact-attempts`

```json
{
  "contact_attempt": {
    "id": 1,
    "policy_id": 1,
    "client_id": 1,
    "advisor_id": 1,
    "channel": "call",
    "result": "Cliente interesado",
    "notes": "Solicita propuesta",
    "attempted_at": "2026-06-02 17:30:00",
    "created_at": "2026-06-02 17:30:00"
  }
}
```

`POST /api/policies/<id>/renew`

```json
{
  "policy": {
    "id": 3,
    "policy_number": "POL-AUTO-0003",
    "expiration_date": "2027-06-02",
    "renewal_status": "renewed",
    "renewed_at": "2026-06-02 17:30:00",
    "priority": "renovada"
  }
}
```

## Cambios en base de datos

- No se modifico `schema.sql`.
- `POST /api/contact-attempts` inserta registros en `contact_attempts`.
- `POST /api/policies/<id>/renew` actualiza `policies.expiration_date`, `policies.renewal_status`, `policies.renewed_at` y `policies.updated_at`.

## Decisiones tomadas

- `src/app.py` no accede a SQLite directamente; usa `db.fetch_all`, `db.fetch_one`, `db.execute_query` y `db.initialize_schema`.
- La app inicializa solo el schema al arrancar, pero no carga seed automaticamente para evitar borrar datos reales.
- En `POST /api/contact-attempts`, `client_id` y `advisor_id` se derivan desde SQLite usando `policy_id`; no se confia en el frontend para esos datos.
- La prioridad se devuelve como `proxima_a_vencer`, `ventana_critica`, `nueva_contratacion`, `renovada` o `sin_prioridad`.
- Se agrego `sin_prioridad` para polizas pendientes que vencen en mas de 30 dias, fuera de los grupos operativos de gestion inmediata.
- No se implemento autenticacion ni endpoints fuera del alcance definido.

## Riesgos identificados

- Aun faltan tests automatizados formales; la validacion actual se hizo con el cliente de pruebas de Flask.
- El frontend debe consumir `priority` desde el backend y no duplicar la regla de clasificacion.
- La carga de seed sigue siendo manual mediante `db.load_seed()` o `db.initialize_database(with_seed=True)`.

## Pendientes para Frontend

- Consumir `GET /api/dashboard` y usar `summary` + `policies`.
- Mostrar `priority` exactamente como llega del backend o mapearlo solo a etiquetas visuales.
- Enviar gestiones comerciales a `POST /api/contact-attempts` con `policy_id`, `channel` y `result`.
- Enviar renovaciones a `POST /api/policies/<id>/renew` con `expiration_date`.
- No calcular prioridades en JavaScript.

## Pendientes generales

- Implementar tests automatizados para clasificacion y renovacion.
- Documentar pruebas manuales en Postman.

## Fecha

2026-06-02

## Agente responsable

Backend - Codex CLI

## Objetivo

Ajustar la ejecucion local de Flask para que la aplicacion no quede en modo debug en la entrega final.

## Archivos modificados

- `src/app.py`
- `ai_history/02_implementacion.md`

## Cambios realizados

- Se cambio `app.run(debug=True)` por `app.run(debug=False)`.
- No se modificaron endpoints ni logica de negocio.

## Endpoints creados o modificados

No aplica. No se crearon ni modificaron endpoints.

## Formato de request

No aplica. No hubo cambios de contrato HTTP.

## Formato de response

No aplica. No hubo cambios de contrato HTTP.

## Cambios en base de datos

No aplica. No hubo cambios en SQLite.

## Decisiones tomadas

- Se desactivo debug en la ejecucion directa de `src/app.py` para evitar comportamiento de desarrollo en la entrega final.
- Se mantuvo intacta la configuracion de endpoints existente.

## Riesgos identificados

- Ninguno identificado para este ajuste puntual.

## Pendientes para Frontend

- Ninguno. No hay cambios en contratos ni respuestas.

## Pendientes generales

- Mantener validaciones finales antes de la entrega.

## Fecha

2026-06-02

## Agente responsable

Backend - Codex CLI

## Objetivo

Implementar pruebas automatizadas con pytest para validar la clasificacion de renovaciones y la renovacion de polizas usando SQLite como fuente de verdad.

## Archivos modificados

- `tests/test_renewals.py`
- `src/app.py`
- `requirements.txt`
- `ai_history/02_implementacion.md`

## Cambios realizados

- Se implementaron 3 tests reales en `tests/test_renewals.py`.
- Se agrego `pytest` a `requirements.txt`.
- Se ajusto `create_app(database_path=None)` para permitir ejecutar la app contra una base SQLite temporal en tests.
- Se mantuvo `src/db.py` como unica via de acceso a SQLite.
- Se valido que los tests no usen `src/database.sqlite`.

## Endpoints creados o modificados

No se crearon endpoints nuevos.

Se probo el endpoint existente:

- `POST /api/policies/<id>/renew`

Tambien se uso el endpoint existente:

- `GET /api/dashboard`

## Formato de request

Para renovacion:

```json
{
  "expiration_date": "2027-06-02"
}
```

## Formato de response

Los tests validan que la renovacion responda:

```json
{
  "policy": {
    "id": 3,
    "expiration_date": "2027-06-02",
    "renewal_status": "renewed",
    "priority": "renovada"
  }
}
```

## Cambios en base de datos

- No se modifico `schema.sql`.
- Los tests crean una base SQLite temporal por prueba usando `db.initialize_database(..., with_seed=True)`.
- La renovacion se verifica tambien consultando SQLite mediante `db.fetch_one`.

## Decisiones tomadas

- Los tests usan bases temporales bajo `tmp_path` para no tocar `src/database.sqlite`.
- `create_app()` acepta `database_path` opcional para separar entorno real y entorno de pruebas.
- La clasificacion se prueba mediante `GET /api/dashboard`, no llamando directamente funciones internas, para validar comportamiento real del backend.
- La renovacion se prueba mediante `POST /api/policies/3/renew` y luego se confirma la persistencia en SQLite.

## Riesgos identificados

- Pytest puede intentar crear `.pytest_cache`; en este entorno genero un warning de permisos, sin fallar los tests.

## Pendientes para Frontend

- Ninguno. No hay cambios de contrato HTTP.
- El frontend debe seguir consumiendo `priority` desde backend.

## Pendientes generales

- Correr los tests con:

```powershell
py -m pytest tests/test_renewals.py -q -p no:cacheprovider
```

- Completar documentacion de pruebas manuales en Postman.
