#!/bin/sh

echo "=== MAKING MIGRATIONS ==="
python manage.py makemigrations
echo "=== ALL MIGRATIONS ==="
python manage.py showmigrations
echo "=== APPLYING MIGRATIONS ==="
python manage.py migrate --run-syncdb
echo "=== STARTING SERVER... ==="
python manage.py runserver 0.0.0.0:8000
