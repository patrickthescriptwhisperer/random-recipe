#!/bin/sh
set -eu

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

ensure_recipes_file() {
  mkdir -p /app/data
  if [ ! -f /app/data/recipes.json ]; then
    printf '[]\n' > /app/data/recipes.json
  fi
}

if [ "$(id -u)" = "0" ]; then
  groupmod -o -g "$PGID" appuser
  usermod -o -u "$PUID" -g "$PGID" appuser
  ensure_recipes_file
  chown -R appuser:appuser /app/data
  exec gosu appuser "$@"
fi

# Already running as a specific user (e.g. compose `user:`).
ensure_recipes_file
exec "$@"
