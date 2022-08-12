"""
Django settings for testing_platform project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from pathlib import Path


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", default="MY-SECRET-KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = False
DEBUG = bool(int(os.environ.get("DEBUG", default=0)))

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", default="*").split()


# Application definition


INSTALLED_APPS = [
    'main_app.apps.MainAppConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'encrypted_fields'
]

# A list of hex-encoded 32 byte keys.
# You only need one unless/until rotating keys.
# If you want to rotate the encryption key
# just prepend settings.FIELD_ENCRYPTION_KEYS with a new key.
# To rotate keys execute: python manage.py rotate_keys.
# After that you may delete the old key.
FIELD_ENCRYPTION_KEYS = os.environ.get(
    "DJANGO_ENCRYPTION_KEYS",
    default="d798ca31f78677edf0d5a268bff71440b1ba059625ffcc1faef994ade28a605d"
).split()

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


X_FRAME_OPTIONS = 'SAMEORIGIN'

ROOT_URLCONF = 'testing_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'testing_platform.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get(
            "SQL_ENGINE",
            "django.db.backends.postgresql"
        ),
        "NAME": os.environ.get("POSTGRES_DB", "langexbank"),
        "USER": os.environ.get("POSTGRES_USER", "user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "db"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = os.environ.get("DJANGO_STATIC_URL", default='/staticfiles/')

MEDIA_URL = os.environ.get("DJANGO_MEDIA_URL", default='/mediafiles/')

MEDIA_ROOT = os.path.join(BASE_DIR, os.environ.get('DJANGO_MEDIA_ROOT',default='mediafiles'))

STATIC_ROOT = os.path.join(BASE_DIR, os.environ.get('DJANGO_STATIC_ROOT',default='staticfiles'))

REFERENCE_URL = os.environ.get("REFERENCE_URL", default="/reference_platform")

login_enc_key = os.environ.get("LANGEXBANK_ENC_KEY", default="")

encode = int(os.environ.get("LANGEXBANK_ENCODE_USERS", default=0))

registration_open = int(os.environ.get("LANGEXBANK_OPEN_SIGNUP", default=0))

TRIES = int(os.environ.get("TRIES", default=3))

TIME_PER_TRY = int(os.environ.get("TIME_PER_TRY", default=10)) * 1000
