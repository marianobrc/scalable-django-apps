""""
    On this file we define an instance of the Celery app.
    reference: https://docs.celeryproject.org/en/stable/django/first-steps-with-django.html
"""
from __future__ import absolute_import, unicode_literals

import os

from celery import Celery


# set the default Django settings module for the 'celery' program.
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quickpay.settings.local")
print(f"Loading CELERY app with settings from {os.getenv('DJANGO_SETTINGS_MODULE')}")
app = Celery("app")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
#print(f"CELERY CONFIG:\n {app.conf.humanize(with_defaults=False, censored=True)}")
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
