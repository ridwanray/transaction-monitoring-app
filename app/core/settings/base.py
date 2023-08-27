"""
Django settings for Transaction-Monitoring project.
"""
import os
from datetime import timedelta
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool)

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party Apps
    "corsheaders",
    "drf_spectacular",
    "core.celery.CeleryConfig",
    # Local Apps
    "monitoring",
]

# USER MODEL
AUTH_USER_MODEL = "monitoring.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

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

STATIC_URL = "static/"
STATIC_ROOT = "static/"

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"
CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["https://*.hereconomy.com"]
LOGIN_URL = "rest_framework:login"
LOGOUT_URL = "rest_framework:logout"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "core.pagination.CustomPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True
TIME_ZONE = "Africa/Lagos"

CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
FLOWER_BASIC_AUTH = os.environ.get("FLOWER_BASIC_AUTH")

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
}

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "DEFAULT_GENERATOR_CLASS": "drf_spectacular.generators.SchemaGenerator",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_PATCH": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "displayRequestDuration": True,
    },
    "UPLOADED_FILES_USE_URL": True,
    "TITLE": "Real-time Transaction Monitoring App",
    "DESCRIPTION": "Real-time Transaction Monitoring App",
    "VERSION": "0.2.0",
    "LICENCE": {"name": "BSD License"},
    "CONTACT": {"name": "Ridwanray", "email": "alabarise@gmail.com"},
    # OAUTH2 SPEC
    "OAUTH2_FLOWS": [],
    "OAUTH2_AUTHORIZATION_URL": None,
    "OAUTH2_TOKEN_URL": None,
    "OAUTH2_REFRESH_URL": None,
    "OAUTH2_SCOPES": None,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/debug.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
