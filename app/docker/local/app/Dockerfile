# Pull base image
FROM python:3.8

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /code

# Install os-level dependencies
RUN apt-get update && apt-get install -y -q --no-install-recommends \
  # dependencies for building Python packages
  build-essential \
  # postgress client (psycopg2) dependencies
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --upgrade pip
COPY ./requirements/base.txt /code/requirements/
RUN pip install --no-cache-dir -r ./requirements/base.txt

# Copy project
COPY . /code/

# Copy entrypoint script which waits for the db to be ready
COPY ./docker/local/app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy the scripts that serves the backend (applying migrations)
COPY ./docker/local/app/start-dev-server.sh /start-dev-server.sh
RUN chmod +x /start-dev-server.sh

ENTRYPOINT ["/entrypoint.sh"]
