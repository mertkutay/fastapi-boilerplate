#! /usr/bin/env bash

python /app/scripts/wait_for_db.py

exec "$@"
