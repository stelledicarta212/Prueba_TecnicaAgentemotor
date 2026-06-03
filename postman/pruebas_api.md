# Pruebas Manuales en Postman

## Objetivo

Validar manualmente los endpoints principales de la aplicación antes de la entrega final y la grabación del video.

---

# Prueba 01 - Consultar Dashboard

## Descripción

Verificar que el dashboard cargue correctamente el resumen de la cartera y la clasificación de pólizas.

## Solicitud

**Método**

```http
GET
```

**Endpoint**

```http
/api/dashboard
```

## Resultado esperado

```json
{
  "policies": [],
  "summary": {
    "total": 0,
    "proxima_a_vencer": 0,
    "ventana_critica": 0,
    "nueva_contratacion": 0,
    "renovada": 0,
    "sin_prioridad": 0
  }
}
```

## Validación de negocio

* El dashboard responde correctamente.
* Se genera el resumen de pólizas.
* La clasificación se realiza desde el backend.
* El frontend únicamente muestra la información.

---

# Prueba 02 - Registrar Gestión

## Descripción

Verificar que el asesor pueda registrar una gestión realizada sobre una póliza.

## Solicitud

**Método**

```http
POST
```

**Endpoint**

```http
/api/policies/{policy_id}/contact-attempts
```

## Body

```json
{
  "channel": "phone",
  "note": "Se llamó al cliente y solicitó cotización para renovación."
}
```

## Resultado esperado

```json
{
  "success": true,
  "message": "Gestión registrada correctamente."
}
```

## Validación de negocio

* La gestión queda almacenada.
* Se conserva el historial de contactos.
* María puede consultar acciones realizadas previamente.
* Se reemplaza la anotación manual realizada en Excel.

---

# Prueba 03 - Renovar Póliza

## Descripción

Validar el flujo crítico del negocio: renovación de una póliza.

## Solicitud

**Método**

```http
POST
```

**Endpoint**

```http
/api/policies/{policy_id}/renew
```

## Body

```json
{
  "new_expiration_date": "2027-06-03"
}
```

## Resultado esperado

```json
{
  "success": true,
  "message": "Póliza renovada correctamente."
}
```

## Validación de negocio

* La póliza cambia a estado renovada.
* Se almacena la nueva fecha de vencimiento.
* La póliza deja de aparecer como pendiente de gestión.
* El asesor conserva al cliente.

---

# Prueba 04 - Validar Dashboard Después de Renovación

## Descripción

Verificar que el dashboard refleje correctamente los cambios realizados después de renovar una póliza.

## Solicitud

**Método**

```http
GET
```

**Endpoint**

```http
/api/dashboard
```

## Resultado esperado

* Incrementa el contador de pólizas renovadas.
* Disminuye el contador de pólizas pendientes.
* El dashboard refleja el estado actualizado de la cartera.

## Validación de negocio

* La información es consistente.
* La fuente de verdad sigue siendo la base de datos.
* La interfaz refleja correctamente las reglas de negocio.

---

# Conclusión

Se realizaron pruebas manuales utilizando Postman Desktop para validar los escenarios críticos de la aplicación.

Escenarios validados:

1. Consulta del dashboard.
2. Registro de gestión.
3. Renovación de póliza.
4. Actualización del dashboard posterior a la renovación.

Estas pruebas confirman el correcto funcionamiento del flujo principal de negocio orientado a la gestión y renovación de pólizas.

---

## Resultados reales de validación

### Prueba 01 - Consultar Dashboard (Resultado)

```json
{
  "policies": [
    {
      "advisor": {
        "id": 1,
        "name": "Maria Gonzalez"
      },
      "archived_at": null,
      "client": {
        "document_number": "1033233444",
        "email": "prueba@gmail.com",
        "full_name": "Carlos",
        "id": 1,
        "phone": "3123334455"
      },
      "contact_attempts": [],
      "expiration_date": "2026-06-11",
      "id": 1,
      "insurance_type": "Hogar",
      "insurer": "Andina",
      "policy_number": "001",
      "priority": "proxima_a_vencer",
      "renewal_status": "pending",
      "renewed_at": null
    }
  ],
  "summary": {
    "nueva_contratacion": 0,
    "proxima_a_vencer": 1,
    "renovada": 0,
    "sin_prioridad": 0,
    "total": 1,
    "ventana_critica": 0
  }
}
```

**Validación realizada**

La API respondió correctamente y devolvió una póliza cargada desde SQLite.

La póliza con fecha de vencimiento 2026-06-11 fue clasificada como proxima_a_vencer, lo cual confirma que el backend está aplicando la regla de negocio de priorización antes de enviar la información al frontend.

El resumen también se actualizó correctamente:

- Total de pólizas: 1
- Próximas a vencer: 1
- Ventana crítica: 0
- Nueva contratación: 0
- Renovadas: 0

Esto valida que la base de datos funciona como fuente de verdad y que el dashboard consume datos calculados por la API.

---

### Prueba 03 - Renovar Póliza (Resultado)

**Endpoint**

`POST /api/policies/1/renew`

**Payload**

```json
{
  "expiration_date": "2027-06-11"
}
```

**Validación de negocio**

El sistema permitió cerrar el flujo crítico de renovación.

Después de renovar la póliza:

- La prioridad cambió a renovada.
- El estado comercial cambió a renewed.
- La nueva fecha de vencimiento quedó almacenada.
- El dashboard actualizó el resumen correctamente.
- El contador renovada pasó a 1.
- El contador proxima_a_vencer pasó a 0.

Esto confirma que SQLite funciona como fuente de verdad y que el backend recalcula el estado del dashboard después de una acción crítica.