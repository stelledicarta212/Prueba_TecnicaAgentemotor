erDiagram

ADVISORS ||--o{ CLIENTS : manages
ADVISORS ||--o{ POLICIES : owns
CLIENTS ||--o{ POLICIES : has
POLICIES ||--o{ CONTACT_ATTEMPTS : receives

ADVISORS {
    int id
    string name
}

CLIENTS {
    int id
    int advisor_id
    string name
    string phone
    string email
}

POLICIES {
    int id
    int advisor_id
    int client_id
    string insurer
    string policy_type
    date expiration_date
    string status
    date renewed_at
    date new_expiration_date
}

CONTACT_ATTEMPTS {
    int id
    int policy_id
    string channel
    string notes
    datetime created_at
}

### Descripción del Diagrama 3 — Modelo de datos

Este diagrama representa la estructura mínima de datos necesaria para soportar el flujo de renovación de pólizas. El modelo separa claramente las entidades principales del negocio: asesores, clientes, pólizas e intentos de contacto.

Un asesor puede gestionar varios clientes y también puede tener varias pólizas asociadas a su cartera. Cada cliente puede tener una o más pólizas, lo cual refleja el caso real donde una misma persona puede tener seguros de auto, hogar, vida u otros productos.

La tabla de pólizas concentra la información clave para la gestión comercial: aseguradora, tipo de póliza, fecha de vencimiento, estado de la póliza y datos de renovación. Esta información permite clasificar las pólizas según su urgencia y determinar qué acciones debe tomar María.

La tabla de intentos de contacto permite conservar trazabilidad sobre cada gestión realizada, como llamadas, correos o mensajes. Esto soluciona uno de los principales problemas del Excel: la pérdida de contexto sobre qué se le ofreció al cliente, cuándo fue contactado y qué seguimiento quedó pendiente.

El objetivo del modelo es mantener una base simple pero suficiente para que la aplicación pueda mostrar prioridades, registrar acciones comerciales y actualizar renovaciones sin introducir complejidad innecesaria.