# Prueba Técnica Agentemotor

Sistema de gestión de renovaciones de pólizas desarrollado con Flask, SQLite y JavaScript.

## Objetivo

Permitir a una asesora comercial gestionar pólizas próximas a vencer, registrar gestiones comerciales, renovar pólizas y administrar clientes desde una única plataforma.

---

# Arquitectura

Frontend:
- HTML
- CSS
- JavaScript Vanilla

Backend:
- Flask
- SQLite

Fuente de verdad:
- SQLite

La interfaz nunca es considerada fuente de verdad.
Todas las operaciones se realizan mediante la API y posteriormente se sincronizan desde la base de datos.

---

# Funcionalidades

## Dashboard

- Resumen de pólizas
- Próximas a vencer
- Ventana crítica
- Nueva contratación
- Renovadas

## Gestión Comercial

- Registrar llamadas
- Registrar correos
- Registrar mensajes
- Historial de gestiones

## Renovación

- Renovar póliza
- Actualizar fecha de vencimiento
- Cambio automático de estado

## Administración

- Crear cliente + póliza
- Editar cliente + póliza
- Archivar póliza

---

# Clasificación de Prioridades

## Próxima a vencer

Pólizas con vencimiento entre hoy y los próximos 30 días.

## Ventana crítica

Pólizas vencidas entre 1 y 30 días.

## Nueva contratación

Pólizas vencidas hace más de 30 días.

## Renovada

Pólizas renovadas exitosamente.

---

# Fuente de Verdad

La base de datos SQLite es la única fuente de verdad del sistema.

Reglas:

- El frontend nunca almacena datos de negocio.
- Después de cada operación se consulta nuevamente la API.
- Las prioridades se calculan en backend.
- Las validaciones se realizan en backend.
- La persistencia se realiza exclusivamente en SQLite.

---

# Colaboración con IA

Se utilizó una estrategia de agentes especializados.

## Codex CLI

Responsable de:

- Backend
- SQLite
- API REST
- Tests
- Reglas de negocio

## Gemini CLI

Responsable de:

- Frontend
- Dashboard
- Experiencia de usuario
- Integración con API

## Contexto Compartido

Ambos agentes trabajan utilizando:

- spec.md
- skills/
- docs/
- ai_history/

Cada tarea queda documentada para mantener continuidad y trazabilidad.

---

# Estructura del Proyecto

```txt
ai_history/
docs/
postman/
skills/
src/
tests/

README.md
spec.md
requirements.txt
```

# Ejecución

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar aplicación:

```bash
py src/app.py
```

Abrir:

```txt
http://127.0.0.1:5000
```

# Tests

Ejecutar:

```bash
pytest
```

# API Principal

GET

```txt
/api/dashboard
```

POST

```txt
/api/contact-attempts
```

POST

```txt
/api/policies
```

PUT

```txt
/api/policies/{id}
```

PATCH

```txt
/api/policies/{id}/archive
```

POST

```txt
/api/policies/{id}/renew
```

# Autor

Carlos Alvis

Prueba Técnica Agentemotor
2026