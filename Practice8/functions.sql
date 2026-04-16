CREATE OR REPLACE FUNCTION search_by_pattern(p_pattern TEXT)
RETURNS TABLE(
    id        INT,
    firstname VARCHAR,
    lastname  VARCHAR,
    phone     VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
        SELECT pb.id, pb.firstname, pb.lastname, pb.phone
        FROM   phonebook pb
        WHERE  pb.firstname ILIKE '%' || p_pattern || '%'
           OR  pb.lastname  ILIKE '%' || p_pattern || '%'
           OR  pb.phone     ILIKE '%' || p_pattern || '%'
        ORDER BY pb.firstname;
END;
$$;



CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit  INT DEFAULT 10,
    p_offset INT DEFAULT 0
)
RETURNS TABLE(
    id        INT,
    firstname VARCHAR,
    lastname  VARCHAR,
    phone     VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_limit <= 0 THEN
        RAISE EXCEPTION 'p_limit must be a positive integer, got %', p_limit;
    END IF;
    IF p_offset < 0 THEN
        RAISE EXCEPTION 'p_offset cannot be negative, got %', p_offset;
    END IF;

    RETURN QUERY
        SELECT pb.id, pb.firstname, pb.lastname, pb.phone
        FROM   phonebook pb
        ORDER BY pb.id
        LIMIT  p_limit
        OFFSET p_offset;
END;
$$;