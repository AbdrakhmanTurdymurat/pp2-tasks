import csv
import sys
from connect import get_connection, create_table


def insert_from_csv(filepath):
    sql = """
        INSERT INTO contacts (username, phone)
        VALUES (%s, %s)
        ON CONFLICT (username) DO NOTHING;
    """
    conn = get_connection()
    inserted = 0
    skipped = 0
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [(row["username"].strip(), row["phone"].strip()) for row in reader]
        with conn:
            with conn.cursor() as cur:
                for username, phone in rows:
                    cur.execute(sql, (username, phone))
                    if cur.rowcount:
                        inserted += 1
                    else:
                        skipped += 1
        print(f"[OK] CSV import done — inserted: {inserted}, skipped: {skipped}")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {filepath}")
    except Exception as e:
        print(f"[ERROR] CSV import failed: {e}")
    finally:
        conn.close()


def insert_from_console():
    username = input("  Enter username : ").strip()
    phone    = input("  Enter phone    : ").strip()
    if not username or not phone:
        print("[ERROR] Username and phone cannot be empty.")
        return
    sql = """
        INSERT INTO contacts (username, phone)
        VALUES (%s, %s)
        ON CONFLICT (username) DO NOTHING;
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (username, phone))
                if cur.rowcount:
                    print(f"[OK] Contact '{username}' added.")
                else:
                    print(f"[SKIP] Username '{username}' already exists.")
    except Exception as e:
        print(f"[ERROR] Insert failed: {e}")
    finally:
        conn.close()


def _print_rows(rows):
    if not rows:
        print("  (no results)")
        return
    print(f"  {'ID':<6} {'USERNAME':<25} {'PHONE':<20}")
    print("  " + "-" * 53)
    for row in rows:
        print(f"  {row[0]:<6} {row[1]:<25} {row[2]:<20}")


def search_by_name(pattern):
    sql = "SELECT id, username, phone FROM contacts WHERE username ILIKE %s ORDER BY username;"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{pattern}%",))
            rows = cur.fetchall()
        print(f"\n  Results for username ~ '{pattern}':")
        _print_rows(rows)
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
    finally:
        conn.close()


def search_by_phone_prefix(prefix):
    sql = "SELECT id, username, phone FROM contacts WHERE phone LIKE %s ORDER BY username;"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"{prefix}%",))
            rows = cur.fetchall()
        print(f"\n  Results for phone prefix '{prefix}':")
        _print_rows(rows)
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
    finally:
        conn.close()


def show_all():
    sql = "SELECT id, username, phone FROM contacts ORDER BY username;"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        print(f"\n  All contacts ({len(rows)} total):")
        _print_rows(rows)
    except Exception as e:
        print(f"[ERROR] Could not fetch contacts: {e}")
    finally:
        conn.close()


def update_phone_by_username():
    username  = input("  Enter username to update : ").strip()
    new_phone = input("  Enter new phone number   : ").strip()
    if not username or not new_phone:
        print("[ERROR] Fields cannot be empty.")
        return
    sql = "UPDATE contacts SET phone = %s WHERE username = %s;"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (new_phone, username))
                if cur.rowcount:
                    print(f"[OK] Phone updated for '{username}'.")
                else:
                    print(f"[WARN] No contact with username '{username}' found.")
    except Exception as e:
        print(f"[ERROR] Update failed: {e}")
    finally:
        conn.close()


def update_username_by_phone():
    phone        = input("  Enter phone to look up    : ").strip()
    new_username = input("  Enter new username        : ").strip()
    if not phone or not new_username:
        print("[ERROR] Fields cannot be empty.")
        return
    sql = "UPDATE contacts SET username = %s WHERE phone = %s;"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (new_username, phone))
                if cur.rowcount:
                    print(f"[OK] Username updated for phone '{phone}'.")
                else:
                    print(f"[WARN] No contact with phone '{phone}' found.")
    except Exception as e:
        print(f"[ERROR] Update failed: {e}")
    finally:
        conn.close()


def delete_by_username():
    username = input("  Enter username to delete : ").strip()
    if not username:
        print("[ERROR] Username cannot be empty.")
        return
    confirm = input(f"  Delete '{username}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return
    sql = "DELETE FROM contacts WHERE username = %s;"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (username,))
                if cur.rowcount:
                    print(f"[OK] Contact '{username}' deleted.")
                else:
                    print(f"[WARN] No contact with username '{username}' found.")
    except Exception as e:
        print(f"[ERROR] Delete failed: {e}")
    finally:
        conn.close()


def delete_by_phone():
    phone = input("  Enter phone to delete : ").strip()
    if not phone:
        print("[ERROR] Phone cannot be empty.")
        return
    confirm = input(f"  Delete contact with phone '{phone}'? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return
    sql = "DELETE FROM contacts WHERE phone = %s;"
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (phone,))
                if cur.rowcount:
                    print(f"[OK] Contact with phone '{phone}' deleted.")
                else:
                    print(f"[WARN] No contact with phone '{phone}' found.")
    except Exception as e:
        print(f"[ERROR] Delete failed: {e}")
    finally:
        conn.close()


MENU = """
╔══════════════════════════════════════╗
║        PhoneBook — Main Menu         ║
╠══════════════════════════════════════╣
║  1. Show all contacts                ║
║  2. Search by name                   ║
║  3. Search by phone prefix           ║
║  4. Add contact (console)            ║
║  5. Import contacts from CSV         ║
║  6. Update phone (by username)       ║
║  7. Update username (by phone)       ║
║  8. Delete contact (by username)     ║
║  9. Delete contact (by phone)        ║
║  0. Exit                             ║
╚══════════════════════════════════════╝
"""


def main():
    create_table()
    while True:
        print(MENU)
        choice = input("  Your choice: ").strip()
        if choice == "1":
            show_all()
        elif choice == "2":
            pattern = input("  Enter name (or part of name): ").strip()
            search_by_name(pattern)
        elif choice == "3":
            prefix = input("  Enter phone prefix: ").strip()
            search_by_phone_prefix(prefix)
        elif choice == "4":
            insert_from_console()
        elif choice == "5":
            filepath = input("  Enter CSV file path [contacts.csv]: ").strip()
            if not filepath:
                filepath = "contacts.csv"
            insert_from_csv(filepath)
        elif choice == "6":
            update_phone_by_username()
        elif choice == "7":
            update_username_by_phone()
        elif choice == "8":
            delete_by_username()
        elif choice == "9":
            delete_by_phone()
        elif choice == "0":
            print("  Goodbye!")
            sys.exit(0)
        else:
            print("  [WARN] Invalid choice.")


if __name__ == "__main__":
    main()
