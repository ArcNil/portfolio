# PostgREST + PostgreSQL in a single container (Hugging Face Space)
# Serves a fully RESTful API from a Postgres database on port 7860.

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PGRST_VERSION=16.2 \
    PORT=7860 \
    PGRST_DB_SCHEMAS=api \
    PGRST_DB_ANON_ROLE=web_anon \
    PGRST_SERVER_HOST=0.0.0.0

# Debian's postgresql package installs binaries outside the default PATH
ENV PATH="/usr/lib/postgresql/15/bin:${PATH}"

# --- System dependencies: PostgreSQL server + tools ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        xz-utils \
        libpq5 \
        postgresql \
        postgresql-contrib \
        postgresql-client \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# --- PostgREST binary (static build from GitHub releases) ---
RUN ARCH="$(dpkg --print-architecture)" \
    && case "$ARCH" in \
        amd64) PGRST_ARCH=x86-64 ;; \
        arm64) PGRST_ARCH=aarch64 ;; \
        *) echo "unsupported arch: $ARCH" && exit 1 ;; \
    esac \
    && curl -fsSL \
        "https://github.com/PostgREST/postgrest/releases/download/v${PGRST_VERSION}/postgrest-v${PGRST_VERSION}-linux-static-${PGRST_ARCH}.tar.xz" \
        -o /tmp/postgrest.tar.xz \
    && tar -xJf /tmp/postgrest.tar.xz -C /usr/local/bin \
    && chmod +x /usr/local/bin/postgrest \
    && rm /tmp/postgrest.tar.xz \
    && postgrest --version

# --- Non-root user (HF Spaces runs containers as a random UID) ---
RUN useradd -m -u 10001 appuser \
    && mkdir -p /var/lib/postgresql/data /var/run/postgresql \
    && chown -R appuser:appuser /var/lib/postgresql /var/run/postgresql /usr/local/bin/postgrest

USER appuser
WORKDIR /home/appuser

# --- Sample schema: a tiny "todos" API to demo PostgREST ---
COPY --chown=appuser:appuser init.sql /docker-entrypoint-init.d/init.sql
COPY --chown=appuser:appuser start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 7860

CMD ["start.sh"]