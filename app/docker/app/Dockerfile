# Base off the official python image
# Define a common stage to dev and prod images called base
FROM python:3.10 as base
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Add the path where python packages are installed, to the path
#ENV PATH="/home/web/.local/bin/:${PATH}"
# Create a user to avoid running containers as root in production
RUN addgroup --system web \
    && adduser --system --ingroup web web
# Install os-level dependencies (as root)
RUN apt-get update && apt-get install -y -q --no-install-recommends \
  # dependencies for building Python packages
  build-essential \
  # postgress client (psycopg2) dependencies
  libpq-dev \
  # cleaning up unused files to reduce the image size
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*
# Install python dependencies
COPY ./requirements/base.txt /requirements/base.txt
RUN pip install --no-cache-dir -r /requirements/base.txt
# Switch to the non-root user
USER web
# Create working directory
RUN mkdir /home/web/code
# Switch to the working directory
WORKDIR /home/web/code/
# Copy entrypoint script which waits for the db to be ready
COPY ./docker/app/entrypoint.sh /entrypoint.sh
# Switch to the root user temporary, to grant execution permissions.
USER root
RUN chmod +x /entrypoint.sh
USER web
# This script will run before every command executed in the container
ENTRYPOINT ["/entrypoint.sh"]


# Define an image for local development. Inherits common packages from the base stage.
FROM base as dev
# Copy the scripts that starts the development application server (runserver)
COPY ./docker/app/start-dev-server.sh /start-dev-server.sh
USER root
RUN chmod +x /start-dev-server.sh  # Permisions to run the dev server
USER web
# The development server starts by default when the container starts
CMD ["/start-dev-server.sh"]


# Define an image for production. Inherits common packages from the base stage.
FROM base as prod
# Install extra packages required in production
USER root
COPY ./requirements/prod.txt /requirements/
RUN pip install --no-cache-dir -r /requirements/prod.txt
USER web
# Copy the script that starts the production application server (gunicorn)
COPY ./docker/app/start-prod-server.sh /start-prod-server.sh
USER root
RUN chmod +x /start-prod-server.sh
USER web
# Copy the source code of our django app
COPY --chown=web:web . /home/web/code/
# The production server starts by default when the container starts
CMD ["/start-prod-server.sh"]
