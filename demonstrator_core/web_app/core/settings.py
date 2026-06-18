
import os

import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, True)
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env.example'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# Assets Management
ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets') 

# load production server from .env
ALLOWED_HOSTS        = ['localhost', 'localhost:85', '127.0.0.1',               env('SERVER', default='127.0.0.1') ]
CSRF_TRUSTED_ORIGINS = ['http://localhost:85', 'http://127.0.0.1', 'https://' + env('SERVER', default='127.0.0.1') ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'web_app.apps.authentication',
    'web_app.apps.entsoe',
    'web_app.apps.demonstrator',
    'web_app.apps.awattar.apps.AwattarConfig',
    'web_app.apps.predictions',
    'web_app.apps.consumption',
    'common_models.common_models_app.apps.CommonModelsConfig',
    'consumer.kafka_consumer.apps.KafkaConsumerConfig',
]

print("LOADING SETTINGS FROM:", __file__)
print("INSTALLED_APPS HAS common_models?:", any("common_models" in a for a in INSTALLED_APPS))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web_app.core.urls'
LOGIN_REDIRECT_URL = "/login/"
LOGOUT_REDIRECT_URL = "/logout/"
TEMPLATE_DIR = os.path.join(CORE_DIR, "apps/templates")  # ROOT dir for templates
SESSION_EXPIRE_AT_BROWSER_CLOSE = True # Session expire


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'web_app.apps.context_processors.cfg_assets_root',
            ],
        },
    },
]

WSGI_APPLICATION = 'web_app.core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

import os

DATABASES = {   
        'default': {  
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.getenv('TIMESCALEDB_NAME', 'timescale'),
           'USER': os.getenv('TIMESCALEDB_USERNAME', 'postgres'),
           'PASSWORD': os.getenv('TIMESCALEDB_PASSWORD', 'eddie'),
           'HOST': os.getenv('TIMESCALEDB_HOST', 'timescale'),
           'PORT': os.getenv('TIMESCALEDB_PORT', '5432'),
        },
}


print("Using database:", DATABASES['default'])

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

#############################################################
# SRC: https://devcenter.heroku.com/articles/django-assets

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(CORE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(CORE_DIR, 'apps/static'),
)


#############################################################
#############################################################

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': (
                '\x1b[90m[%(asctime)s]\x1b[0m '
                '%(log_color)s%(levelname)-8s%(reset)s '
                '\x1b[90m%(name)s:%(lineno)d\x1b[0m '  
                '%(message)s'
            ),
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': {
                'DEBUG': 'light_black',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
        },
        'plain': {
            'format': (
                '[{asctime}] '
                '{levelname:<8} '
                '{name}:{lineno} '
                '{message}'
            ),
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored' if DEBUG else 'plain',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG' if DEBUG else 'INFO',
    },
    'loggers': {
        'django.server': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'kafka': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


