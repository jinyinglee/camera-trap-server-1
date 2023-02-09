"""
Django settings for conf taicat.

Generated by 'django-admin startproject' using Django 3.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import environ
import os
from django.contrib.messages import constants as messages


# for bootstrap alert
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}


# Build paths inside the taicat like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Build .env to locate private settings
# https://pypi.org/project/python-environ/
env = environ.Env(DEBUG=(bool, False))
config_dir = os.path.join(BASE_DIR, 'conf')
environ.Env.read_env(os.path.join(config_dir, '.env'))

# current mode (development/production)
ENV = env('ENV', default='dev')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Application definition

INSTALLED_APPS = [
    # "sslserver", # for local https
    'base',
    'taicat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conf.urls'


DATA_UPLOAD_MAX_NUMBER_FIELDS = None

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'conf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL'),
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

# local
# STATIC_ROOT = ''
# STATIC_URL = '/static/'
# STATICFILES_DIRS = [os.path.join('static'),]

# web
default_static_dir = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATIC_ROOT = env('STATIC_ROOT', default=default_static_dir)
STATICFILES_DIRS = [default_static_dir, ]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "basdb"
    },
    'file': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/bucket/cache-files',
        'TIMEOUT': None,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


SERIALIZATION_MODULES = {
    "geojson": "django.contrib.gis.serializers.geojson",
}

# email
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_SES_REGION_NAME = env('AWS_SES_REGION_NAME', default='')
AWS_SES_REGION_ENDPOINT = env('AWS_SES_REGION_ENDPOINT', default='')
AWS_S3_BUCKET = env('AWS_S3_BUCKET', default='')

CT_SERVICE_EMAIL = env('CT_SERVICE_EMAIL', default='')
CT_BCC_EMAIL_LIST = env('CT_BCC_EMAIL_LIST', default='')


MEDIA_URL = '/media/'
MEDIA_ROOT = env('MEDIA_ROOT')


ORCID_CLIENT_ID = env('ORCID_CLIENT_ID')
ORCID_CLIENT_SECRET = env('ORCID_CLIENT_SECRET')

# Content Security Policy 
CSP_DEFAULT_SRC = ("'self'", "https://www.google.com/recpatcha/", "https://www.google.com/") 
CSP_STYLE_SRC = ["'self'","https://cdn.datatables.net","https://*.fontawesome.com","https://*.highcharts.com","https://unpkg.com/","http://www.w3.org","https://cdnjs.cloudflare.com", "'unsafe-inline'"]
CSP_IMG_SRC = ("'self'","https://*.highcharts.com", "https://*.fontawesome.com", "data: http://www.w3.org", 'https://*.tile.osm.org/',"https://*.s3.ap-northeast-1.amazonaws.com/","https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/") 
CSP_MEDIA_SRC = ("'self'","https://*.s3.ap-northeast-1.amazonaws.com/","https://d3gg2vsgjlos1e.cloudfront.net/") 
CSP_FONT_SRC = ("'self'", "https://*.fontawesome.com" ) 

CSP_SCRIPT_SRC = ["'self'", "https://cdnjs.cloudflare.com",
    "https://code.jquery.com",
    "https://cdn.datatables.net",
    "https://*.highcharts.com",
    "https://*.fontawesome.com",
    "https://unpkg.com/", "data: http://www.w3.org", "https://www.google.com", "https://www.gstatic.com"
]

CSP_CONNECT_SRC = ("'self'","https://*.fontawesome.com",)

DATA_UPLOAD_MAX_MEMORY_SIZE = 20000000

# via: https://docs.djangoproject.com/en/4.1/topics/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            #'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
            'format': '{levelname} {asctime} {module}.{funcName} #{lineno} {process} {thread} {message}',
        },
        'main': {
            'format': '{levelname} {asctime} {module}.{funcName} #{lineno} {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'filters': {
        #'special': {
        #    '()': 'project.logging.SpecialFilter',
        #    'foo': 'bar',
        #},
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'main'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_true']
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/ct-web/ct-web.log',
            'when': 'W3',
            'backupCount': 7,
            'formatter': 'main'
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.utils.autoreload': {
            'level': 'INFO',
        },
        # 'django.server': {
        #     'handlers': ['django.server'],
        #     'propagate': False,
        #     'level': 'DEBUG',
        # },
        # 'django.request': {
        #     'handlers': ['mail_admins'],
        #     'level': 'ERROR',
        #     'propagate': False,
        # },
        # 'django.db.backends': {
        #     'handlers': ['null'],  # Quiet by default!
        #     'propagate': False,
        #     'level': 'DEBUG',
        # },
        #'myproject.custom': {
        #    'handlers': ['console', 'mail_admins'],
        #    'level': 'INFO',
        #    'filters': ['special']
        #}
    }
}
