#!/bin/bash
# Keeps a pinggy TCP tunnel to local postgres alive, recycling it before
# the free-tier ~60 minute cap, and writing the current public host:port
# to a file that the FastAPI app reads from.

set -u

URL_FILE=/tmp/pinggy_url.txt
LOG_FILE=/tmp/pinggy_current.log
TTL_SECONDS=$((50 * 60))   # refresh every 50 min, inside the 60 min free cap

echo "[tunnel] waiting for postgres..."
until pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; do
    sleep 1
done
echo "[tunnel] postgres is up"

while true; do
    SECONDS=0
    : > "$LOG_FILE"
    echo "[tunnel] opening new pinggy tunnel..."

    ssh -p 443 -T \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ServerAliveInterval=30 \
        -o ExitOnForwardFailure=yes \
        -R0:127.0.0.1:5432 qr+tcp@free.pinggy.io \
        >> "$LOG_FILE" 2>&1 &
    SSH_PID=$!

    # poll the log for the public "tcp://host:port" pinggy prints on connect
    URL=""
    for i in $(seq 1 30); do
        URL=$(grep -oE 'tcp://[a-zA-Z0-9.-]+:[0-9]+' "$LOG_FILE" | head -n1)
        [ -n "$URL" ] && break
        kill -0 "$SSH_PID" 2>/dev/null || break   # ssh already died
        sleep 1
    done

    if [ -n "$URL" ]; then
        echo "$URL" > "$URL_FILE"
        echo "[tunnel] live at $URL"
    else
        echo "[tunnel] never got a URL from pinggy, see $LOG_FILE" >&2
    fi

    # hold this tunnel open until TTL expires or ssh dies on its own
    while [ "$SECONDS" -lt "$TTL_SECONDS" ] && kill -0 "$SSH_PID" 2>/dev/null; do
        sleep 5
    done

    echo "[tunnel] recycling..."
    kill "$SSH_PID" 2>/dev/null
    wait "$SSH_PID" 2>/dev/null
done