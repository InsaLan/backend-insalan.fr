#!/bin/sh

echo "=== MAKING MIGRATIONS ==="
python manage.py makemigrations
echo "=== ALL MIGRATIONS ==="
python manage.py showmigrations
echo "=== APPLYING MIGRATIONS ==="
python manage.py migrate --run-syncdb
echo "=== DEPLOYING STATIC FILES ==="
python manage.py collectstatic --noinput
echo "=== STARTING SERVER... ==="
exec python -m gunicorn --bind 0.0.0.0:8000 insalan.asgi:application -k uvicorn.workers.UvicornWorker
