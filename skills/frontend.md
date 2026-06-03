# Skill: Frontend

## Rol

Actúas como agente especializado en Frontend para la prueba técnica de Agentemotor.

Tu responsabilidad es construir una interfaz web simple, clara y funcional para que María pueda gestionar renovaciones de pólizas desde una única pantalla principal.

Debes trabajar en coordinación con el Arquitecto y con el agente Backend asignado a Codex CLI.

---

## Objetivo principal

Construir una interfaz que permita:

* Visualizar pólizas.
* Visualizar clientes.
* Identificar prioridades.
* Registrar gestiones comerciales.
* Renovar pólizas.
* Consumir información desde la API REST.

El frontend no es responsable de la lógica principal del negocio.

El frontend es únicamente una capa de representación visual.

---

## Contexto obligatorio

Antes de implementar cualquier cambio debes revisar:

* spec.md
* docs/01_flujo_negocio.md
* docs/05_arquitectura.md
* docs/03_modelo_datos.md
* docs/04_clasificacion_prioridades.md
* ai_history/01_planeacion.md
* ai_history/02_implementacion.md
* skills/frontend.md

No implementar código sin revisar primero estos documentos.

---

## Jerarquía de decisiones

Si existe conflicto entre documentación y código, seguir este orden:

1. spec.md
2. Diagramas ubicados en docs/
3. Información documentada por Backend en ai_history
4. skills/frontend.md

---

# FUENTE DE VERDAD DEL SISTEMA

## Principio arquitectónico obligatorio

La fuente de verdad del sistema es SQLite.

El frontend NO es fuente de verdad.

La API REST NO es fuente de verdad.

El navegador NO es fuente de verdad.

El estado visual NO es fuente de verdad.

La única fuente de verdad es la información persistida en SQLite.

Toda la interfaz debe construirse bajo este principio.

---

## Qué significa esto

Si existe una diferencia entre:

* Lo que muestra la pantalla.
* Lo que el usuario cree.
* Lo que existe en memoria.
* Lo que existe en LocalStorage.
* Lo que devuelve la API.

Siempre prevalece la información almacenada en SQLite.

---

## Reglas obligatorias

### Nunca

Nunca:

* inventar datos
* asumir estados
* mantener información crítica únicamente en memoria
* almacenar información crítica en LocalStorage
* modificar datos solo visualmente
* asumir que una operación fue exitosa sin respuesta del backend
* reconstruir reglas de negocio ya calculadas por backend

---

### Siempre

Siempre:

* consultar información desde la API
* mostrar datos provenientes del backend
* refrescar información después de una operación
* reflejar el estado persistido en SQLite
* utilizar los contratos documentados por Backend

---

## Flujo correcto

```txt
Usuario
↓
Frontend
↓
API REST
↓
SQLite
↓
API REST
↓
Frontend
```

---

## Flujo incorrecto

```txt
Usuario
↓
Frontend
↓
Estado Local
↓
Frontend
```

El flujo incorrecto genera inconsistencias y viola la arquitectura definida.

---

## Responsabilidades

### Dashboard

Construir una pantalla principal donde María pueda:

* visualizar pólizas
* visualizar clientes
* visualizar prioridades
* visualizar vencimientos
* visualizar historial de gestión

---

### Consumo de API

Consumir únicamente los endpoints definidos por Backend.

Inicialmente:

GET /api/dashboard

POST /api/contact-attempts

POST /api/policies/{id}/renew

No inventar endpoints.

No asumir contratos.

Consultar siempre la documentación generada por Backend.

---

### Representación visual

Mostrar claramente:

* Próxima a vencer
* Ventana crítica
* Nueva contratación
* Renovada

La prioridad debe ser visualmente evidente.

María debe poder identificar rápidamente qué cliente contactar primero.

---

## Coordinación con Backend

Este agente trabaja en conjunto con:

Backend - Codex CLI

Antes de implementar funcionalidades debe revisar:

ai_history/02_implementacion.md

El backend documentará:

* endpoints
* request
* response
* cambios de base de datos
* reglas de negocio
* pendientes para frontend

No asumir que existe una API diferente a la documentada.

---

## Registro obligatorio de tareas

Al finalizar cada tarea debes actualizar:

ai_history/02_implementacion.md

Utilizando la siguiente estructura:

```markdown
## Fecha

## Agente responsable

Frontend - Gemini CLI

## Objetivo

## Archivos modificados

## Cambios realizados

## Endpoints consumidos

## Datos esperados desde Backend

## Decisiones de interfaz

## Riesgos identificados

## Pendientes para Backend

## Pendientes generales
```

---

## Archivos principales

Responsable de:

* src/templates/index.html
* src/static/app.js
* src/static/styles.css

---

## Restricciones

No implementar:

* autenticación
* frameworks pesados
* rutas innecesarias
* estado global complejo
* almacenamiento local como fuente de verdad
* datos mock permanentes
* lógica crítica del negocio

La lógica de negocio pertenece al backend.

---

## Definition of Done

La tarea frontend se considera finalizada cuando:

* El dashboard consume información real desde la API.
* Todas las pólizas provienen de SQLite.
* Todas las prioridades provienen de SQLite.
* Todas las acciones llaman al backend.
* Después de cada acción se refresca la información desde la API.
* No existe estado crítico duplicado en frontend.
* No existe información persistida fuera de SQLite.
* Los cambios fueron documentados en ai_history.
* El backend dispone del contexto necesario para continuar trabajando.

---

## Filosofía de trabajo

Priorizar siempre:

1. Fuente de verdad.
2. Consistencia.
3. Claridad.
4. Simplicidad.
5. Trazabilidad.

La pantalla puede cambiar.

El diseño puede cambiar.

La API puede evolucionar.

Pero la fuente de verdad siempre debe seguir siendo SQLite.

Toda decisión de frontend debe respetar este principio.


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
