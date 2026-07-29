#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time

services = [
    ("PostgreSQL", os.getenv("POSTGRES_HOST", "postgres"), int(os.getenv("POSTGRES_PORT", "5432"))),
    ("MongoDB", os.getenv("MONGO_HOST", "mongo"), int(os.getenv("MONGO_PORT", "27017"))),
]

for name, host, port in services:
    for attempt in range(60):
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{name} disponivel em {host}:{port}")
                break
        except OSError:
            print(f"Aguardando {name} em {host}:{port}...")
            time.sleep(1)
    else:
        raise SystemExit(f"{name} nao ficou disponivel em {host}:{port}")
PY

python manage.py migrate
python manage.py runserver 0.0.0.0:8000
