#!/bin/bash
echo "Waiting for postgres..."

while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 0.1
done

echo "PostgreSQL started"

python manage.py migrate
python manage.py collectstatic --no-input --clear
python manage.py createsuperuser --noinput #--username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL --password $DJANGO_SUPERUSER_PASSWORD

# command
gunicorn testing_platform.wsgi:application --bind 0.0.0.0:8000 -t 10000