# LangExBank

Инструкция по установке и запуску тестовой платформы на сервере

Конфигурация тестовой платформы осуществляется через файл env.prod. В нём должны быть указаны значения следующих переменных в формате KEY=VALUE:

SECRET_KEY - Секретный ключ приложения, не должен меняться

DEBUG - 0 или 1, использовать ли платформу в режиме дебага

ALLOWED_HOSTS - Список (через пробел) хостов, на которых можно запускать приложение, должен включать localhost, 127.0.0.1, IP-адрес сервера и доменное имя, на котором работает приложение

FIELD_ENCRYPTION_KEYS - Список ключей для кодирования защищённых полей в бд

DJANGO_STATIC_URL - URL, по которому будут доступны статические файлы сайта

DJANGO_MEDIA_URL - URL, по которому будут доступны медиафайлы платформы (PDF, аудиозаписи)

MEDIA_ROOT - местоположение папки, в которой будут находиться медиафайлы платформы

STATIC_ROOT - местоположение папки, в которой будут находиться статические файлы сайта

REFERENCE_URL - URL, по которому будет доступна справочная платформа

LANGEXBANK_ENC_KEY - ключ, при помощи которого будут шифроваться логины при включенной анонимизации результатов тестов

LANGEXBANK_ENCODE_USERS - 0 или 1, анонимизировать ли результаты тестов

LANGEXBANK_OPEN_SIGNUP - 0 или 1, оставить ли открытой регистрацию для всех желающих

TRIES - число, максимальное количество возможных выводов курсора с экрана при сдаче теста

TIME_PER_TRY - максимальное дозволенное время увода курсора с экрана при сдаче теста

POSTGRES_USER - имя пользователя БД Postgres

POSTGRES_PASSWORD - пароль пользователя БД Postgres

POSTGRES_DB - название БД Postgres

PGDATA - Путь к каталогу с данными Postgres на томе postgres_volume

Инструкция по первоначальному запуску:

1. Собрать и запустить контейнеры
```bash
sudo docker-compose up -d --build
```

2. Создать нужные таблицы в базе данных
```bash
sudo docker exec langexbank_web_1 python manage.py makemigrations main_app
sudo docker exec langexbank_web_1 python manage.py migrate
```

3. Собрать static_files
```bash
sudo docker exec langexbank_web_1 python manage.py collectstatic --no-input
```

4. Скопировать медиафайлы
```
sudo docker cp ./latest_mediafiles/. langexbank_web_1:/home/app/web/mediafiles
```

5. Загрузить дамп БД
```bash
sudo docker cp ./latest_dump.json langexbank_web_1:/home/app/web/latest_dump.json
sudo docker exec langexbank_web_1 python manage.py loaddata --app main_app latest_dump.json
```

6. Создать суперпользователя и записать логин и пароль
```bash
sudo docker exec -it langexbank_web_1 python manage.py createsuperuser
```

Как менять переменные среды:

1. Поменять значения в файле docker-compose.yml

2. Перезапустить сервис
```bash
sudo docker-compose up -d
```