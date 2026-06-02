from datetime import date, datetime
import os

from flask import Flask, jsonify, request, render_template

import db


VALID_CONTACT_CHANNELS = {"call", "email", "message"}
DEFAULT_ADVISOR_ID = 1


def create_app(database_path=None):
    app = Flask(__name__)
    database_path = database_path or os.environ.get(
        "AGENTEMOTOR_DATABASE_PATH",
        db.DATABASE_PATH,
    )
    db.initialize_schema(database_path)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/dashboard")
    def get_dashboard():
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

        dashboard_policies = [build_policy_response(policy, database_path=database_path) for policy in policies]
        return jsonify(
            {
                "summary": build_dashboard_summary(dashboard_policies),
                "policies": dashboard_policies,
            }
        )

    @app.post("/api/contact-attempts")
    def create_contact_attempt():
        payload = request.get_json(silent=True) or {}
        error = validate_contact_attempt_payload(payload)
        if error:
            return jsonify({"error": error}), 400

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

        contact_attempt = db.fetch_one(
            "SELECT * FROM contact_attempts WHERE id = ?",
            (result["lastrowid"],),
            db_path=database_path,
        )
        return jsonify({"contact_attempt": contact_attempt}), 201

    @app.post("/api/policies")
    def create_policy():
        payload = request.get_json(silent=True) or {}
        error = validate_policy_payload(payload, require_all=True)
        if error:
            return jsonify({"error": error}), 400

        advisor = db.fetch_one(
            "SELECT id FROM advisors WHERE id = ?",
            (DEFAULT_ADVISOR_ID,),
            db_path=database_path,
        )
        if advisor is None:
            return jsonify({"error": "Default advisor not found"}), 400

        client_payload = payload["client"]
        policy_payload = payload["policy"]

        existing_policy = db.fetch_one(
            "SELECT id FROM policies WHERE policy_number = ?",
            (policy_payload["policy_number"],),
            db_path=database_path,
        )
        if existing_policy is not None:
            return jsonify({"error": "policy_number already exists"}), 400

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
                        DEFAULT_ADVISOR_ID,
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

        created_policy = get_policy_response(
            transaction_results[-1]["lastrowid"],
            database_path,
        )
        return jsonify({"policy": created_policy}), 201

    @app.put("/api/policies/<int:policy_id>")
    def update_policy(policy_id):
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

        if policy_payload:
            if policy_payload.get("policy_number"):
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

        updated_policy = get_policy_response(policy_id, database_path)
        return jsonify({"policy": updated_policy})

    @app.patch("/api/policies/<int:policy_id>/archive")
    def archive_policy(policy_id):
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


def classify_policy(expiration_date, renewal_status):
    if renewal_status == "renewed":
        return "renovada"

    days_until_expiration = (
        datetime.strptime(expiration_date, "%Y-%m-%d").date() - date.today()
    ).days

    if 0 <= days_until_expiration <= 30:
        return "proxima_a_vencer"
    if -30 <= days_until_expiration <= -1:
        return "ventana_critica"
    if days_until_expiration < -30:
        return "nueva_contratacion"
    return "sin_prioridad"


def build_dashboard_summary(policies):
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
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    return True


def is_valid_datetime(value):
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
