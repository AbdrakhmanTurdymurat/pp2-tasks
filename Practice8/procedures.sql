CREATE OR REPLACE PROCEDURE upsert_contact(
    p_firstname VARCHAR,
    p_lastname  VARCHAR,
    p_phone     VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    
    IF EXISTS (SELECT 1 FROM phonebook WHERE phone = p_phone) THEN
        UPDATE phonebook
        SET    firstname = p_firstname,
               lastname  = p_lastname
        WHERE  phone = p_phone;

    ELSIF EXISTS (
        SELECT 1 FROM phonebook
        WHERE  firstname = p_firstname
          AND  (lastname = p_lastname OR (lastname IS NULL AND p_lastname IS NULL))
    ) THEN
        UPDATE phonebook
        SET    phone = p_phone
        WHERE  firstname = p_firstname
          AND  (lastname = p_lastname OR (lastname IS NULL AND p_lastname IS NULL));

   
    ELSE
        INSERT INTO phonebook (firstname, lastname, phone)
        VALUES (p_firstname, p_lastname, p_phone);
    END IF;
END;
$$;


CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_firstnames TEXT[],
    p_lastnames  TEXT[],
    p_phones     TEXT[],
    INOUT p_invalid TEXT[] DEFAULT '{}'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_phone_pattern TEXT := '^\+?[\d\s\-]{7,15}$';
    i               INT;
    v_firstname     TEXT;
    v_lastname      TEXT;
    v_phone         TEXT;
BEGIN
    p_invalid := '{}';   

    IF array_length(p_firstnames, 1) IS DISTINCT FROM array_length(p_phones, 1) THEN
        RAISE EXCEPTION 'Array length mismatch: firstnames=%, phones=%',
            array_length(p_firstnames, 1), array_length(p_phones, 1);
    END IF;

    FOR i IN 1 .. array_length(p_firstnames, 1) LOOP
        v_firstname := TRIM(p_firstnames[i]);
        v_lastname  := TRIM(COALESCE(p_lastnames[i], ''));
        v_phone     := TRIM(p_phones[i]);

    
        IF v_phone !~ v_phone_pattern THEN
            p_invalid := array_append(
                p_invalid,
                format('Row %s: name="%s %s", phone="%s"', i, v_firstname, v_lastname, v_phone)
            );
            CONTINUE;   
        END IF;

       
        IF EXISTS (SELECT 1 FROM phonebook WHERE phone = v_phone) THEN
            UPDATE phonebook
            SET    firstname = v_firstname,
                   lastname  = NULLIF(v_lastname, '')
            WHERE  phone = v_phone;
        ELSE
            INSERT INTO phonebook (firstname, lastname, phone)
            VALUES (v_firstname, NULLIF(v_lastname, ''), v_phone);
        END IF;
    END LOOP;
END;
$$;



CREATE OR REPLACE PROCEDURE delete_contact(
    p_search_type VARCHAR,   -- 'name' | 'phone'
    p_value       VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_deleted INT;
BEGIN
    IF p_search_type = 'name' THEN
        DELETE FROM phonebook
        WHERE firstname ILIKE p_value;

    ELSIF p_search_type = 'phone' THEN
        DELETE FROM phonebook
        WHERE phone = p_value;

    ELSE
        RAISE EXCEPTION 'p_search_type must be ''name'' or ''phone'', got: %', p_search_type;
    END IF;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RAISE NOTICE 'Deleted % row(s).', v_deleted;
END;
$$;