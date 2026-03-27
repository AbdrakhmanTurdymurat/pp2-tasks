import psycopg2
from config import DB_CONFIG


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def create_table():
    sql = """
        CREATE TABLE IF NOT EXISTS contacts (
            id        SERIAL PRIMARY KEY,
            username  VARCHAR(100) NOT NULL UNIQUE,
            phone     VARCHAR(20)  NOT NULL
        );
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        print("[OK] Table 'contacts' is ready.")
    except Exception as e:
        print(f"[ERROR] Could not create table: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        conn = get_connection()
        print(f"[OK] Connected to PostgreSQL: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
        conn.close()
        create_table()
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
