###########
# BUILDER #
###########

# pull official base image
# если так и не будет работать, убрать slim
FROM python:3.7-slim as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# COPY . /usr/src/app/

# install dependencies
# install torch first as a separate layer (to be cached)
# remove torch from dependencies as DistractorSelector doesn't use it anyway
# RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels torch==1.7.1

COPY ./requirements-final.txt .
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements-final.txt


#########
# FINAL #
#########

# pull official base image
# если не будет работать, убрать slim
FROM python:3.7-slim

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system app && adduser app app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/mediafiles
WORKDIR $APP_HOME

# install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
# COPY --from=builder /usr/src/app/requirements-final.txt .
RUN apt update && apt install --no-install-recommends -y netcat
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*
RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader punkt

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app
