"""
==============================================================================
Agentemotor - Flask REST API Core
==============================================================================
Este archivo implementa el servidor web REST API utilizando el micro-framework
Flask. Actúa como la única capa de abstracción autorizada para realizar operaciones
de lectura y escritura contra la base de datos SQLite (única fuente de verdad).

Reglas de Negocio Implementadas:
1. Clasificación Automática de Prioridades:
   - "renovada": Si la póliza tiene un estado de renovación "renewed".
   - "proxima_a_vencer": Pólizas pendientes que vencen en los próximos 30 días.
   - "ventana_critica": Pólizas pendientes vencidas hace entre 1 y 30 días.
   - "nueva_contratacion": Pólizas pendientes vencidas hace más de 30 días.
   - "sin_prioridad": Pólizas pendientes que vencen en más de 30 días en el futuro.
2. Trazabilidad de Interacciones:
   - Registro de intentos de contacto (Llamada, Correo, Mensaje) guardados
     directamente en la tabla relacional "contact_attempts".
3. Archivación Lógica:
   - Actualiza "archived_at" con la fecha actual, excluyéndose automáticamente
     del dashboard sin destruir registros físicos.
"""

from datetime import date, datetime, timezone
import os
import sqlite3

from flask import Flask, jsonify, request, render_template

import db


# Canales de comunicación válidos y admitidos por la base de datos
VALID_CONTACT_CHANNELS = {"call", "email", "message"}

# Datos del Asesor de Demostración por defecto para inicialización
DEMO_ADVISOR = {
    "name": "Maria Gonzalez",
    "email": "maria.gonzalez@agentemotor.test",
    "phone": "+57 300 111 2233",
}


def create_app(database_path=None):
    """
    Fábrica de Aplicaciones Flask (Application Factory).
    Configura e inicializa la aplicación, la base de datos y define las rutas HTTP.
    """
    app = Flask(__name__)
    
    # Determina la ruta física de SQLite desde el entorno o usa el valor por defecto
    database_path = database_path or os.environ.get(
        "AGENTEMOTOR_DATABASE_PATH",
        db.DATABASE_PATH,
    )
    
    # Crea el esquema de base de datos si no existe al arrancar el servidor
    db.initialize_schema(database_path)

    @app.get("/")
    def index():
        """
        GET /
        Sirve la interfaz principal Single Page Application (SPA) para el usuario.
        """
        return render_template("index.html")

    @app.get("/api/dashboard")
    def get_dashboard():
        """
        GET /api/dashboard
        Retorna las métricas consolidadas (summary) y el listado de pólizas vigentes
        y pendientes no archivadas clasificadas por prioridad de negocio.
        """
        # Ejecuta la consulta SQL relacional uniendo pólizas, clientes y asesores
        policies = db.fetch_all(
            """
            SELECT
                policies.id,
                policies.policy_number,
                policies.insurance_type,
                policies.insurer,
                policies.expiration_date,
                policies.renewal_status,
                policies.renewed_at,
                policies.archived_at,
                clients.id AS client_id,
                clients.full_name AS client_name,
                clients.document_number AS client_document,
                clients.email AS client_email,
                clients.phone AS client_phone,
                advisors.id AS advisor_id,
                advisors.name AS advisor_name
            FROM policies
            JOIN clients ON clients.id = policies.client_id
            JOIN advisors ON advisors.id = clients.advisor_id
            WHERE policies.archived_at IS NULL
            ORDER BY date(policies.expiration_date) ASC, policies.id ASC
            """,
            db_path=database_path,
        )

        # Genera el JSON estructurado mapeando cada póliza y adjuntando su historial
        dashboard_policies = [build_policy_response(policy, database_path=database_path) for policy in policies]
        return jsonify(
            {
                "summary": build_dashboard_summary(dashboard_policies),
                "policies": dashboard_policies,
            }
        )

    @app.post("/api/contact-attempts")
    def create_contact_attempt():
        """
        POST /api/contact-attempts
        Registra una interacción de contacto realizada con el cliente asociado a una póliza.
        JSON Payload:
        {
          "policy_id": int,
          "channel": "call" | "email" | "message",
          "result": str,
          "notes": str (opcional),
          "attempted_at": "YYYY-MM-DDTHH:MM:SS" (opcional)
        }
        """
        payload = request.get_json(silent=True) or {}
        error = validate_contact_attempt_payload(payload)
        if error:
            return jsonify({"error": error}), 400

        # Recupera datos relacionales de cliente y asesor derivados de la póliza
        policy = db.fetch_one(
            """
            SELECT
                policies.id AS policy_id,
                clients.id AS client_id,
                clients.advisor_id AS advisor_id
            FROM policies
            JOIN clients ON clients.id = policies.client_id
            WHERE policies.id = ?
            """,
            (payload["policy_id"],),
            db_path=database_path,
        )
        if policy is None:
            return jsonify({"error": "Policy not found"}), 404

        attempted_at = payload.get("attempted_at")
        if attempted_at and not is_valid_datetime(attempted_at):
            return jsonify({"error": "attempted_at must be a valid ISO datetime"}), 400

        # Inserta el registro en SQLite usando el timestamp provisto o el DEFAULT actual
        if attempted_at:
            result = db.execute_query(
                """
                INSERT INTO contact_attempts (
                    policy_id,
                    client_id,
                    advisor_id,
                    channel,
                    result,
                    notes,
                    attempted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy["policy_id"],
                    policy["client_id"],
                    policy["advisor_id"],
                    payload["channel"],
                    payload["result"],
                    payload.get("notes"),
                    attempted_at,
                ),
                db_path=database_path,
            )
        else:
            result = db.execute_query(
                """
                INSERT INTO contact_attempts (
                    policy_id,
                    client_id,
                    advisor_id,
                    channel,
                    result,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    policy["policy_id"],
                    policy["client_id"],
                    policy["advisor_id"],
                    payload["channel"],
                    payload["result"],
                    payload.get("notes"),
                ),
                db_path=database_path,
            )

        # Retorna el registro creado directamente desde la base de datos
        contact_attempt = db.fetch_one(
            "SELECT * FROM contact_attempts WHERE id = ?",
            (result["lastrowid"],),
            db_path=database_path,
        )
        return jsonify({"contact_attempt": contact_attempt}), 201

    @app.post("/api/policies")
    def create_policy():
        """
        POST /api/policies
        Crea un nuevo Cliente y le asocia una Póliza de seguro bajo una transacción ACID.
        JSON Payload:
        {
          "client": {
            "full_name": str,
            "document_number": str (opcional),
            "email": str (opcional),
            "phone": str (opcional)
          },
          "policy": {
            "policy_number": str,
            "insurance_type": str,
            "insurer": str (opcional),
            "expiration_date": "YYYY-MM-DD"
          }
        }
        """
        payload = request.get_json(silent=True) or {}
        error = validate_policy_payload(payload, require_all=True)
        if error:
            return jsonify({"error": error}), 400

        # Obtiene el asesor responsable por defecto de la cartera
        advisor = get_or_create_advisor(database_path)
        client_payload = payload["client"]
        policy_payload = payload["policy"]

        try:
            # Ejecuta la transacción de inserción para garantizar atomicidad e integridad
            transaction_results = db.execute_transaction(
                [
                    (
                        """
                        INSERT INTO clients (
                            advisor_id,
                            full_name,
                            document_number,
                            email,
                            phone
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            advisor["id"],
                            client_payload["full_name"],
                            client_payload.get("document_number"),
                            client_payload.get("email"),
                            client_payload.get("phone"),
                        ),
                    ),
                    (
                        """
                        INSERT INTO policies (
                            client_id,
                            policy_number,
                            insurance_type,
                            insurer,
                            expiration_date
                        )
                        VALUES (last_insert_rowid(), ?, ?, ?, ?)
                        """,
                        (
                            policy_payload["policy_number"],
                            policy_payload["insurance_type"],
                            policy_payload.get("insurer"),
                            policy_payload["expiration_date"],
                        ),
                    ),
                ],
                db_path=database_path,
            )
        except sqlite3.IntegrityError as error:
            # Controla violaciones de restricciones UNIQUE de números de documento o pólizas
            return handle_policy_creation_integrity_error(error)

        # Recupera el objeto creado completo para retornar al cliente
        created_policy = get_policy_response(
            transaction_results[-1]["lastrowid"],
            database_path,
        )
        return jsonify({"policy": created_policy}), 201

    @app.put("/api/policies/<int:policy_id>")
    def update_policy(policy_id):
        """
        PUT /api/policies/<int:policy_id>
        Modifica los campos del Cliente y/o la Póliza utilizando lógica COALESCE de SQLite.
        JSON Payload:
        {
          "client": { ... campos opcionales ... },
          "policy": { ... campos opcionales ... }
        }
        """
        payload = request.get_json(silent=True) or {}
        error = validate_policy_payload(payload, require_all=False)
        if error:
            return jsonify({"error": error}), 400

        current_policy = db.fetch_one(
            "SELECT id, client_id FROM policies WHERE id = ?",
            (policy_id,),
            db_path=database_path,
        )
        if current_policy is None:
            return jsonify({"error": "Policy not found"}), 404

        client_payload = payload.get("client") or {}
        policy_payload = payload.get("policy") or {}

        # 1. Actualiza el Cliente asociado si el payload lo incluye
        if client_payload:
            db.execute_query(
                """
                UPDATE clients
                SET
                    full_name = COALESCE(?, full_name),
                    document_number = COALESCE(?, document_number),
                    email = COALESCE(?, email),
                    phone = COALESCE(?, phone),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    client_payload.get("full_name"),
                    client_payload.get("document_number"),
                    client_payload.get("email"),
                    client_payload.get("phone"),
                    current_policy["client_id"],
                ),
                db_path=database_path,
            )

        # 2. Actualiza los detalles de la póliza si el payload los incluye
        if policy_payload:
            if policy_payload.get("policy_number"):
                # Valida que el número de póliza no pertenezca a otra póliza existente
                existing_policy = db.fetch_one(
                    "SELECT id FROM policies WHERE policy_number = ? AND id <> ?",
                    (policy_payload["policy_number"], policy_id),
                    db_path=database_path,
                )
                if existing_policy is not None:
                    return jsonify({"error": "policy_number already exists"}), 400

            db.execute_query(
                """
                UPDATE policies
                SET
                    policy_number = COALESCE(?, policy_number),
                    insurance_type = COALESCE(?, insurance_type),
                    insurer = COALESCE(?, insurer),
                    expiration_date = COALESCE(?, expiration_date),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    policy_payload.get("policy_number"),
                    policy_payload.get("insurance_type"),
                    policy_payload.get("insurer"),
                    policy_payload.get("expiration_date"),
                    policy_id,
                ),
                db_path=database_path,
            )

        # Retorna el objeto actualizado completo
        updated_policy = get_policy_response(policy_id, database_path)
        return jsonify({"policy": updated_policy})

    @app.patch("/api/policies/<int:policy_id>/archive")
    def archive_policy(policy_id):
        """
        PATCH /api/policies/<int:policy_id>/archive
        Archiva lógicamente una póliza (asigna archived_at) para excluirla de las alertas del dashboard
        sin destruir físicamente los datos históricos.
        """
        policy = db.fetch_one(
            "SELECT id FROM policies WHERE id = ?",
            (policy_id,),
            db_path=database_path,
        )
        if policy is None:
            return jsonify({"error": "Policy not found"}), 404

        db.execute_query(
            """
            UPDATE policies
            SET
                archived_at = COALESCE(archived_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (policy_id,),
            db_path=database_path,
        )

        archived_policy = get_policy_response(policy_id, database_path)
        return jsonify({"policy": archived_policy})

    @app.post("/api/policies/<int:policy_id>/renew")
    def renew_policy(policy_id):
        """
        POST /api/policies/<int:policy_id>/renew
        Renueva una póliza comercialmente. Actualiza la fecha de vencimiento acordada,
        marca su renewal_status en 'renewed' e inactiva las gestiones prioritarias comerciales.
        JSON Payload:
        {
          "expiration_date": "YYYY-MM-DD"
        }
        """
        payload = request.get_json(silent=True) or {}
        new_expiration_date = payload.get("expiration_date")
        if not new_expiration_date:
            return jsonify({"error": "expiration_date is required"}), 400
        if not is_valid_date(new_expiration_date):
            return jsonify({"error": "expiration_date must be a valid ISO date"}), 400

        policy = db.fetch_one(
            "SELECT id FROM policies WHERE id = ?",
            (policy_id,),
            db_path=database_path,
        )
        if policy is None:
            return jsonify({"error": "Policy not found"}), 404

        # Actualiza el estado y fecha de renovación en SQLite
        db.execute_query(
            """
            UPDATE policies
            SET
                expiration_date = ?,
                renewal_status = 'renewed',
                renewed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_expiration_date, policy_id),
            db_path=database_path,
        )

        # Recupera el registro modificado con todos los datos y su historial de intentos
        renewed_policy = db.fetch_one(
            """
            SELECT
                policies.id,
                policies.policy_number,
                policies.insurance_type,
                policies.insurer,
                policies.expiration_date,
                policies.renewal_status,
                policies.renewed_at,
                policies.archived_at,
                clients.id AS client_id,
                clients.full_name AS client_name,
                clients.document_number AS client_document,
                clients.email AS client_email,
                clients.phone AS client_phone,
                advisors.id AS advisor_id,
                advisors.name AS advisor_name
            FROM policies
            JOIN clients ON clients.id = policies.client_id
            JOIN advisors ON advisors.id = clients.advisor_id
            WHERE policies.id = ?
            """,
            (policy_id,),
            db_path=database_path,
        )
        return jsonify({"policy": build_policy_response(renewed_policy, database_path=database_path)})

    return app


def build_policy_response(policy, database_path=None):
    """
    Formatea la póliza y le calcula la prioridad comercial de negocio.
    Adicionalmente, consulta y adjunta cronológicamente su historial de gestiones.
    """
    priority = classify_policy(
        policy["expiration_date"],
        policy["renewal_status"],
    )
    db_path = database_path or db.DATABASE_PATH
    attempts = db.fetch_all(
        "SELECT id, channel, result, notes, attempted_at, created_at FROM contact_attempts WHERE policy_id = ? ORDER BY datetime(attempted_at) DESC",
        (policy["id"],),
        db_path=db_path,
    )
    return {
        "id": policy["id"],
        "policy_number": policy["policy_number"],
        "insurance_type": policy["insurance_type"],
        "insurer": policy["insurer"],
        "expiration_date": policy["expiration_date"],
        "renewal_status": policy["renewal_status"],
        "renewed_at": policy["renewed_at"],
        "archived_at": policy["archived_at"],
        "priority": priority,
        "client": {
            "id": policy["client_id"],
            "full_name": policy["client_name"],
            "document_number": policy["client_document"],
            "email": policy["client_email"],
            "phone": policy["client_phone"],
        },
        "advisor": {
            "id": policy["advisor_id"],
            "name": policy["advisor_name"],
        },
        "contact_attempts": attempts,
    }


def get_policy_response(policy_id, database_path):
    """
    Función auxiliar para recuperar una póliza específica uniendo las tablas
    relacionales por su id único y retornando su payload completo.
    """
    policy = db.fetch_one(
        """
        SELECT
            policies.id,
            policies.policy_number,
            policies.insurance_type,
            policies.insurer,
            policies.expiration_date,
            policies.renewal_status,
            policies.renewed_at,
            policies.archived_at,
            clients.id AS client_id,
            clients.full_name AS client_name,
            clients.document_number AS client_document,
            clients.email AS client_email,
            clients.phone AS client_phone,
            advisors.id AS advisor_id,
            advisors.name AS advisor_name
        FROM policies
        JOIN clients ON clients.id = policies.client_id
        JOIN advisors ON advisors.id = clients.advisor_id
        WHERE policies.id = ?
        """,
        (policy_id,),
        db_path=database_path,
    )
    if policy is None:
        return None
    return build_policy_response(policy, database_path=database_path)


def get_or_create_advisor(database_path):
    """
    Retorna el primer asesor registrado en SQLite o crea el asesor demo
    si la base de datos se encuentra vacía.
    """
    advisor = db.fetch_one(
        "SELECT id, name FROM advisors ORDER BY id ASC LIMIT 1",
        db_path=database_path,
    )
    if advisor is not None:
        return advisor

    result = db.execute_query(
        """
        INSERT INTO advisors (name, email, phone)
        VALUES (?, ?, ?)
        """,
        (
            DEMO_ADVISOR["name"],
            DEMO_ADVISOR["email"],
            DEMO_ADVISOR["phone"],
        ),
        db_path=database_path,
    )
    return db.fetch_one(
        "SELECT id, name FROM advisors WHERE id = ?",
        (result["lastrowid"],),
        db_path=database_path,
    )


def handle_policy_creation_integrity_error(error):
    """
    Mapeador amigable de errores de integridad relacional (UNIQUE constraints).
    Traduce las excepciones crudas de SQLite a respuestas JSON legibles con código 400.
    """
    message = str(error)
    if "clients.document_number" in message:
        return jsonify({"error": "Ya existe un cliente con ese documento."}), 400
    if "policies.policy_number" in message:
        return jsonify({"error": "Ya existe una póliza con ese número."}), 400
    return jsonify({"error": "No se pudo crear la póliza."}), 400


def classify_policy(expiration_date, renewal_status):
    """
    Clasificador de Prioridades (Regla de Negocio Core).
    Calcula dinámicamente la prioridad operativa de una póliza en base a la
    fecha actual (en UTC para mantener consistencia con SQLite) y la diferencia
    en días frente a su fecha de vencimiento.
    """
    if renewal_status == "renewed":
        return "renovada"

    days_until_expiration = (
        datetime.strptime(expiration_date, "%Y-%m-%d").date() - datetime.now(timezone.utc).date()
    ).days

    if 0 <= days_until_expiration <= 30:
        return "proxima_a_vencer"
    if -30 <= days_until_expiration <= -1:
        return "ventana_critica"
    if days_until_expiration < -30:
        return "nueva_contratacion"
    return "sin_prioridad"


def build_dashboard_summary(policies):
    """
    Construye las estadísticas cuantitativas del dashboard agrupándolas
    según su clasificación de prioridad para consumo de las tarjetas KPIs.
    """
    summary = {
        "total": len(policies),
        "proxima_a_vencer": 0,
        "ventana_critica": 0,
        "nueva_contratacion": 0,
        "renovada": 0,
        "sin_prioridad": 0,
    }
    for policy in policies:
        summary[policy["priority"]] += 1
    return summary


def validate_contact_attempt_payload(payload):
    """Validador de entrada para el registro de gestiones comerciales."""
    if not payload.get("policy_id"):
        return "policy_id is required"
    if not isinstance(payload["policy_id"], int):
        return "policy_id must be an integer"
    if payload.get("channel") not in VALID_CONTACT_CHANNELS:
        return "channel must be one of: call, email, message"
    if not payload.get("result"):
        return "result is required"
    return None


def validate_policy_payload(payload, require_all):
    """Validador de entrada flexible para la creación y edición de pólizas y clientes."""
    client_payload = payload.get("client")
    policy_payload = payload.get("policy")

    if require_all:
        if not isinstance(client_payload, dict):
            return "client is required"
        if not isinstance(policy_payload, dict):
            return "policy is required"
        if not client_payload.get("full_name"):
            return "client.full_name is required"
        if not policy_payload.get("policy_number"):
            return "policy.policy_number is required"
        if not policy_payload.get("insurance_type"):
            return "policy.insurance_type is required"
        if not policy_payload.get("expiration_date"):
            return "policy.expiration_date is required"
    else:
        if client_payload is None and policy_payload is None:
            return "client or policy is required"
        if client_payload is not None and not isinstance(client_payload, dict):
            return "client must be an object"
        if policy_payload is not None and not isinstance(policy_payload, dict):
            return "policy must be an object"

    if policy_payload and policy_payload.get("expiration_date"):
        if not is_valid_date(policy_payload["expiration_date"]):
            return "policy.expiration_date must be a valid ISO date"

    return None


def is_valid_date(value):
    """Validador auxiliar de fechas simples en formato ISO YYYY-MM-DD."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    return True


def is_valid_datetime(value):
    """Validador auxiliar de fechas-horas completas en formato ISO YYYY-MM-DDTHH:MM:SS."""
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


# Instancia de aplicación Flask lista para ejecución
app = create_app()


# Punto de arranque principal para ejecución directa
if __name__ == "__main__":
    app.run(debug=False)
