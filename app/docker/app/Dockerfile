# Pull base image
FROM python:3.10 as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Add the path where python packages are installed, to the path
ENV PATH="/home/apps-user/.local/bin/:${PATH}"

# Create a user to avoid running containers as root in production
RUN addgroup --system apps \
    && adduser --system --ingroup apps apps-user

# Install os-level dependencies (as root)
RUN apt-get update && apt-get install -y -q --no-install-recommends \
  # dependencies for building Python packages
  build-essential \
  # postgress client (psycopg2) dependencies
  libpq-dev \
  # cleaning up unused files to reduce the image size
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Switch to the non-root user
USER apps-user

# Set working directory
WORKDIR /code

# Install python dependencies
RUN pip install --upgrade pip
COPY ./requirements/base.txt /code/requirements/
RUN pip install --no-cache-dir -r ./requirements/base.txt

# Copy entrypoint script which waits for the db to be ready
COPY ./docker/app/entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER apps-user
ENTRYPOINT ["/entrypoint.sh"]

# One image for local development
FROM base as dev

# Copy the scripts that serves the backend (applying migrations)
COPY ./docker/app/start-dev-server.sh /start-dev-server.sh
USER root
RUN chmod +x /start-dev-server.sh
USER apps-user

CMD ["/start-dev-server.sh"]

# Another image for local production
FROM base as prod

# Install extra packages required in production
COPY ./requirements/prod.txt /code/requirements/
RUN pip install --no-cache-dir -r ./requirements/prod.txt

# Copy the scripts that serves the backend (applying migrations)
COPY ./docker/app/start-prod-server.sh /start-prod-server.sh
# Grant execution permissions
USER root
RUN chmod +x /start-prod-server.sh
USER apps-user

# Copy the source code
COPY . /code/

# Default command starts the web server
CMD ["/start-prod-server.sh"]

