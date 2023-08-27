from decouple import config

from .base import *

ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("SMTP_HOST")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_FROM = config("SENDER_EMAIL")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

CELERY_BROKER_URL = config("RABBITMQ_URL")

LOGGING = {}
