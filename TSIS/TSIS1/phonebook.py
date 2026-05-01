
import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from connect import get_connection
from config import (
    PAGE_SIZE,
    PHONE_TYPES,
    SAMPLE_CSV_FILE,
    SCHEMA_FILE,
    PROCEDURES_FILE,
    SORT_FIELDS,
)

ROOT = Path(__file__).resolve().parent


# ---------------- ENCODING-SAFE FILE HELPERS ----------------
def read_text_with_fallback(path: Path) -> str:
    encodings = ("utf-8-sig", "utf-8", "cp1251", "latin-1")
    last_error = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error


def write_text_utf8(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


# ---------------- INPUT HELPERS ----------------
def clean(text: Optional[str]) -> str:
    return (text or "").strip()


def prompt(message: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    while True:
        try:
            value = input(f"{message}{suffix}: ").strip()
        except EOFError:
            value = ""
        if value:
            return value
        if default is not None:
            return default
        print("This field cannot be empty.")


def prompt_optional(message: str, default: Optional[str] = None) -> Optional[str]:
    suffix = f" [{default}]" if default not in (None, "") else ""
    try:
        value = input(f"{message}{suffix}: ").strip()
    except EOFError:
        value = ""
    if value:
        return value
    return default


def prompt_yes_no(message: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            value = input(f"{message} [{hint}]: ").strip().lower()
        except EOFError:
            value = ""
        if not value:
            return default
        if value in ("y", "yes", "1"):
            return True
        if value in ("n", "no", "0"):
            return False
        print("Please answer y or n.")


def prompt_choice(message: str, choices: List[str], default: Optional[str] = None) -> str:
    normalized = [c.lower() for c in choices]
    while True:
        suffix = f" ({'/'.join(choices)})"
        if default:
            suffix += f" [{default}]"
        try:
            value = input(f"{message}{suffix}: ").strip().lower()
        except EOFError:
            value = ""
        if not value and default:
            value = default.lower()
        if value in normalized:
            return choices[normalized.index(value)]
        print(f"Choose one of: {', '.join(choices)}")


def normalize_phone_type(value: Optional[str]) -> str:
    value = clean(value).lower() or "mobile"
    if value not in PHONE_TYPES:
        raise ValueError(f"Phone type must be one of: {', '.join(PHONE_TYPES)}")
    return value


def parse_birthday(value: Optional[str]) -> Optional[str]:
    value = clean(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError("Birthday must be in YYYY-MM-DD format") from exc


def ask_phone_block(single: bool = False) -> List[Dict[str, str]]:
    phones: List[Dict[str, str]] = []
    while True:
        phone = prompt("Phone")
        phone_type = prompt_choice("Phone type", list(PHONE_TYPES), default="mobile")
        phones.append({"phone": phone, "type": phone_type})
        if single or not prompt_yes_no("Add another phone?", default=False):
            break
    return phones


def print_rows(rows) -> None:
    if not rows:
        print("No records found.")
        return
    for row in rows:
        print(row)


# ---------------- DB HELPERS ----------------
def fetch_group_id(cur, group_name: Optional[str]) -> Optional[int]:
    group_name = clean(group_name)
    if not group_name:
        return None
    cur.execute("INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (group_name,))
    cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
    row = cur.fetchone()
    return row[0] if row else None


def contact_exists(cur, name: str) -> bool:
    cur.execute("SELECT 1 FROM contacts WHERE name = %s", (name,))
    return cur.fetchone() is not None


def upsert_contact(
    cur,
    name: str,
    email: Optional[str],
    birthday: Optional[str],
    group_name: Optional[str],
    phones: List[Dict[str, str]],
) -> None:
    group_id = fetch_group_id(cur, group_name)

    if contact_exists(cur, name):
        cur.execute(
            """
            UPDATE contacts
            SET email = %s,
                birthday = %s,
                group_id = %s
            WHERE name = %s
            """,
            (email or None, birthday or None, group_id, name),
        )
        cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
        contact_id = cur.fetchone()[0]
        cur.execute("DELETE FROM phones WHERE contact_id = %s", (contact_id,))
    else:
        cur.execute(
            """
            INSERT INTO contacts (name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (name, email or None, birthday or None, group_id),
        )
        contact_id = cur.fetchone()[0]

    for phone in phones:
        cur.execute(
            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
            (contact_id, phone["phone"], phone["type"]),
        )


def replace_contact(
    cur,
    name: str,
    email: Optional[str],
    birthday: Optional[str],
    group_name: Optional[str],
    phones: List[Dict[str, str]],
) -> None:
    cur.execute("DELETE FROM contacts WHERE name = %s", (name,))
    group_id = fetch_group_id(cur, group_name)
    cur.execute(
        """
        INSERT INTO contacts (name, email, birthday, group_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (name, email or None, birthday or None, group_id),
    )
    contact_id = cur.fetchone()[0]
    for phone in phones:
        cur.execute(
            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
            (contact_id, phone["phone"], phone["type"]),
        )


def get_contact_payload(cur, contact_id: int) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT
            c.id,
            c.name,
            c.email,
            c.birthday,
            c.created_at,
            g.name AS group_name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.id = %s
        """,
        (contact_id,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Contact id {contact_id} not found")

    cur.execute(
        """
        SELECT phone, type
        FROM phones
        WHERE contact_id = %s
        ORDER BY id
        """,
        (contact_id,),
    )
    phones = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "birthday": row[3].isoformat() if row[3] else None,
        "created_at": row[4].isoformat() if row[4] else None,
        "group": row[5],
        "phones": phones,
    }


# ---------------- DATABASE INITIALIZATION ----------------
def init_db(conn) -> None:
    schema_sql = read_text_with_fallback(SCHEMA_FILE)
    procedures_sql = read_text_with_fallback(PROCEDURES_FILE)

    with conn.cursor() as cur:
        cur.execute(schema_sql)
        cur.execute(procedures_sql)
    conn.commit()
    print("Database initialized successfully.")


# ---------------- CONTACT OPERATIONS ----------------
def add_contact_interactive(conn) -> None:
    print("\nAdd / update contact")
    name = prompt("Name")
    email = prompt_optional("Email", default="")
    birthday = parse_birthday(prompt_optional("Birthday (YYYY-MM-DD)", default=""))
    group_name = prompt_optional("Group", default="")
    phones = ask_phone_block(single=False)

    with conn.cursor() as cur:
        upsert_contact(cur, name, email, birthday, group_name, phones)
    conn.commit()
    print("Contact saved.")


def add_contact(conn, name: Optional[str], email: Optional[str], birthday: Optional[str], group_name: Optional[str], phone: Optional[str], phone_type: Optional[str]) -> None:
    name = clean(name) or prompt("Name")
    email = clean(email) or prompt_optional("Email", default="")
    birthday = parse_birthday(birthday or prompt_optional("Birthday (YYYY-MM-DD)", default=""))
    group_name = clean(group_name) or prompt_optional("Group", default="")
    if clean(phone):
        phones = [{"phone": clean(phone), "type": normalize_phone_type(phone_type)}]
    else:
        print("No phone was given, so let's add one now.")
        phones = ask_phone_block(single=True)

    with conn.cursor() as cur:
        upsert_contact(cur, name, email, birthday, group_name, phones)
    conn.commit()
    print("Contact saved.")


def add_phone(conn, name: Optional[str], phone: Optional[str], phone_type: Optional[str]) -> None:
    name = clean(name) or prompt("Contact name")
    phone = clean(phone) or prompt("Phone")
    phone_type = normalize_phone_type(phone_type or prompt_choice("Phone type", list(PHONE_TYPES), default="mobile"))

    with conn.cursor() as cur:
        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
    conn.commit()
    print("Phone added.")


def move_group(conn, name: Optional[str], group_name: Optional[str]) -> None:
    name = clean(name) or prompt("Contact name")
    group_name = clean(group_name) or prompt("Group name")
    with conn.cursor() as cur:
        cur.execute("CALL move_to_group(%s, %s)", (name, group_name))
    conn.commit()
    print("Contact moved to group.")


def delete_contact(conn, name: Optional[str]) -> None:
    name = clean(name) or prompt("Contact name")
    if not prompt_yes_no(f"Delete '{name}'?", default=False):
        print("Cancelled.")
        return
    with conn.cursor() as cur:
        cur.execute("DELETE FROM contacts WHERE name = %s", (name,))
        if cur.rowcount == 0:
            conn.rollback()
            print("Contact not found.")
            return
    conn.commit()
    print("Contact deleted.")


def search_contacts(conn, query: Optional[str]) -> None:
    query = clean(query) or prompt("Search query")
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM search_contacts(%s)", (query,))
        rows = cur.fetchall()
    print_rows(rows)


def list_contacts(conn, group_name: Optional[str], email_query: Optional[str], sort_by: str, desc: bool) -> None:
    if sort_by not in SORT_FIELDS:
        sort_by = "name"

    order = "DESC" if desc else "ASC"

    sql = """
        SELECT
            c.id,
            c.name,
            c.email,
            c.birthday,
            g.name AS group_name,
            COALESCE(string_agg(p.phone || ' (' || p.type || ')', ', ' ORDER BY p.id), '') AS phones,
            c.created_at
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
    """
    conditions = []
    params: List[Any] = []

    if clean(group_name):
        conditions.append("g.name = %s")
        params.append(group_name)
    if clean(email_query):
        conditions.append("COALESCE(c.email, '') ILIKE %s")
        params.append(f"%{email_query}%")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += f"""
        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
        ORDER BY c.{sort_by} {order} NULLS LAST, c.id {order}
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    print_rows(rows)


def paginate_contacts(conn, limit: int, sort_by: str, desc: bool) -> None:
    if sort_by not in SORT_FIELDS:
        sort_by = "name"

    offset = 0
    limit = max(1, limit)

    while True:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM get_contacts_page(%s, %s, %s, %s)", (limit, offset, sort_by, desc))
            rows = cur.fetchall()

        print("\n" + "=" * 72)
        print(f"Page offset: {offset} | limit: {limit} | sort: {sort_by} | desc: {desc}")
        print("=" * 72)
        if not rows:
            print("No records found.")
        else:
            for row in rows:
                print(row)

        cmd = prompt_optional("Next / prev / quit", default="q").lower()
        if cmd in ("n", "next"):
            if len(rows) < limit:
                print("No next page.")
            else:
                offset += limit
        elif cmd in ("p", "prev"):
            offset = max(0, offset - limit)
        elif cmd in ("q", "quit", ""):
            break
        else:
            print("Use n, p or q.")


# ---------------- EXPORT / IMPORT ----------------
def export_json(conn, file_path: Path) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM contacts ORDER BY id")
        contact_ids = [row[0] for row in cur.fetchall()]

        data = []
        for cid in contact_ids:
            data.append(get_contact_payload(cur, cid))

    write_text_utf8(file_path, json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Exported {len(data)} contacts to {file_path}")


def load_json_contacts(file_path: Path) -> List[Dict[str, Any]]:
    text = read_text_with_fallback(file_path)
    data = json.loads(text)
    if isinstance(data, dict) and "contacts" in data:
        data = data["contacts"]
    if not isinstance(data, list):
        raise ValueError("JSON must contain a list of contacts or {'contacts': [...]}")

    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        phones = item.get("phones", [])
        normalized_phones = []
        if isinstance(phones, list):
            for phone_item in phones:
                if isinstance(phone_item, dict) and phone_item.get("phone"):
                    normalized_phones.append({
                        "phone": str(phone_item["phone"]).strip(),
                        "type": normalize_phone_type(phone_item.get("type")),
                    })
        result.append({
            "name": str(item.get("name", "")).strip(),
            "email": item.get("email"),
            "birthday": item.get("birthday"),
            "group": item.get("group"),
            "phones": normalized_phones,
        })
    return [x for x in result if x["name"]]


def import_json(conn, file_path: Path) -> None:
    file_path = Path(file_path)
    contacts = load_json_contacts(file_path)
    if not contacts:
        print("No contacts found in JSON.")
        return

    with conn.cursor() as cur:
        for contact in contacts:
            if not contact["phones"]:
                print(f"Skipping '{contact['name']}' because it has no phones.")
                continue

            if contact_exists(cur, contact["name"]):
                print(f"\nDuplicate contact found: {contact['name']}")
                if prompt_yes_no("Overwrite this contact?", default=False):
                    replace_contact(
                        cur,
                        contact["name"],
                        contact.get("email"),
                        parse_birthday(contact.get("birthday")),
                        contact.get("group"),
                        contact["phones"],
                    )
                else:
                    print("Skipped.")
            else:
                upsert_contact(
                    cur,
                    contact["name"],
                    contact.get("email"),
                    parse_birthday(contact.get("birthday")),
                    contact.get("group"),
                    contact["phones"],
                )

    conn.commit()
    print("JSON import completed.")


def detect_csv_columns(fieldnames: List[str]) -> Dict[str, str]:
    return {name.lower().strip(): name for name in fieldnames if name}


def import_csv(conn, file_path: Path) -> None:
    file_path = Path(file_path)
    text = read_text_with_fallback(file_path)
    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames:
        print("CSV file has no header.")
        return

    cols = detect_csv_columns(reader.fieldnames)

    with conn.cursor() as cur:
        count = 0
        for row in reader:
            name = clean(row.get(cols.get("name", ""), ""))
            if not name:
                first = clean(row.get(cols.get("first_name", ""), ""))
                last = clean(row.get(cols.get("last_name", ""), ""))
                name = clean(f"{first} {last}")

            if not name:
                continue

            email = clean(row.get(cols.get("email", ""), "")) or None
            birthday = row.get(cols.get("birthday", ""), "") or None
            group_name = (
                clean(row.get(cols.get("group", ""), ""))
                or clean(row.get(cols.get("category", ""), ""))
                or None
            )

            phones: List[Dict[str, str]] = []
            if clean(row.get(cols.get("phone", ""), "")):
                phones.append(
                    {
                        "phone": clean(row.get(cols.get("phone", ""), "")),
                        "type": normalize_phone_type(row.get(cols.get("phone_type", ""), "") or row.get(cols.get("type", ""), "")),
                    }
                )
            elif clean(row.get(cols.get("phones", ""), "")):
                phones.append({"phone": clean(row.get(cols.get("phones", ""), "")), "type": "mobile"})

            if not phones:
                print(f"Skipping '{name}' because no phone was found.")
                continue

            if contact_exists(cur, name):
                if prompt_yes_no(f"Duplicate contact '{name}'. Overwrite?", default=False):
                    replace_contact(cur, name, email, parse_birthday(birthday), group_name, phones)
                else:
                    print(f"Skipped {name}")
            else:
                upsert_contact(cur, name, email, parse_birthday(birthday), group_name, phones)

            count += 1

    conn.commit()
    print(f"Imported {count} CSV rows.")


# ---------------- SAMPLE DATA ----------------
def create_sample_csv(file_path: Path) -> None:
    content = (
        "name,email,birthday,group,phone,phone_type\n"
        "Alihan Sarsenov,alihan@example.com,2004-05-12,Friend,+77011234567,mobile\n"
        "Dana Karim,dana@example.com,2003-11-22,Work,+77771234567,work\n"
    )
    write_text_utf8(Path(file_path), content)
    print(f"Sample CSV written to {file_path}")


# ---------------- INTERACTIVE MENU ----------------
def show_menu() -> None:
    print("\n" + "=" * 60)
    print("TSIS1 PhoneBook")
    print("=" * 60)
    print("1) Initialize database")
    print("2) Add / update contact")
    print("3) Add phone to contact")
    print("4) Move contact to group")
    print("5) Search")
    print("6) List with filters")
    print("7) Pagination")
    print("8) Export to JSON")
    print("9) Import from JSON")
    print("10) Import from CSV")
    print("11) Delete contact")
    print("12) Create sample CSV")
    print("0) Exit")


def interactive_menu(conn) -> None:
    while True:
        show_menu()
        choice = prompt_optional("Choose", default="0")
        choice = clean(choice)

        try:
            if choice == "1":
                init_db(conn)
            elif choice == "2":
                add_contact_interactive(conn)
            elif choice == "3":
                add_phone(conn, None, None, None)
            elif choice == "4":
                move_group(conn, None, None)
            elif choice == "5":
                search_contacts(conn, None)
            elif choice == "6":
                group_name = prompt_optional("Group filter", default="")
                email_query = prompt_optional("Email filter", default="")
                sort_by = prompt_choice("Sort by", list(SORT_FIELDS), default="name")
                desc = prompt_yes_no("Sort descending?", default=False)
                list_contacts(conn, group_name, email_query, sort_by, desc)
            elif choice == "7":
                limit_text = prompt_optional("Page size", default=str(PAGE_SIZE))
                sort_by = prompt_choice("Sort by", list(SORT_FIELDS), default="name")
                desc = prompt_yes_no("Sort descending?", default=False)
                paginate_contacts(conn, int(limit_text), sort_by, desc)
            elif choice == "8":
                file_name = prompt_optional("Output file", default="contacts.json")
                export_json(conn, Path(file_name))
            elif choice == "9":
                file_name = prompt("JSON file path")
                import_json(conn, Path(file_name))
            elif choice == "10":
                file_name = prompt("CSV file path")
                import_csv(conn, Path(file_name))
            elif choice == "11":
                delete_contact(conn, None)
            elif choice == "12":
                file_name = prompt_optional("CSV file path", default=str(SAMPLE_CSV_FILE))
                create_sample_csv(Path(file_name))
            elif choice in ("0", "q", "quit", "exit", ""):
                print("Bye.")
                break
            else:
                print("Unknown option.")
        except Exception as exc:
            print(f"Error: {exc}")


# ---------------- ARGPARSE / CLI ----------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TSIS1 PhoneBook — Extended Contact Management")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init", help="Initialize database schema and procedures")

    add = sub.add_parser("add", help="Add or update a contact")
    add.add_argument("--name")
    add.add_argument("--email")
    add.add_argument("--birthday")
    add.add_argument("--group")
    add.add_argument("--phone")
    add.add_argument("--phone-type", default="mobile")

    aphone = sub.add_parser("add-phone", help="Add a phone to an existing contact")
    aphone.add_argument("--name")
    aphone.add_argument("--phone")
    aphone.add_argument("--phone-type", default="mobile")

    move = sub.add_parser("move-group", help="Move contact to group")
    move.add_argument("--name")
    move.add_argument("--group")

    search = sub.add_parser("search", help="Search by name, email or phone")
    search.add_argument("--query")

    lst = sub.add_parser("list", help="List contacts with filters")
    lst.add_argument("--group")
    lst.add_argument("--email")
    lst.add_argument("--sort-by", default="name")
    lst.add_argument("--desc", action="store_true")

    page = sub.add_parser("page", help="Interactive pagination")
    page.add_argument("--limit", type=int, default=PAGE_SIZE)
    page.add_argument("--sort-by", default="name")
    page.add_argument("--desc", action="store_true")

    exp = sub.add_parser("export-json", help="Export all contacts to JSON")
    exp.add_argument("--file", default="contacts.json")

    impj = sub.add_parser("import-json", help="Import contacts from JSON")
    impj.add_argument("--file")

    impc = sub.add_parser("import-csv", help="Import contacts from CSV")
    impc.add_argument("--file")

    delc = sub.add_parser("delete", help="Delete contact")
    delc.add_argument("--name")

    sample = sub.add_parser("sample-csv", help="Create a sample CSV file")
    sample.add_argument("--file", default=str(SAMPLE_CSV_FILE))

    return parser


def main() -> None:
    if hasattr(sys.stdin, "reconfigure"):
        try:
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args()

    conn = get_connection()
    try:
        if not args.cmd:
            interactive_menu(conn)
            return

        if args.cmd == "init":
            init_db(conn)
        elif args.cmd == "add":
            add_contact(conn, args.name, args.email, args.birthday, args.group, args.phone, args.phone_type)
        elif args.cmd == "add-phone":
            add_phone(conn, args.name, args.phone, args.phone_type)
        elif args.cmd == "move-group":
            move_group(conn, args.name, args.group)
        elif args.cmd == "search":
            search_contacts(conn, args.query)
        elif args.cmd == "list":
            list_contacts(conn, args.group, args.email, args.sort_by, args.desc)
        elif args.cmd == "page":
            paginate_contacts(conn, args.limit, args.sort_by, args.desc)
        elif args.cmd == "export-json":
            export_json(conn, Path(args.file))
        elif args.cmd == "import-json":
            file_name = args.file or prompt("JSON file path")
            import_json(conn, Path(file_name))
        elif args.cmd == "import-csv":
            file_name = args.file or prompt("CSV file path")
            import_csv(conn, Path(file_name))
        elif args.cmd == "delete":
            delete_contact(conn, args.name)
        elif args.cmd == "sample-csv":
            create_sample_csv(Path(args.file))
        else:
            parser.print_help()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
