#!/bin/sh

python3 manage.py makemigrations
python3 manage.py migrate --run-syncdb
python3 manage.py collectstatic --noinput

echo "Running Django development server on port 8000"
exec python3 manage.py runserver 0.0.0.0:8000