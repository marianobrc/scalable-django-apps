#!/bin/sh
ls -alh
celery -A app worker -Q $1 -l info
