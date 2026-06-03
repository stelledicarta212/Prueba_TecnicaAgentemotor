PRAGMA foreign_keys = ON;

-- Advisors: responsable comercial de la cartera.
CREATE TABLE IF NOT EXISTS advisors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Clients: datos del cliente vinculados a un asesor.
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advisor_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    document_number TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (advisor_id) REFERENCES advisors(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Policies: polizas activas o renovadas, con soporte de archivado logico.
CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    policy_number TEXT NOT NULL UNIQUE,
    insurance_type TEXT NOT NULL,
    insurer TEXT,
    expiration_date TEXT NOT NULL,
    renewal_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (renewal_status IN ('pending', 'renewed')),
    renewed_at TEXT,
    archived_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (date(expiration_date) IS NOT NULL),
    CHECK (renewed_at IS NULL OR datetime(renewed_at) IS NOT NULL),
    CHECK (archived_at IS NULL OR datetime(archived_at) IS NOT NULL),
    CHECK (
        (renewal_status = 'pending' AND renewed_at IS NULL)
        OR (renewal_status = 'renewed' AND renewed_at IS NOT NULL)
    ),
    FOREIGN KEY (client_id) REFERENCES clients(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Contact attempts: historial comercial asociado a cada poliza.
CREATE TABLE IF NOT EXISTS contact_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    advisor_id INTEGER NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('call', 'email', 'message')),
    result TEXT NOT NULL,
    notes TEXT,
    attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (datetime(attempted_at) IS NOT NULL),
    FOREIGN KEY (policy_id) REFERENCES policies(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES clients(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (advisor_id) REFERENCES advisors(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Indexes: aceleran joins y filtros frecuentes del dashboard/API.
CREATE INDEX IF NOT EXISTS idx_clients_advisor_id
    ON clients(advisor_id);

CREATE INDEX IF NOT EXISTS idx_policies_client_id
    ON policies(client_id);

CREATE INDEX IF NOT EXISTS idx_policies_expiration_date
    ON policies(expiration_date);

CREATE INDEX IF NOT EXISTS idx_policies_renewal_status
    ON policies(renewal_status);

CREATE INDEX IF NOT EXISTS idx_policies_archived_at
    ON policies(archived_at);

CREATE INDEX IF NOT EXISTS idx_contact_attempts_policy_id
    ON contact_attempts(policy_id);

CREATE INDEX IF NOT EXISTS idx_contact_attempts_client_id
    ON contact_attempts(client_id);

CREATE INDEX IF NOT EXISTS idx_contact_attempts_advisor_id
    ON contact_attempts(advisor_id);
