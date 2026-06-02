from datetime import date, datetime
import os

from flask import Flask, jsonify, request

import db


VALID_CONTACT_CHANNELS = {"call", "email", "message"}


def create_app(database_path=None):
    app = Flask(__name__)
    database_path = database_path or os.environ.get(
        "AGENTEMOTOR_DATABASE_PATH",
        db.DATABASE_PATH,
    )
    db.initialize_schema(database_path)

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
                clients.id AS client_id,
                clients.full_name AS client_name,
                clients.email AS client_email,
                clients.phone AS client_phone,
                advisors.id AS advisor_id,
                advisors.name AS advisor_name
            FROM policies
            JOIN clients ON clients.id = policies.client_id
            JOIN advisors ON advisors.id = clients.advisor_id
            ORDER BY date(policies.expiration_date) ASC, policies.id ASC
            """,
            db_path=database_path,
        )

        dashboard_policies = [build_policy_response(policy) for policy in policies]
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
        return jsonify({"policy": build_policy_response(renewed_policy)})

    return app


def build_policy_response(policy):
    priority = classify_policy(
        policy["expiration_date"],
        policy["renewal_status"],
    )
    return {
        "id": policy["id"],
        "policy_number": policy["policy_number"],
        "insurance_type": policy["insurance_type"],
        "insurer": policy["insurer"],
        "expiration_date": policy["expiration_date"],
        "renewal_status": policy["renewal_status"],
        "renewed_at": policy["renewed_at"],
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
    }


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
