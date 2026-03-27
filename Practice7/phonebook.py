import csv
from connect import get_connection

def insert_from_csv(file_path):
    conn = get_connection()
    cur = conn.cursor()

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT INTO contacts (name, phone) VALUES (%s, %s)",
                (row["name"], row["phone"])
            )

    conn.commit()
    cur.close()
    conn.close()
    print("Данные из CSV добавлены")

def insert_from_console():
    name = input("Имя: ")
    phone = input("Телефон: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO contacts (name, phone) VALUES (%s, %s)",
        (name, phone)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Контакт добавлен")


def update_contact():
    name = input("Кого обновить: ")
    new_name = input("Новое имя (или Enter): ")
    new_phone = input("Новый телефон (или Enter): ")

    conn = get_connection()
    cur = conn.cursor()

    if new_name:
        cur.execute("UPDATE contacts SET name=%s WHERE name=%s", (new_name, name))
    if new_phone:
        cur.execute("UPDATE contacts SET phone=%s WHERE name=%s", (new_phone, name))

    conn.commit()
    cur.close()
    conn.close()
    print("Контакт обновлен")

def query_contacts():
    print("1 - Все\n2 - По имени\n3 - По префиксу")
    choice = input("Выбор: ")

    conn = get_connection()
    cur = conn.cursor()

    if choice == "1":
        cur.execute("SELECT * FROM contacts")

    elif choice == "2":
        name = input("Имя: ")
        cur.execute("SELECT * FROM contacts WHERE name ILIKE %s", ('%' + name + '%',))

    elif choice == "3":
        prefix = input("Префикс: ")
        cur.execute("SELECT * FROM contacts WHERE phone LIKE %s", (prefix + '%',))

    rows = cur.fetchall()
    for row in rows:
        print(row)

    cur.close()
    conn.close()

def delete_contact():
    value = input("Имя или телефон для удаления: ")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM contacts WHERE name=%s OR phone=%s",
        (value, value)
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Удалено")

def menu():
    while True:
        print("""
1. Загрузить CSV
2. Добавить контакт
3. Обновить
4. Поиск
5. Удалить
0. Выход
        """)

        choice = input("Выбор: ")

        if choice == "1":
            insert_from_csv("contacts.csv")
        elif choice == "2":
            insert_from_console()
        elif choice == "3":
            update_contact()
        elif choice == "4":
            query_contacts()
        elif choice == "5":
            delete_contact()
        elif choice == "0":
            break


if __name__ == "__main__":
    menu()