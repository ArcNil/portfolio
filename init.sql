-- Schema + roles for PostgREST, executed once at container startup.

-- Role PostgREST connects as (anonymous / public access)
CREATE ROLE web_anon LOGIN NOINHERIT;

-- Role used to apply schema changes. Password comes from start.sh
-- via psql variable `auth_pw` (sourced from AUTHENTICATOR_PASSWORD).
CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD :'auth_pw';
GRANT web_anon TO authenticator;

CREATE SCHEMA api;
GRANT USAGE ON SCHEMA api TO web_anon;

CREATE TABLE api.todos (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    done        boolean NOT NULL DEFAULT false,
    task        text    NOT NULL,
    due         timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Change ownership BEFORE granting: ALTER TABLE ... OWNER TO drops
-- privileges granted by the previous owner.
ALTER TABLE api.todos OWNER TO authenticator;
GRANT SELECT, INSERT, UPDATE, DELETE ON api.todos TO web_anon;
GRANT USAGE, SELECT ON SEQUENCE api.todos_id_seq TO web_anon;

INSERT INTO api.todos (task, due) VALUES
    ('Try GET /todos', now() + interval '1 day'),
    ('Try POST /todos', now() + interval '2 days'),
    ('Try PATCH /todos?id=eq.1', now() + interval '3 days');

-- Expose row counts in Content-Range headers
CREATE OR REPLACE FUNCTION api.todos_count()
RETURNS bigint
LANGUAGE sql
AS $$
    SELECT count(*) FROM api.todos;
$$;

-- OpenAPI description endpoint
CREATE OR REPLACE FUNCTION api.openapi_description()
RETURNS text
LANGUAGE sql
AS $$
    SELECT 'A demo PostgREST API running on Hugging Face Spaces';
$$;