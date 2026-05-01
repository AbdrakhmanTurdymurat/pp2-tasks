from pathlib import Path

ROOT = Path(__file__).resolve().parent

DB_CONFIG = {
    "host": "localhost",
    "database": "postgres",
    "user": "postgres",
    "password": "1234",
    "port": "5432",
}

SCHEMA_FILE = ROOT / "schema.sql"
PROCEDURES_FILE = ROOT / "procedures.sql"
SAMPLE_CSV_FILE = ROOT / "contacts.csv"

PAGE_SIZE = 5

GROUPS = ("Family", "Work", "Friend", "Other")
PHONE_TYPES = ("home", "work", "mobile")
SORT_FIELDS = ("name", "birthday", "created_at")
