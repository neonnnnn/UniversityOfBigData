#!/bin/bash

if [ -n "$POSTGRES_DB" ]; then
  echo "Waiting for PostgreSQL at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
  python - <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
deadline = time.time() + 120

while True:
	try:
		with socket.create_connection((host, port), timeout=2):
			print("PostgreSQL is ready.")
			sys.exit(0)
	except OSError as exc:
		if time.time() >= deadline:
			raise SystemExit(f"PostgreSQL did not become ready in time: {exc}")
		time.sleep(1)
PY
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Making migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations authentication
python manage.py makemigrations management
python manage.py makemigrations competitions
python manage.py makemigrations discussion

echo "Running database migrations..."
python manage.py migrate

echo "Initialize the DB if not yet initialized..."
python manage.py initialize_db

echo "Starting scheduler..."
python manage.py runapscheduler --minute "*/10" --second "0" &

echo "Creating a superuser..."
python manage.py createsuperuser --noinput

echo "Starting server..."
uwsgi --ini /opt/universityofbigdata/uwsgi.ini
