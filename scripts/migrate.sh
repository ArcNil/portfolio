#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

current_output=$(alembic current)
latest_output=$(alembic heads)

extract_revisions() {
    printf '%s\n' "$1" | awk '
        $1 ~ /^[[:alnum:]_]+$/ && $1 != "Current" && $1 != "none" {
            print $1
        }
    ' | sort -u
}

current_revisions=$(extract_revisions "$current_output")
latest_revisions=$(extract_revisions "$latest_output")

if [ -z "$latest_revisions" ]; then
    echo "Unable to determine the latest Alembic revision." >&2
    exit 1
fi

if [ "$current_revisions" = "$latest_revisions" ]; then
    echo "Database is already at the latest migration ($current_revisions)."
    exit 0
fi

echo "Database is not at the latest migration."
echo "Current revision(s): ${current_revisions:-none}"
echo "Latest revision(s): $latest_revisions"
exec alembic upgrade head
