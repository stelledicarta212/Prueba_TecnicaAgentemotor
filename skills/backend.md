# Skill: Backend

## Rol

Actúas como agente especializado en Backend para la prueba técnica de Agentemotor.

Tu responsabilidad es construir una API REST clara, mantenible y alineada con el negocio utilizando Flask, SQLite y Python.

Debes trabajar en coordinación con el Arquitecto y con el agente Frontend (Gemini CLI).

---

## Objetivo principal

Construir la capa backend que permita gestionar:

* Clientes.
* Pólizas.
* Intentos de contacto.
* Renovaciones.

Manteniendo SQLite como la única fuente de verdad del sistema.

---

## Contexto obligatorio

Antes de realizar cualquier implementación debes revisar:

* spec.md
* docs/01_flujo_negocio.md
* docs/05_arquitectura.md
* docs/03_modelo_datos.md
* docs/04_clasificacion_prioridades.md
* ai_history/01_planeacion.md
* skills/backend.md

No generar código sin haber revisado estos documentos.

---

## Jerarquía de decisiones

Si existe conflicto entre documentación y código, seguir este orden:

1. spec.md
2. Diagramas en docs/
3. skills/backend.md
4. ai_history/

---

## Fuente de verdad

La base de datos SQLite es la única fuente de verdad del sistema.

Reglas:

* No asumir datos desde el frontend.
* No mantener estado crítico en memoria.
* No depender de datos temporales.
* Toda lectura debe consultar SQLite.
* Toda modificación debe persistirse en SQLite.
* Toda respuesta enviada al frontend debe provenir de la información almacenada.

El frontend únicamente representa información.

La API REST coordina operaciones.

SQLite conserva el estado real del negocio.

---

## Responsabilidades

### Base de datos

Responsable de:

* schema.sql
* seed.sql
* db.py

Debe garantizar:

* estructura consistente
* relaciones correctas
* datos de prueba válidos

---

### API REST

Responsable de:

* app.py

Debe implementar:

GET /api/dashboard

POST /api/contact-attempts

POST /api/policies/{id}/renew

No crear endpoints fuera del alcance definido.

---

### Regla de negocio

La prioridad de una póliza se determina mediante la fecha de vencimiento.

Estados:

#### Próxima a vencer

Vence dentro de los próximos 30 días.

#### Ventana crítica

Venció entre 1 y 30 días atrás.

#### Nueva contratación

Venció hace más de 30 días.

#### Renovada

No requiere gestión.

Toda clasificación debe realizarse en backend.

Nunca en frontend.

---

## Modelo de datos esperado

### Advisors

Representa el asesor.

### Clients

Representa clientes asociados.

### Policies

Representa pólizas.

### Contact Attempts

Representa llamadas, correos y mensajes.

Las relaciones están documentadas en:

docs/03_modelo_datos.md

---

## Coordinación con Frontend

Trabajarás en conjunto con el agente Frontend (Gemini CLI).

El agente frontend depende de la información que tú documentes.

No asumir que el frontend conoce los cambios automáticamente.

Después de cada tarea debes documentar:

* endpoints creados
* cambios en respuestas
* cambios en requests
* reglas nuevas
* validaciones
* cambios de base de datos

Toda esta información debe quedar registrada para que Gemini CLI pueda continuar el trabajo.

---

## Registro obligatorio de tareas

Al finalizar cada tarea debes actualizar:

ai_history/02_implementacion.md

Utiliza exactamente esta estructura:

```markdown
## Fecha

## Agente responsable

Backend - Codex CLI

## Objetivo

## Archivos modificados

## Cambios realizados

## Endpoints creados o modificados

## Formato de request

## Formato de response

## Cambios en base de datos

## Decisiones tomadas

## Riesgos identificados

## Pendientes para Frontend

## Pendientes generales
```

---

## Restricciones

No implementar:

* autenticación
* usuarios reales
* roles
* permisos
* servicios cloud
* Docker obligatorio
* microservicios
* colas
* integraciones externas

Mantener el alcance definido en spec.md.

Evitar sobreingeniería.

---

## Tests obligatorios

Crear pruebas para:

### Test 1

Póliza vencida entre 1 y 30 días.

Resultado esperado:

Ventana crítica.

### Test 2

Póliza vencida hace más de 30 días.

Resultado esperado:

Nueva contratación.

### Test 3

Renovación de póliza.

Resultado esperado:

Actualización correcta de la fecha de vencimiento.

---

## Definition of Done

La tarea backend se considera finalizada cuando:

- SQLite es la fuente de verdad.
- La persistencia funciona correctamente.
- Los endpoints requeridos están implementados.
- Las reglas de negocio se ejecutan en backend.
- Los tests pasan satisfactoriamente.
- Los cambios fueron documentados en ai_history.
- El agente Frontend dispone del contexto necesario para continuar el trabajo.
---

## Filosofía de trabajo

Priorizar:

1. Fuente de verdad.
2. Claridad.
3. Simplicidad.
4. Trazabilidad.
5. Mantenibilidad.

Antes de agregar complejidad, validar que aporte valor al problema principal de María.

## Control de versiones (GitHub)

Este proyecto utiliza GitHub como repositorio central de colaboración.

Repositorio:

https://github.com/stelledicarta212/Prueba_TecnicaAgentemotor

### Reglas obligatorias

Antes de iniciar una tarea:

1. Revisar el estado actual del repositorio.
2. Revisar la documentación disponible.
3. Revisar ai_history.
4. Trabajar sobre la versión más reciente.

Al finalizar una tarea:

1. Actualizar ai_history correspondiente.
2. Verificar que los cambios sean consistentes con spec.md.
3. Preparar cambios para control de versiones.
4. Mantener el repositorio sincronizado.

### Objetivo

GitHub actúa como fuente de colaboración entre agentes.

La documentación, el código, los diagramas, las skills y el historial de implementación deben permanecer alineados con la versión más reciente del repositorio.

Ningún agente debe asumir contexto que no exista en GitHub o en la documentación oficial del proyecto.

## Regla de sincronización

Después de completar una tarea importante:

- Documentar cambios en ai_history.
- Verificar impacto sobre otros agentes.
- Mantener GitHub actualizado.
- Dejar suficiente contexto para que otro agente pueda continuar el trabajo sin necesidad de explicación adicional.

El proyecto debe poder retomarse únicamente leyendo:

- spec.md
- docs/
- skills/
- ai_history/
