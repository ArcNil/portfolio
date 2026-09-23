FROM postgres:16

ENV DEBIAN_FRONTEND=noninteractive

# python for the FastAPI app, ssh client for the tunnel, supervisor to run
# postgres + the tunnel loop + the api as one PID-1-managed process tree.
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip \
        openssh-client \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

# Key so pinggy never blocks on an interactive password prompt (there's no
# TTY in a container). Accepted as an unauthenticated client key by pinggy's
# free tier -- it's just there to skip the "press enter" prompt.
RUN mkdir -p /root/.ssh \
    && ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N "" -q

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed -r requirements.txt
COPY app/ ./app/

COPY tunnel.sh /usr/local/bin/tunnel.sh
RUN chmod +x /usr/local/bin/tunnel.sh

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Override these at `docker run -e ...` (don't ship real creds in the image).
ENV POSTGRES_PASSWORD=changeme
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=postgres

EXPOSE 7860

ENTRYPOINT ["/usr/bin/supervisord"]
CMD ["-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
