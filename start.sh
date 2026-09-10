#!/usr/bin/env bash
# Start PostgreSQL, apply the schema, then launch PostgREST on $PORT.
set -euo pipefail

# Load .env if present (local runs; HF Spaces injects vars itself)
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

PGDATA=/var/lib/postgresql/data
SOCKET_DIR=/var/run/postgresql
INIT_SQL=/docker-entrypoint-init.d/init.sql

# Debian's postgresql package keeps binaries in a versioned dir
# (e.g. /usr/lib/postgresql/15/bin) that is not on PATH.
for PGDIR in /usr/lib/postgresql/*/bin; do
    [ -x "$PGDIR/pg_ctl" ] && export PATH="$PGDIR:$PATH" && break
done

command -v pg_ctl >/dev/null || { echo "postgres binaries not found" >&2; exit 1; }

# --- Initialize and start PostgreSQL ---
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    initdb --username=appuser --pgdata="$PGDATA" --auth-local=trust --auth-host=trust
fi

pg_ctl -D "$PGDATA" -o "-c listen_addresses=127.0.0.1 -c unix_socket_directories=$SOCKET_DIR -c port=5432" -w start

# Wait until the server accepts connections
until pg_isready -h "$SOCKET_DIR" -p 5432 -q; do
    sleep 0.2
done

# --- Apply schema once ---
if ! psql -h "$SOCKET_DIR" -p 5432 -d postgres -Atqc "SELECT 1 FROM pg_roles WHERE rolname='web_anon'" | grep -q 1; then
    psql -v ON_ERROR_STOP=1 --set=auth_pw="${AUTHENTICATOR_PASSWORD:-secret}" \
        -h "$SOCKET_DIR" -p 5432 -d postgres -f "$INIT_SQL"
fi

# --- Launch PostgREST ---
export PGRST_DB_URI="postgresql://authenticator:${AUTHENTICATOR_PASSWORD:-secret}@/postgres?host=$SOCKET_DIR&port=5432"
export PGRST_DB_SCHEMA="${PGRST_DB_SCHEMA:-api}"
export PGRST_DB_ANON_ROLE="${PGRST_DB_ANON_ROLE:-web_anon}"
export PGRST_SERVER_PORT="${PGRST_PORT:-3000}"

# PGRST_JWT_ROLE_CLAIM_KEY must be a JSON path (".role", ".payload.role",
# '."https://example.com/role"' or "[\"role\"]"). A bare value like "role"
# is a parse error that crashes PostgREST at startup — normalize it.
if [ -n "${PGRST_JWT_ROLE_CLAIM_KEY:-}" ] && \
   [[ ! "$PGRST_JWT_ROLE_CLAIM_KEY" =~ ^(\.|\[|\") ]]; then
    export PGRST_JWT_ROLE_CLAIM_KEY=".$PGRST_JWT_ROLE_CLAIM_KEY"
fi

# PostgREST listens on the internal port; the proxy serves it (plus
# Swagger UI at /docs) on the public $PORT.
postgrest &
exec python3 /usr/local/bin/proxy.py