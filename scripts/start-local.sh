#! /usr/bin/env sh
set -e

HOST=${HOST:-0.0.0.0}
PORT=${PORT:-80}
LOG_LEVEL=${LOG_LEVEL:-info}

aerich upgrade
python /app/scripts/initial_data.py

exec uvicorn --reload --host $HOST --port $PORT --log-level $LOG_LEVEL "app.main:app"
