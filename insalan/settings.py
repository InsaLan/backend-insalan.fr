# flake8: noqa E501
"""
Django settings for insalan project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from os import getenv, path
from pathlib import Path
from sys import argv

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv(
    "DJANGO_SECRET",
    "django-insecure-&s(%0f90_a(wa!hk5w9pzri%+6%46)pjn4tq5xycvk9t7dwe_d",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(getenv("DEV", "0")) == 1

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
PROTOCOL = getenv("HTTP_PROTOCOL", "http")

OUTSIDE_PORT = getenv("NGINX_PORT", "80")
if (OUTSIDE_PORT == "80" and PROTOCOL == "http") or (OUTSIDE_PORT == "443" and PROTOCOL == "https"):
    OUTSIDE_PORT = "" # Don't specify it
else:
    OUTSIDE_PORT = f":{OUTSIDE_PORT}"

# LOGGING Setup
LOGGING = {
    "version":1,
    "disable_existing_loggers":False,
    "handlers":{
        "console":{
                "class":"logging.StreamHandler",
            },
        },
    "root": {
        "handlers": ["console"],
        "level": ["INFO", "DEBUG"][DEBUG]
        },
}

# Allow itself and the frontend
WEBSITE_HOST = getenv("WEBSITE_HOST", "localhost")
ALLOWED_HOSTS = [
    "api." + WEBSITE_HOST,
    WEBSITE_HOST,
    "dev." + WEBSITE_HOST,
]

CSRF_TRUSTED_ORIGINS = [
     PROTOCOL + "://api." + getenv("WEBSITE_HOST", "localhost") + OUTSIDE_PORT,
     PROTOCOL + "://" + getenv("WEBSITE_HOST", "localhost") + OUTSIDE_PORT,
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "insalan.user",
    "insalan.partner",
    "insalan.tournament",
    "insalan.tickets",
    "insalan.cms",
    "insalan.payment",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "insalan.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "insalan.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "USER": getenv("DB_USER", "user") + ("_test" if "test" in argv else ""),
        "NAME": getenv("DB_NAME", "mydb"),
        "PASSWORD": getenv("DB_PASS", "password"),
        "HOST": getenv("DB_HOST", "localhost"),
        "PORT": getenv("DB_PORT", "5432"),
    },
    "cms": {
        "ENGINE": 'djongo',
        "NAME": "cms-db",
        "CLIENT": {
            "password": getenv("MONGODB_PASS", "password"),
            "host": getenv("DB_HOST", "localhost"),
            "port": getenv("DB_MONGO_PORT", "5433"),
            "username": getenv("MONGODB_USER", "admin")
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "user.User"

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

TIME_ZONE = "Europe/Paris"

LANGUAGE_CODE = 'fr'
LOCALE_PATH='locale'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("Anglais")),
    ("fr", _("Français")),
    ("es", _("Espagnol")),
    ("de", _("Allemand")),
]

LOCALE_PATHS = [path.join(BASE_DIR, 'locale')]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "v1/static/"
STATIC_ROOT = "v1/" + getenv("STATIC_ROOT", "static/")
STATICFILES_DIRS = [path.join(BASE_DIR, "assets")]

MEDIA_URL = 'v1/media/'
MEDIA_ROOT = 'v1/' + getenv("MEDIA_ROOT", "media/")

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# Login and logout
LOGIN_URL = ("rest_framework:login",)
LOGIN_REDIRECT_URL = "/v1/"
LOGOUT_URL = "rest_framework:logout"

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://" + getenv("WEBSITE_HOST", "localhost"),
    "https://api." + getenv("WEBSITE_HOST", "localhost"),
    "http://" + getenv("WEBSITE_HOST", "localhost"),
    "http://api." + getenv("WEBSITE_HOST", "localhost"),
    "https://" + getenv("HELLOASSO_HOSTNAME", "localhost") # helloasso has be to trusted

]
CSRF_COOKIE_DOMAIN = '.' + getenv("WEBSITE_HOST", "localhost")
# MAILER SETTINGS
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = getenv("MAIL_HOST", "localhost")
EMAIL_HOST_PASSWORD = getenv("MAIL_PASS", "")
EMAIL_HOST_USER = getenv("MAIL_FROM", "insalan@localhost")
DEFAULT_FROM_EMAIL = getenv("MAIL_FROM", "email@localhost")
EMAIL_PORT = int(getenv("MAIL_PORT", "465"))
EMAIL_USE_SSL = getenv("MAIL_SSL", "true").lower() in ["true", "1", "t", "y", "yes"]
EMAIL_SUBJECT_PREFIX = "[InsaLan] "

# Payment variables
HA_URL = f"https://{format(getenv('HELLOASSO_HOSTNAME', 'api.helloasso-sandbox.com'))}"
HA_ORG_SLUG = getenv("HELLOASSO_ORGANIZATION_SLUG", "insalan-test")
# View URLs (fall back on the front page if needed)
HA_RETURN_URL = getenv("HELLOASSO_RETURN_URL", f"https://{WEBSITE_HOST}/")
HA_ERROR_URL = getenv("HELLOASSO_ERROR_URL", f"https://{WEBSITE_HOST}/")
HA_BACK_URL = getenv("HELLOASSO_BACK_URL", f"https://{WEBSITE_HOST}/")
# OAuth Credentials
HA_OAUTH_CLIENT_SECRET = getenv("HELLOASSO_CLIENT_SECRET")
HA_OAUTH_CLIENT_ID = getenv("HELLOASSO_CLIENT_ID")

# Session cookie settings
SESSION_COOKIE_AGE = int(getenv("SESSION_COOKIE_AGE", "1209600"))
