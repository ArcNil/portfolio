#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

sh scripts/migrate.sh
exec uvicorn app.main:app --host 0.0.0.0 --port 7860
