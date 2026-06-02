from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.sqlite"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_PATH = BASE_DIR / "seed.sql"


def dict_factory(cursor, row):
    """Return SQLite rows as plain dictionaries."""
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


def get_db_connection(db_path=DATABASE_PATH):
    """Create a SQLite connection configured as the system source of truth."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = dict_factory
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def read_sql_file(path):
    """Read a SQL file from disk."""
    return Path(path).read_text(encoding="utf-8")


def execute_script(script_path, db_path=DATABASE_PATH):
    """Execute a SQL script inside a single SQLite transaction."""
    connection = get_db_connection(db_path)
    try:
        connection.executescript(read_sql_file(script_path))
        connection.commit()
    finally:
        connection.close()


def initialize_schema(db_path=DATABASE_PATH):
    """Create the database structure defined in schema.sql."""
    execute_script(SCHEMA_PATH, db_path)
    ensure_policy_archive_column(db_path)


def ensure_policy_archive_column(db_path=DATABASE_PATH):
    """Keep existing SQLite databases compatible with the current schema."""
    connection = get_db_connection(db_path)
    try:
        columns = [
            column["name"]
            for column in connection.execute("PRAGMA table_info(policies)").fetchall()
        ]
        if "archived_at" not in columns:
            connection.execute("ALTER TABLE policies ADD COLUMN archived_at TEXT")
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_policies_archived_at
                ON policies(archived_at)
            """
        )
        connection.commit()
    finally:
        connection.close()


def load_seed(db_path=DATABASE_PATH):
    """Load development seed data defined in seed.sql."""
    execute_script(SEED_PATH, db_path)


def initialize_database(db_path=DATABASE_PATH, with_seed=False):
    """Initialize schema and optionally load seed data."""
    initialize_schema(db_path)
    if with_seed:
        load_seed(db_path)


def fetch_one(query, params=None, db_path=DATABASE_PATH):
    """Run a read query and return one row as a dictionary or None."""
    connection = get_db_connection(db_path)
    try:
        cursor = connection.execute(query, params or ())
        return cursor.fetchone()
    finally:
        connection.close()


def fetch_all(query, params=None, db_path=DATABASE_PATH):
    """Run a read query and return all rows as dictionaries."""
    connection = get_db_connection(db_path)
    try:
        cursor = connection.execute(query, params or ())
        return cursor.fetchall()
    finally:
        connection.close()


def execute_query(query, params=None, db_path=DATABASE_PATH):
    """Run a write query and return basic execution metadata."""
    connection = get_db_connection(db_path)
    try:
        cursor = connection.execute(query, params or ())
        connection.commit()
        return {
            "lastrowid": cursor.lastrowid,
            "rowcount": cursor.rowcount,
        }
    finally:
        connection.close()


def execute_transaction(operations, db_path=DATABASE_PATH):
    """Run multiple write queries in one SQLite transaction."""
    connection = get_db_connection(db_path)
    results = []
    try:
        for query, params in operations:
            cursor = connection.execute(query, params or ())
            results.append(
                {
                    "lastrowid": cursor.lastrowid,
                    "rowcount": cursor.rowcount,
                }
            )
        connection.commit()
        return results
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
