#! /usr/bin/env sh
set -e

aerich upgrade
pybabel compile -d locale
python /app/scripts/initial_data.py

exec gunicorn -k "uvicorn.workers.UvicornWorker" -c "/app/core/gunicorn_conf.py" "app.main:app"
