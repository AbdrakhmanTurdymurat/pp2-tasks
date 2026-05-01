CREATE OR REPLACE FUNCTION get_contacts_page(
    p_limit INTEGER,
    p_offset INTEGER,
    p_sort_field TEXT DEFAULT 'name',
    p_sort_desc BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phones TEXT,
    created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_by TEXT;
BEGIN
    IF p_sort_field NOT IN ('name', 'birthday', 'created_at') THEN
        p_sort_field := 'name';
    END IF;

    v_order_by := CASE
        WHEN p_sort_desc THEN format('%I DESC NULLS LAST, c.id DESC', p_sort_field)
        ELSE format('%I ASC NULLS LAST, c.id ASC', p_sort_field)
    END;

    RETURN QUERY EXECUTE format($q$
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
        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
        ORDER BY %s
        LIMIT $1 OFFSET $2
    $q$, v_order_by)
    USING p_limit, p_offset;
END;
$$;

CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone VARCHAR,
    p_type VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type: %', p_type;
    END IF;

    SELECT id
    INTO v_contact_id
    FROM contacts
    WHERE name = p_contact_name;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact not found: %', p_contact_name;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type)
    ON CONFLICT (contact_id, phone)
    DO UPDATE SET type = EXCLUDED.type;
END;
$$;

CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_group_id INTEGER;
BEGIN
    INSERT INTO groups (name)
    VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id
    INTO v_group_id
    FROM groups
    WHERE name = p_group_name;

    IF v_group_id IS NULL THEN
        RAISE EXCEPTION 'Could not create or find group: %', p_group_name;
    END IF;

    UPDATE contacts
    SET group_id = v_group_id
    WHERE name = p_contact_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Contact not found: %', p_contact_name;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phones TEXT,
    created_at TIMESTAMP
)
LANGUAGE sql
AS $$
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
    WHERE
        c.name ILIKE '%' || p_query || '%'
        OR COALESCE(c.email, '') ILIKE '%' || p_query || '%'
        OR EXISTS (
            SELECT 1
            FROM phones p2
            WHERE p2.contact_id = c.id
              AND p2.phone ILIKE '%' || p_query || '%'
        )
    GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
    ORDER BY c.id;
$$;
