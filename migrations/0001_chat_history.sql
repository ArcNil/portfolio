-- Schema + roles for PostgREST, executed once at container startup.
-- Model: chat history (conversations -> messages).

-- Role PostgREST connects as (anonymous / public access)
CREATE ROLE web_anon LOGIN NOINHERIT;

-- Role used to apply schema changes. Password comes from start.sh
-- via psql variable `auth_pw` (sourced from AUTHENTICATOR_PASSWORD).
CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD :'auth_pw';
GRANT web_anon TO authenticator;

CREATE SCHEMA api;
GRANT USAGE ON SCHEMA api TO web_anon;

-- One conversation (a chat thread)
CREATE TABLE api.chats (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title       text    NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Messages belonging to a conversation
CREATE TABLE api.messages (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chat_id     bigint  NOT NULL REFERENCES api.chats (id) ON DELETE CASCADE,
    role        text    NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content     text    NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX messages_chat_id_idx ON api.messages (chat_id);

-- Change ownership BEFORE granting: ALTER TABLE ... OWNER TO drops
-- privileges granted by the previous owner.
ALTER TABLE api.chats    OWNER TO authenticator;
ALTER TABLE api.messages OWNER TO authenticator;

GRANT SELECT, INSERT, UPDATE, DELETE ON api.chats    TO web_anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON api.messages TO web_anon;
GRANT USAGE, SELECT ON SEQUENCE api.chats_id_seq    TO web_anon;
GRANT USAGE, SELECT ON SEQUENCE api.messages_id_seq TO web_anon;

INSERT INTO api.chats (title) VALUES
    ('Getting started'),
    ('PostgREST questions');

INSERT INTO api.messages (chat_id, role, content) VALUES
    (1, 'user',      'How do I list all chats?'),
    (1, 'assistant', 'GET /chats — or GET /chats?select=*,messages(*) to embed messages.'),
    (2, 'user',      'How do I add a message to chat 1?'),
    (2, 'assistant', 'POST /messages with {"chat_id": 1, "role": "user", "content": "..."}');

-- Row counts for Content-Range headers
CREATE OR REPLACE FUNCTION api.chats_count()
RETURNS bigint
LANGUAGE sql
AS $$
    SELECT count(*) FROM api.chats;
$$;

CREATE OR REPLACE FUNCTION api.messages_count()
RETURNS bigint
LANGUAGE sql
AS $$
    SELECT count(*) FROM api.messages;
$$;

-- OpenAPI description endpoint
CREATE OR REPLACE FUNCTION api.openapi_description()
RETURNS text
LANGUAGE sql
AS $$
    SELECT 'A demo PostgREST chat-history API running on Hugging Face Spaces';
$$;