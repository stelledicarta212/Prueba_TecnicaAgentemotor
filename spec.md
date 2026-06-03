# Especificación de la Solución

## 1. Entendimiento del problema

El problema principal consiste en reemplazar el proceso manual que actualmente utiliza María para gestionar la renovación de pólizas de seguros. Actualmente la información se encuentra distribuida en hojas de cálculo donde se registran vencimientos, seguimientos y renovaciones de manera manual.

Este enfoque genera varios riesgos operativos:

* Pérdida de contexto sobre conversaciones con clientes.
* Duplicidad de información.
* Errores humanos en el seguimiento.
* Dificultad para priorizar renovaciones.
* Pólizas vencidas que no son gestionadas oportunamente.
* Dependencia de archivos que pueden dañarse o quedar desactualizados.

Analizando el problema, se concluye que la necesidad principal no es únicamente visualizar pólizas, sino construir una fuente de información única, consistente y confiable que permita a María tomar decisiones sobre su cartera de clientes.

Adicionalmente, el negocio establece una regla crítica: una póliza vencida dentro de los primeros 30 días posteriores al vencimiento mantiene una ventaja operativa para el intermediario. Después de ese periodo, la oportunidad pasa a comportarse como una nueva contratación.

---

## 2. Objetivos de la solución

La aplicación debe permitir:

* Centralizar la información de clientes y pólizas.
* Establecer una única fuente de verdad para la operación.
* Priorizar renovaciones según reglas de negocio.
* Registrar historial de gestiones comerciales.
* Mantener trazabilidad sobre cada cliente.
* Reducir la pérdida de clientes por falta de seguimiento.
* Reemplazar el uso de hojas de cálculo como mecanismo principal de gestión.

---

## 3. Fuente de verdad del sistema

La decisión arquitectónica más importante de esta solución es definir la base de datos como la única fuente de verdad del sistema.

Todos los datos relacionados con clientes, pólizas, vencimientos, renovaciones e intentos de contacto deben almacenarse y consultarse desde la base de datos SQLite.

Ni el frontend, ni archivos externos, ni estados temporales del navegador deben ser considerados fuentes válidas de información.

La API REST actuará como la única capa autorizada para modificar o consultar información persistida.

Esta decisión busca eliminar los problemas observados en el proceso actual basado en Excel:

* Información duplicada.
* Versiones inconsistentes del mismo archivo.
* Pérdida de historial.
* Actualizaciones manuales difíciles de auditar.
* Dependencia del conocimiento individual del asesor.

Cuando María abra el sistema, toda la información visualizada en el dashboard deberá reconstruirse a partir de la información almacenada en la base de datos.

De esta manera se garantiza consistencia, trazabilidad y confiabilidad operativa.

---

## 4. Alcance funcional

### Funcionalidades incluidas

* Dashboard principal.
* Visualización de pólizas.
* Clasificación automática por prioridad.
* Registro de llamadas.
* Registro de correos electrónicos.
* Registro de mensajes.
* Historial de gestiones.
* Renovación de pólizas.
* Persistencia en SQLite.
* API REST.
* Tests automatizados.
* Documentación de pruebas manuales en Postman.

### Funcionalidades excluidas

* Autenticación.
* Gestión de usuarios.
* Roles y permisos.
* Integraciones con aseguradoras.
* Notificaciones automáticas.
* Importación desde Excel.
* Reportes avanzados.
* Integraciones cloud.

Estas funcionalidades se excluyen para mantener el alcance alineado con el tiempo estimado de la prueba.

---

## 5. Flujo principal del sistema

1. María accede al dashboard.
2. El sistema consulta la información desde la base de datos.
3. Las pólizas son clasificadas automáticamente.
4. María identifica clientes prioritarios.
5. Registra una gestión comercial.
6. La gestión se almacena en la base de datos.
7. Si la póliza se renueva, se actualiza la fecha de vencimiento.
8. El dashboard refleja inmediatamente la información persistida.

En todo momento la base de datos permanece como fuente de verdad.

---

## 6. Modelo de datos

La solución utiliza las siguientes entidades:

### Advisors

Representa al asesor responsable de la cartera.

### Clients

Representa a los clientes administrados por el asesor.

### Policies

Representa las pólizas asociadas a cada cliente.

### Contact Attempts

Representa cada interacción realizada con el cliente.

Estas entidades permiten mantener trazabilidad completa sobre el ciclo de renovación.

El detalle de las relaciones se encuentra documentado en el diagrama entidad-relación ubicado en la carpeta `docs`.

---

## 7. Arquitectura de la solución

La solución utiliza una arquitectura de tres capas:

### Frontend

HTML, CSS y JavaScript.

Responsable únicamente de presentar información y capturar acciones del usuario.

### Backend

Flask REST API.

Responsable de aplicar reglas de negocio, validar datos y coordinar operaciones.

### Persistencia

SQLite.

Responsable de almacenar toda la información crítica del negocio.

La arquitectura fue diseñada para garantizar que toda la operación dependa de una fuente única y consistente de información.

---

## 8. Endpoints propuestos

### Obtener Dashboard

```http
GET /api/dashboard
```

Retorna el resumen operativo y las pólizas activas clasificadas según prioridad.

Incluye:
- resumen de métricas;
- datos de póliza;
- datos del cliente;
- datos del asesor;
- historial de gestiones comerciales;
- prioridad calculada en backend.

### Registrar Gestión

```http
POST /api/contact-attempts
```

Permite registrar llamadas, correos o mensajes realizados a un cliente.

Este endpoint guarda trazabilidad comercial sobre una póliza específica.

### Renovar Póliza

```http
POST /api/policies/{id}/renew
```

Permite actualizar la fecha de vencimiento de una póliza renovada.

Al renovar:
- actualiza `expiration_date`;
- cambia `renewal_status` a `renewed`;
- registra `renewed_at`;
- la prioridad pasa a renovada.

### Crear Cliente + Póliza

```http
POST /api/policies
```

Permite crear un nuevo cliente junto con su póliza.

Se decidió crear cliente y póliza en una misma operación porque para María el flujo real no es crear entidades aisladas, sino registrar una oportunidad de gestión comercial completa.

### Editar Cliente + Póliza

```http
PUT /api/policies/{id}
```

Permite editar datos del cliente y de la póliza asociada.

Este endpoint permite corregir información sin depender de cambios manuales en la base de datos.

### Archivar Póliza

```http
PATCH /api/policies/{id}/archive
```

Permite archivar una póliza sin eliminarla físicamente.

Se eligió archivado lógico en lugar de borrado físico para conservar trazabilidad histórica de la gestión comercial.

Todos los endpoints interactúan directamente con SQLite mediante la API.

La base de datos permanece como fuente de verdad del sistema. El frontend no calcula prioridades ni persiste información crítica de negocio.

---

## 9. Regla de negocio principal

La prioridad de una póliza se determina comparando la fecha de vencimiento con la fecha actual.

### Próxima a vencer

Vence dentro de los próximos 30 días.

### Ventana crítica

Venció entre 1 y 30 días atrás.

### Nueva contratación

Venció hace más de 30 días.

Esta clasificación permite priorizar los esfuerzos comerciales sobre las oportunidades con mayor impacto para el negocio.

---

## 10. Estrategia de pruebas

Se implementarán pruebas automatizadas enfocadas en la regla más importante del negocio:

* Clasificación de pólizas próximas a vencer.
* Clasificación de pólizas dentro de la ventana crítica.
* Renovación correcta de pólizas.

Adicionalmente se documentarán pruebas manuales utilizando Postman para validar:

* `GET /api/dashboard`
* `POST /api/contact-attempts`
* `POST /api/policies/{id}/renew`

La documentación de estas pruebas quedará almacenada en la carpeta `postman`.

---

## 11. Trade-offs y decisiones arquitectónicas

La principal decisión de diseño fue priorizar simplicidad y claridad sobre escalabilidad.

Se decidió utilizar SQLite como fuente de verdad debido a su facilidad de ejecución y porque cumple adecuadamente con los objetivos de la prueba.

No se implementó autenticación ni gestión multiusuario debido a que el problema planteado está enfocado en el flujo operativo de una única asesora.

La solución busca demostrar entendimiento del negocio, claridad arquitectónica y capacidad para transformar un proceso manual basado en Excel en una aplicación respaldada por una fuente de verdad centralizada y confiable.

---

## 12. Uso de IA durante el desarrollo

Durante el desarrollo de esta prueba se utilizarán herramientas de IA como apoyo técnico controlado.

La estrategia será trabajar con dos asistentes de IA en paralelo:

- **Codex CLI:** apoyo principal para backend, API REST, SQLite y tests.
- **Gemini CLI:** apoyo principal para frontend, interfaz, JavaScript y ajustes visuales.

Cada IA deberá registrar las tareas realizadas, decisiones tomadas y cambios aplicados dentro de la carpeta `ai_history`. Esto permite mantener trazabilidad del proceso y asegurar que ambos asistentes tengan contexto compartido durante la implementación.

El uso de IA no reemplaza la responsabilidad técnica del desarrollador. La arquitectura, alcance, decisiones finales y revisión del código serán validadas manualmente antes de la entrega.

Todas las conversaciones relevantes serán guardadas en archivos Markdown dentro de `ai_history`, siguiendo el requisito obligatorio de la prueba.

---

## 13. Estrategia de colaboración asistida por IA

Durante la implementación se utilizará una estrategia de colaboración entre múltiples asistentes especializados.

### Arquitecto

Responsable de validar arquitectura, alcance y alineación con el problema de negocio.

### Backend

Responsable de la API REST, persistencia SQLite y reglas de negocio.

### Frontend

Responsable de la interfaz de usuario y experiencia operativa de María.

Todos los asistentes compartirán contexto mediante documentación persistida en la carpeta `ai_history`, garantizando trazabilidad y continuidad entre tareas.

La fuente de verdad continuará siendo la base de datos y no los estados temporales generados por los asistentes.

---

### Endpoints implementados

#### Dashboard

```http
GET /api/dashboard
```

Retorna:

* KPIs comerciales
* pólizas próximas a vencer
* pólizas en ventana crítica
* pólizas archivadas
* historial de actividad

---

#### Registrar intento de contacto

```http
POST /api/contact-attempts
```

Permite registrar una gestión comercial realizada por el asesor.

Ejemplos:

* llamada realizada
* mensaje enviado
* cliente contactado
* seguimiento pendiente

---

#### Renovar póliza

```http
POST /api/policies/{id}/renew
```

Renueva una póliza existente y actualiza automáticamente su fecha de vencimiento.

---

#### Crear póliza

```http
POST /api/policies
```

Crea una nueva póliza junto con la información necesaria para la gestión comercial.

---

#### Editar póliza

```http
PUT /api/policies/{id}
```

Permite modificar los datos de una póliza existente.

---

#### Archivar póliza

```http
PATCH /api/policies/{id}/archive
```

Realiza archivado lógico de la póliza.

La información permanece disponible para auditoría y trazabilidad, pero deja de mostrarse en los listados activos.