DROP TABLE IF EXISTS phones CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS groups CASCADE;

CREATE TABLE groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE contacts (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) UNIQUE NOT NULL,
    email      VARCHAR(100),
    birthday   DATE,
    group_id   INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) NOT NULL CHECK (type IN ('home', 'work', 'mobile')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (contact_id, phone)
);

INSERT INTO groups (name) VALUES
    ('Family'),
    ('Work'),
    ('Friend'),
    ('Other')
ON CONFLICT (name) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts (name);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts (email);
CREATE INDEX IF NOT EXISTS idx_contacts_group_id ON contacts (group_id);
CREATE INDEX IF NOT EXISTS idx_phones_phone ON phones (phone);
