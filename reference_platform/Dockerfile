FROM python:3.8

RUN mkdir /usr/src/app

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt

CMD uwsgi --http 0.0.0.0:8000 --wsgi-file app.py --callable application --stats 0.0.0.0:8001 --static-map /static=/usr/src/app/static
