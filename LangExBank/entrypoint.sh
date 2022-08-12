#!/bin/bash
echo "Waiting for postgres..."

while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 0.1
done

echo "PostgreSQL started"

python manage.py migrate
python manage.py collectstatic --no-input --clear
python manage.py createsuperuser --noinput --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL --password $DJANGO_SUPERUSER_PASSWORD

# cкачать данные с хостинга, используя пароль из environment_variables
# загрузить их с помощью loaddata