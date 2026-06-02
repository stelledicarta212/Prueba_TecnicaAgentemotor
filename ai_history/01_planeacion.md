# Estrategia de colaboración con IA

Se utilizará una estrategia de trabajo con múltiples asistentes especializados.

## Arquitecto

Responsable de:
- Definir alcance.
- Diseñar arquitectura.
- Mantener alineación con spec.md.
- Coordinar agentes.

## Backend (Codex CLI)

Responsable de:
- SQLite.
- API REST.
- Reglas de negocio.
- Tests.

## Frontend (Gemini CLI)

Responsable de:
- Dashboard.
- Consumo de API.
- Experiencia de usuario.

## Fuente de verdad

La base de datos SQLite será la única fuente de verdad del sistema.

Todo cambio deberá persistirse en la base de datos antes de reflejarse en la interfaz.

## Comunicación entre agentes

Antes de iniciar una nueva tarea, cada agente debe revisar:

- spec.md
- ai_history/01_planeacion.md
- ai_history/02_implementacion.md
- skills correspondientes

Esto garantiza que ambos agentes trabajen sobre el mismo contexto y evita decisiones contradictorias entre frontend y backend.

Ningún agente debe asumir comportamiento o estructura no documentada.

## Registro obligatorio de tareas

Al finalizar una tarea, cada agente debe actualizar `ai_history/02_implementacion.md` utilizando la siguiente estructura:

### Fecha

### Agente responsable

### Objetivo

### Archivos modificados

### Cambios realizados

### Decisiones tomadas

### Dependencias generadas

### Riesgos identificados

### Pendientes

