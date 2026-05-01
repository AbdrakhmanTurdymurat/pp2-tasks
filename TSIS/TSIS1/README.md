# TSIS1 PhoneBook — Extended Contact Management

## Files
- `phonebook.py` — main console app
- `config.py` — settings
- `connect.py` — PostgreSQL connection helper
- `schema.sql` — updated schema
- `procedures.sql` — stored procedures and functions
- `contacts.csv` — sample import file

## Run
1. Install dependency:
   `pip install psycopg2-binary`
2. Create database connection settings in `config.py` if needed.
3. Initialize DB:
   `python phonebook.py init`
4. Add a contact:
   `python phonebook.py add --name "Alihan Sarsenov" --email "alihan@example.com" --birthday 2004-05-12 --group Friend --phone +77011234567 --phone-type mobile`
5. Search:
   `python phonebook.py search --query gmail`
6. Pagination:
   `python phonebook.py page --limit 5 --sort-by name`
