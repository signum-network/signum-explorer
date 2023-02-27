# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
import os
from .celery import app as celery_app
from django.conf import settings
from config.settings import APP_ENV

if APP_ENV == "production":
    __all__ = ("celery_app",)