#!/bin/bash
# When starting the django app container, we need to wait until the postgress DB is ready to receive connections
# (docker-compose "depends_on: - quick-pay-db" is not enough to check that the quick-pay-db is ready)
# This script also accepts a command to be executed after the DB is ready (i.e. migrate, runserver or a script..)
function postgres_ready(){
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(dbname="$DB_NAME", user="$DB_USER", password="$DB_PASSWORD", host="quick-pay-db")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing..."
# Here the received command is executed
exec "$@"
