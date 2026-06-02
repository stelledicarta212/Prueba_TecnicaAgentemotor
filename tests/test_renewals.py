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


def teardown_module():
    Path(TEST_DATABASE_PATH).unlink(missing_ok=True)
