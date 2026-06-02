PRAGMA foreign_keys = ON;

DELETE FROM contact_attempts;
DELETE FROM policies;
DELETE FROM clients;
DELETE FROM advisors;

DELETE FROM sqlite_sequence
WHERE name IN ('contact_attempts', 'policies', 'clients', 'advisors');

INSERT INTO advisors (id, name, email, phone)
VALUES
    (1, 'Maria Gonzalez', 'maria.gonzalez@agentemotor.test', '+57 300 111 2233');

INSERT INTO clients (id, advisor_id, full_name, document_number, email, phone)
VALUES
    (1, 1, 'Carlos Ramirez', 'CC-10010001', 'carlos.ramirez@example.com', '+57 310 100 0001'),
    (2, 1, 'Laura Martinez', 'CC-10010002', 'laura.martinez@example.com', '+57 310 100 0002'),
    (3, 1, 'Andres Torres', 'CC-10010003', 'andres.torres@example.com', '+57 310 100 0003'),
    (4, 1, 'Sofia Herrera', 'CC-10010004', 'sofia.herrera@example.com', '+57 310 100 0004'),
    (5, 1, 'Jorge Castillo', 'CC-10010005', 'jorge.castillo@example.com', '+57 310 100 0005'),
    (6, 1, 'Valentina Rojas', 'CC-10010006', 'valentina.rojas@example.com', '+57 310 100 0006'),
    (7, 1, 'Miguel Alvarez', 'CC-10010007', 'miguel.alvarez@example.com', '+57 310 100 0007'),
    (8, 1, 'Diana Moreno', 'CC-10010008', 'diana.moreno@example.com', '+57 310 100 0008');

INSERT INTO policies (
    id,
    client_id,
    policy_number,
    insurance_type,
    insurer,
    expiration_date,
    renewal_status,
    renewed_at
)
VALUES
    -- Proxima a vencer: vence dentro de los proximos 30 dias.
    (1, 1, 'POL-AUTO-0001', 'Auto', 'Seguros Andina', date('now', '+7 days'), 'pending', NULL),
    (2, 2, 'POL-HOGAR-0002', 'Hogar', 'Proteccion Nacional', date('now', '+28 days'), 'pending', NULL),

    -- Ventana critica: vencio entre 1 y 30 dias atras.
    (3, 3, 'POL-AUTO-0003', 'Auto', 'Seguros Andina', date('now', '-1 day'), 'pending', NULL),
    (4, 4, 'POL-VIDA-0004', 'Vida', 'Vida Plena', date('now', '-15 days'), 'pending', NULL),

    -- Nueva contratacion: vencio hace mas de 30 dias.
    (5, 5, 'POL-MOTO-0005', 'Moto', 'Ruta Segura', date('now', '-31 days'), 'pending', NULL),
    (6, 6, 'POL-SALUD-0006', 'Salud', 'Salud Total', date('now', '-60 days'), 'pending', NULL),

    -- Renovada: no requiere gestion, aunque tenga fecha historica o nueva vigencia.
    (7, 7, 'POL-AUTO-0007', 'Auto', 'Seguros Andina', date('now', '+365 days'), 'renewed', datetime('now', '-3 days')),
    (8, 8, 'POL-HOGAR-0008', 'Hogar', 'Proteccion Nacional', date('now', '+330 days'), 'renewed', datetime('now', '-10 days'));
