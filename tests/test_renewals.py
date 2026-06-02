import os
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

TEST_DATABASE_FD, TEST_DATABASE_PATH = tempfile.mkstemp(suffix=".sqlite")
os.close(TEST_DATABASE_FD)
os.environ["AGENTEMOTOR_DATABASE_PATH"] = TEST_DATABASE_PATH

import db  # noqa: E402
from app import create_app  # noqa: E402


def create_test_client(tmp_path):
    database_path = tmp_path / "renewals.sqlite"
    db.initialize_database(database_path, with_seed=True)
    app = create_app(database_path=database_path)
    app.config["TESTING"] = True
    return app.test_client(), database_path


def find_policy_by_number(response_json, policy_number):
    return next(
        policy
        for policy in response_json["policies"]
        if policy["policy_number"] == policy_number
    )


def test_policy_expired_between_one_and_thirty_days_is_critical_window(tmp_path):
    client, _database_path = create_test_client(tmp_path)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    policy = find_policy_by_number(response.get_json(), "POL-AUTO-0003")
    assert policy["priority"] == "ventana_critica"
    assert policy["renewal_status"] == "pending"


def test_policy_expired_more_than_thirty_days_is_new_sale(tmp_path):
    client, _database_path = create_test_client(tmp_path)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    policy = find_policy_by_number(response.get_json(), "POL-MOTO-0005")
    assert policy["priority"] == "nueva_contratacion"
    assert policy["renewal_status"] == "pending"


def test_renew_policy_updates_status_and_returns_renewed_priority(tmp_path):
    client, database_path = create_test_client(tmp_path)

    response = client.post(
        "/api/policies/3/renew",
        json={"expiration_date": "2027-06-02"},
    )

    assert response.status_code == 200
    policy = response.get_json()["policy"]
    assert policy["id"] == 3
    assert policy["expiration_date"] == "2027-06-02"
    assert policy["renewal_status"] == "renewed"
    assert policy["priority"] == "renovada"

    stored_policy = db.fetch_one(
        "SELECT renewal_status, expiration_date, renewed_at FROM policies WHERE id = ?",
        (3,),
        db_path=database_path,
    )
    assert stored_policy["renewal_status"] == "renewed"
    assert stored_policy["expiration_date"] == "2027-06-02"
    assert stored_policy["renewed_at"] is not None


def test_create_policy_creates_client_and_policy(tmp_path):
    client, database_path = create_test_client(tmp_path)

    response = client.post(
        "/api/policies",
        json={
            "client": {
                "full_name": "Natalia Pineda",
                "document_number": "CC-20020009",
                "email": "natalia.pineda@example.com",
                "phone": "+57 310 200 0009",
            },
            "policy": {
                "policy_number": "POL-AUTO-0009",
                "insurance_type": "Auto",
                "insurer": "Seguros Andina",
                "expiration_date": "2027-06-02",
            },
        },
    )

    assert response.status_code == 201
    policy = response.get_json()["policy"]
    assert policy["policy_number"] == "POL-AUTO-0009"
    assert policy["renewal_status"] == "pending"
    assert policy["archived_at"] is None
    assert policy["client"]["full_name"] == "Natalia Pineda"
    assert policy["advisor"]["id"] == 1

    stored_policy = db.fetch_one(
        """
        SELECT
            policies.policy_number,
            policies.insurance_type,
            policies.archived_at,
            clients.full_name AS client_name
        FROM policies
        JOIN clients ON clients.id = policies.client_id
        WHERE policies.id = ?
        """,
        (policy["id"],),
        db_path=database_path,
    )
    assert stored_policy["policy_number"] == "POL-AUTO-0009"
    assert stored_policy["insurance_type"] == "Auto"
    assert stored_policy["archived_at"] is None
    assert stored_policy["client_name"] == "Natalia Pineda"


def test_update_policy_updates_client_and_policy(tmp_path):
    client, database_path = create_test_client(tmp_path)

    response = client.put(
        "/api/policies/1",
        json={
            "client": {
                "full_name": "Carlos Ramirez Actualizado",
                "email": "carlos.actualizado@example.com",
            },
            "policy": {
                "policy_number": "POL-AUTO-0001-EDIT",
                "insurance_type": "Auto Premium",
                "insurer": "Seguros Andina Plus",
                "expiration_date": "2027-07-15",
            },
        },
    )

    assert response.status_code == 200
    policy = response.get_json()["policy"]
    assert policy["policy_number"] == "POL-AUTO-0001-EDIT"
    assert policy["insurance_type"] == "Auto Premium"
    assert policy["insurer"] == "Seguros Andina Plus"
    assert policy["expiration_date"] == "2027-07-15"
    assert policy["client"]["full_name"] == "Carlos Ramirez Actualizado"
    assert policy["client"]["email"] == "carlos.actualizado@example.com"

    stored_policy = db.fetch_one(
        """
        SELECT
            policies.policy_number,
            policies.insurance_type,
            clients.full_name AS client_name,
            clients.email AS client_email
        FROM policies
        JOIN clients ON clients.id = policies.client_id
        WHERE policies.id = ?
        """,
        (1,),
        db_path=database_path,
    )
    assert stored_policy["policy_number"] == "POL-AUTO-0001-EDIT"
    assert stored_policy["insurance_type"] == "Auto Premium"
    assert stored_policy["client_name"] == "Carlos Ramirez Actualizado"
    assert stored_policy["client_email"] == "carlos.actualizado@example.com"


def test_archive_policy_hides_it_from_dashboard_without_deleting(tmp_path):
    client, database_path = create_test_client(tmp_path)

    response = client.patch("/api/policies/1/archive")

    assert response.status_code == 200
    archived_policy = response.get_json()["policy"]
    assert archived_policy["id"] == 1
    assert archived_policy["archived_at"] is not None

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    policy_ids = [policy["id"] for policy in dashboard.get_json()["policies"]]
    assert 1 not in policy_ids

    stored_policy = db.fetch_one(
        "SELECT id, archived_at FROM policies WHERE id = ?",
        (1,),
        db_path=database_path,
    )
    assert stored_policy is not None
    assert stored_policy["archived_at"] is not None


def teardown_module():
    Path(TEST_DATABASE_PATH).unlink(missing_ok=True)
