from connect import get_connection
def _print_rows(rows):
    if not rows:
        print("  (no results)")
        return
    print(f"\n  {'ID':<5} {'First name':<15} {'Last name':<15} {'Phone':<20}")
    print("  " + "─" * 57)
    for r in rows:
        print(f"  {r[0]:<5} {r[1]:<15} {(r[2] or ''):<15} {r[3]:<20}")
    print()



def search_by_pattern():
    pattern = input("Enter search pattern (part of name or phone): ").strip()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_by_pattern(%s)", (pattern,))
            _print_rows(cur.fetchall())
    finally:
        conn.close()




def upsert_one():
    firstname = input("First name : ").strip()
    lastname  = input("Last name  : ").strip()
    phone     = input("Phone      : ").strip()

    if not firstname or not phone:
        print("[ERROR] First name and phone are required.")
        return

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CALL upsert_contact(%s, %s, %s)",
                    (firstname, lastname or None, phone)
                )
        print("[OK] Contact saved (inserted or updated).")
    finally:
        conn.close()



def bulk_insert():
    print("Enter contacts one by one. Leave first name blank to stop.")
    firstnames, lastnames, phones = [], [], []

    while True:
        fn = input("  First name (blank to finish): ").strip()
        if not fn:
            break
        ln = input("  Last name : ").strip()
        ph = input("  Phone     : ").strip()
        firstnames.append(fn)
        lastnames.append(ln)
        phones.append(ph)

    if not firstnames:
        print("[INFO] Nothing to insert.")
        return

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                
                cur.execute(
                    "CALL bulk_insert_contacts(%s::text[], %s::text[], %s::text[], %s::text[])",
                    (firstnames, lastnames, phones, [])
                )
               
                row = cur.fetchone()
                invalid = row[0] if row else []

        if invalid:
            print(f"\n[WARN] {len(invalid)} invalid phone number(s) were skipped:")
            for entry in invalid:
                print(f"  • {entry}")
        else:
            print("[OK] All contacts inserted/updated successfully.")
    finally:
        conn.close()




def paginated_query():
    try:
        limit  = int(input("Rows per page [5]: ").strip() or "5")
        page   = int(input("Page number  [1]: ").strip() or "1")
    except ValueError:
        print("[ERROR] Please enter valid numbers.")
        return

    offset = (page - 1) * limit
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM get_contacts_paginated(%s, %s)",
                (limit, offset)
            )
            rows = cur.fetchall()
        print(f"\n  Page {page} (limit={limit}, offset={offset})")
        _print_rows(rows)
    finally:
        conn.close()




def delete_contact():
    print("Delete by:")
    print("  1. Name")
    print("  2. Phone")
    choice = input("Choice (1/2): ").strip()

    if choice == "1":
        value = input("First name to delete: ").strip()
        search_type = "name"
    elif choice == "2":
        value = input("Phone to delete: ").strip()
        search_type = "phone"
    else:
        print("[ERROR] Invalid choice.")
        return

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CALL delete_contact(%s, %s)",
                    (search_type, value)
                )
        print("[OK] Delete procedure executed.")
    finally:
        conn.close()



def menu():
    while True:
        print("\n═══════════ PhoneBook – Practice 8 ═══════════")
        print(" 1. Search contacts by pattern")
        print(" 2. Add / update one contact  (upsert)")
        print(" 3. Bulk insert contacts with validation")
        print(" 4. Browse contacts (paginated)")
        print(" 5. Delete a contact")
        print(" 0. Exit")
        print("═══════════════════════════════════════════════")
        choice = input("Choose: ").strip()

        if   choice == "1": search_by_pattern()
        elif choice == "2": upsert_one()
        elif choice == "3": bulk_insert()
        elif choice == "4": paginated_query()
        elif choice == "5": delete_contact()
        elif choice == "0":
            print("Bye!")
            break
        else:
            print("[ERROR] Unknown option.")


if __name__ == "__main__":
    menu()