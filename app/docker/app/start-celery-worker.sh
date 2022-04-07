#!/bin/sh
echo "CELERY_BROKER_URL: ${CELERY_BROKER_URL}"
celery -A app worker -Q $1 -l info
