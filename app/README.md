This is a template project for Dockerized Django apps.

## Prerequisites

- [X] Docker & Docker Compose - [instructions](https://docs.docker.com/compose/install/)


Notice: Windows support was not tested but should work if environment variables are set properly.

## Development environment with Docker & Docker Compose

All the files required to run docker & docker-compose are at the `docker/` directory, grouped by service.


The system is composed by the following services (docker-compose.yml): 
* `db`:  The PostresSQL database, used by the Django app and eventually by the workers.
* `app`:  The Django app.
* `broker`:  SQS broker holding queues and managing messages between the app and the workers.
* `worker-default`:  A Celery worker processing messages in the default queue.

`docker-compose` is used as the local orchestrator.
Each service run in a docker container, and they all share a common docker network.

### Environment variables for local development
First create a local file for env vars called .env, at the docker folder (next to docker-compose.yml).
The variables needed can be found in .env.template .
These environment variables will be automatically loaded by docker-compose while starting containers for the different services.

### Running services locally
All services required to run the project have been dockerized and can be initiated with the generic `docker-compose up`, as seen below:
```shell
$ COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose up -d --build  # Use Docker Buildkit for multi-stage builds
Creating network "docker_default" with the default driver
Creating volume "docker_postgres_data" with default driver
Building app
[+] Building 4.0s (17/17) FINISHED                                                                                                                         
 => [internal] load build definition from Dockerfile                                                                                                  0.5s
 => => transferring dockerfile: 38B                                                                                                                   0.0s
 => [internal] load .dockerignore                                                                                                                     2.2s
 => => transferring context: 2B                                                                                                                       0.0s
 => [internal] load metadata for docker.io/library/python:3.10                                                                                        0.0s
 => [base  1/10] FROM docker.io/library/python:3.10                                                                                                   0.0s
 => [internal] load build context                                                                                                                     0.3s
 => => transferring context: 276B                                                                                                                     0.0s
 => CACHED [base  2/10] RUN addgroup --system web     && adduser --system --ingroup web web                                                           0.0s
 => CACHED [base  3/10] RUN apt-get update && apt-get install -y -q --no-install-recommends   build-essential   libpq-dev   && apt-get purge -y --au  0.0s
 => CACHED [base  4/10] WORKDIR /home/web/code/                                                                                                       0.0s
 => CACHED [base  5/10] COPY --chown=web:web ./requirements/base.txt requirements/base.txt                                                            0.0s
 => CACHED [base  6/10] RUN pip install --no-cache-dir -r requirements/base.txt                                                                       0.0s
 => CACHED [base  7/10] COPY --chown=web:web ./docker/app/entrypoint.sh /usr/local/bin/entrypoint.sh                                                  0.0s
 => CACHED [base  8/10] RUN chmod +x /usr/local/bin/entrypoint.sh                                                                                     0.0s
 => CACHED [base  9/10] COPY --chown=web:web ./docker/app/start-celery-worker.sh /usr/local/bin/start-celery-worker.sh                                0.0s
 => CACHED [base 10/10] RUN chmod +x /usr/local/bin/start-celery-worker.sh                                                                            0.0s
 => CACHED [dev 1/2] COPY --chown=web:web ./docker/app/start-dev-server.sh /usr/local/bin/start-dev-server.sh                                         0.0s
 => CACHED [dev 2/2] RUN chmod +x /usr/local/bin/start-dev-server.sh                                                                                  0.0s
 => exporting to image                                                                                                                                1.1s
 => => exporting layers                                                                                                                               0.0s
 => => writing image sha256:c3f1d7aa49a371cd7f54f2925e745867cb054f3819e666d8051b569b1b5f725e                                                          0.0s
 => => naming to docker.io/library/docker_app                                                                                                         0.0s
Building worker-default
[+] Building 2.5s (17/17) FINISHED                                                                                                                         
 => [internal] load build definition from Dockerfile                                                                                                  0.7s
 => => transferring dockerfile: 38B                                                                                                                   0.0s
 => [internal] load .dockerignore                                                                                                                     0.8s
 => => transferring context: 2B                                                                                                                       0.0s
 => [internal] load metadata for docker.io/library/python:3.10                                                                                        0.0s
 => [base  1/10] FROM docker.io/library/python:3.10                                                                                                   0.0s
 => [internal] load build context                                                                                                                     0.3s
 => => transferring context: 276B                                                                                                                     0.0s
 => CACHED [base  2/10] RUN addgroup --system web     && adduser --system --ingroup web web                                                           0.0s
 => CACHED [base  3/10] RUN apt-get update && apt-get install -y -q --no-install-recommends   build-essential   libpq-dev   && apt-get purge -y --au  0.0s
 => CACHED [base  4/10] WORKDIR /home/web/code/                                                                                                       0.0s
 => CACHED [base  5/10] COPY --chown=web:web ./requirements/base.txt requirements/base.txt                                                            0.0s
 => CACHED [base  6/10] RUN pip install --no-cache-dir -r requirements/base.txt                                                                       0.0s
 => CACHED [base  7/10] COPY --chown=web:web ./docker/app/entrypoint.sh /usr/local/bin/entrypoint.sh                                                  0.0s
 => CACHED [base  8/10] RUN chmod +x /usr/local/bin/entrypoint.sh                                                                                     0.0s
 => CACHED [base  9/10] COPY --chown=web:web ./docker/app/start-celery-worker.sh /usr/local/bin/start-celery-worker.sh                                0.0s
 => CACHED [base 10/10] RUN chmod +x /usr/local/bin/start-celery-worker.sh                                                                            0.0s
 => CACHED [dev 1/2] COPY --chown=web:web ./docker/app/start-dev-server.sh /usr/local/bin/start-dev-server.sh                                         0.0s
 => CACHED [dev 2/2] RUN chmod +x /usr/local/bin/start-dev-server.sh                                                                                  0.0s
 => exporting to image                                                                                                                                1.0s
 => => exporting layers                                                                                                                               0.0s
 => => writing image sha256:c3f1d7aa49a371cd7f54f2925e745867cb054f3819e666d8051b569b1b5f725e                                                          0.1s
 => => naming to docker.io/library/worker-default                                                                                                     0.0s
Creating docker_db_1     ... done
Creating docker_broker_1 ... done
Creating docker_worker-default_1 ... done
Creating docker_app_1            ... done
```
After a successful start you will see:
* The Django app is available at `http://127.0.0.1:8000` (Port exposed at docker-compose)
* A status check endpoint is available at `http://127.0.0.1:8000/status/`
* Django Admin Panel is available at `http://127.0.0.1:8000/admin/`
* An SQS Monitoring UI is available at `http://127.0.0.1:9325/`


#### Automatic actions executed on services start:
* `db`: At volume creation, the script /db.sql is ran to create a PostgreSQL user and database.
* `app`: 
    * There is an entry point script to check and wait until the db is ready. It's normal to have three or four 
    retries the first time until the db is ready to accept connection. 
    * Migrations are applied running `python manage.py migrate`.
    * The development server is started running `python manage.py runserver 0.0.0.0:8000`.
* `broker`: The default queue is initialized.
* `worker-default`: The celery worker tries to connect to the broker. In case of failure it retries applying a back-off policy (in 2s, in 4s, in 8s..). It's normal to have two or three retries until the broker starts accepting connections.
 
### View the logs
The `docker-compose up` command aggregates the output of each container. When the command exits, all containers are stopped. 
Running `docker-compose up -d` starts the containers in the background and leaves them running.

#### How do I see the logs for a single service?
Run `docker-compose logs [-f] <service>` 
```shell
$ docker-compose logs -f app
Attaching to docker_app_1
app_1             | Trying to connect to database 'db_dev' on host 'db'..
app_1             | could not connect to server: Connection refused
app_1             | 	Is the server running on host "db" (172.27.0.3) and accepting
app_1             | 	TCP/IP connections on port 5432?
app_1             | 
app_1             | Postgres is unavailable - sleeping
app_1             | Trying to connect to database 'db_dev' on host 'db'..
app_1             | Postgres is up - continuing...
app_1             | Running migrations..
app_1             | Loading CELERY app with settings from app.settings.local
app_1             | Operations to perform:
app_1             |   Apply all migrations: admin, auth, contenttypes, sessions, users
app_1             | Running migrations:
app_1             |   Applying contenttypes.0001_initial... OK
app_1             |   Applying contenttypes.0002_remove_content_type_name... OK
app_1             |   Applying auth.0001_initial... OK
app_1             |   Applying auth.0002_alter_permission_name_max_length... OK
app_1             |   Applying auth.0003_alter_user_email_max_length... OK
app_1             |   Applying auth.0004_alter_user_username_opts... OK
app_1             |   Applying auth.0005_alter_user_last_login_null... OK
app_1             |   Applying auth.0006_require_contenttypes_0002... OK
app_1             |   Applying auth.0007_alter_validators_add_error_messages... OK
app_1             |   Applying auth.0008_alter_user_username_max_length... OK
app_1             |   Applying auth.0009_alter_user_last_name_max_length... OK
app_1             |   Applying auth.0010_alter_group_name_max_length... OK
app_1             |   Applying auth.0011_update_proxy_permissions... OK
app_1             |   Applying auth.0012_alter_user_first_name_max_length... OK
app_1             |   Applying users.0001_initial... OK
app_1             |   Applying admin.0001_initial... OK
app_1             |   Applying admin.0002_logentry_remove_auto_add... OK
app_1             |   Applying admin.0003_logentry_add_action_flag_choices... OK
app_1             |   Applying sessions.0001_initial... OK
app_1             | Starting server..
app_1             | Loading CELERY app with settings from app.settings.local
app_1             | Loading CELERY app with settings from app.settings.local
app_1             | Watching for file changes with StatReloader
app_1             | Watching for file changes with StatReloader
app_1             | Performing system checks...
app_1             | 
app_1             | System check identified no issues (0 silenced).
app_1             | April 10, 2022 - 14:36:05
app_1             | Django version 4.0.2, using settings 'app.settings.local'
app_1             | Starting development server at http://0.0.0.0:8000/
app_1             | Quit the server with CONTROL-C.
```

### Hot reloading
* backend supports hot reloading.
* local changes are synched with the containers via volumes.
* celery workers don't support hot-reloading and they need to be restarted manually.

### Managing services & docker containers

#### How do I reset the database?
    * Stop the services and delete the volumes: `docker-compose down --volumes`
    * Start the services again: `docker-compose up`
    
#### How do I see the status of each service?
Using docker-compose:
`docker-compose ps`
```shell
$ docker-compose ps
             Name                            Command               State                           Ports                        
--------------------------------------------------------------------------------------------------------------------------------
docker_app_1              entrypoint.sh start-dev-se ...   Up      0.0.0.0:8000->8000/tcp                        
docker_broker_1           /sbin/tini -- /opt/docker/ ...   Up      0.0.0.0:9324->9324/tcp, 0.0.0.0:9325->9325/tcp
docker_db_1               docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp                        
docker_worker-default_1   entrypoint.sh start-celery ...   Up                                                    
```
Using docker:
`docker ps`
```shell
$ docker ps
CONTAINER ID        IMAGE                    COMMAND                  CREATED             STATUS              PORTS                                                   NAMES
75e428f6ea24   docker_app                      "entrypoint.sh start…"   8 minutes ago   Up 8 minutes   0.0.0.0:8000->8000/tcp             docker_app_1
531d4131159c   worker-default                  "entrypoint.sh start…"   8 minutes ago   Up 8 minutes                                      docker_worker-default_1
d8e46eb8aa6b   softwaremill/elasticmq-native   "/sbin/tini -- /opt/…"   9 minutes ago   Up 9 minutes   0.0.0.0:9324-9325->9324-9325/tcp   docker_broker_1
b88fecb94bab   postgres:10                     "docker-entrypoint.s…"   9 minutes ago   Up 8 minutes   0.0.0.0:5432->5432/tcp             docker_db_1                                              
```

#### How do I run a command in a service container?
Using docker-compose:
`docker-compose exec <service> <command>`
```shell
# Open a bash shell inside the container
$ docker-compose exec app bash
web@75e428f6ea24:~/code$
```
Using docker:
`docker exec -it <container> <command>`
```shell
# docker_app_1 is the name of the running Docker container, found with docker ps.
$ docker exec -it docker_app_1 /bin/bash
web@75e428f6ea24:~/code$
```

#### How can I restart or stop a single service?
Restart can be useful if one specific service gets unresponsive or gets into some unrecoverable error state.
Using docker-compose:
`docker-compose restart <service>`
```shell
$ docker-compose restart worker-default 
Restarting docker_worker-default_1 ... done
```

Stopping the backend service can be useful if you want to run it locally for debugging.
`docker-compose restart <service>`
```shell
$ docker-compose stop app
Stopping app_1 ... done
```
