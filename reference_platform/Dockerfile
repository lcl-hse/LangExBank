FROM python:3.8.10-slim

RUN mkdir /usr/src/app

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements.txt

RUN apt update && \
    apt install --no-install-recommends -y build-essential gcc
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD uwsgi --http 0.0.0.0:8000 --wsgi-file app.py --callable application --stats 0.0.0.0:8001 --static-map /static=/usr/src/app/static
