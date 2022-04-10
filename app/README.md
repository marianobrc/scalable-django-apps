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
The variables needed can be found in .env.template
These environment variables will be automatically loaded by docker-compose while starting containers for the different services.

### Running services locally
All services required to run the project have been dockerized and initiated with the generic `docker-compose up`, as seen below:
```shell
$ cd docker/ # Move to the directory where the docker files are placed
$ . ../scripts/set_env_vars.sh  # Set env vars in the current console (you can set them differently)
>>>>>>>>>>>>>>>>>>ToDo
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
ToDo
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
ToDo
```
Using docker:
`docker ps`
```shell
$ docker ps
CONTAINER ID        IMAGE                    COMMAND                  CREATED             STATUS              PORTS                                                   NAMES
                                                       
```

#### How do I run a command in a service container?
Using docker-compose:
`docker-compose exec <service> <command>`
```shell
# Open a bash shell inside the container
$ docker-compose exec app bash
```
Using docker:
`docker exec -it <container> <command>`
```shell
$ docker exec -it app_1 /bin/bash
Where app_1 is the name of the running Docker container, found with docker ps.
```

#### How can I restart or stop a single service?
Restart can be useful if one specific service gets unresponsive or gets into some unrecoverable error state.
Using docker-compose:
`docker-compose restart <service>`
```shell
$ docker-compose restart app
Restarting app_1 ... done
```

Stopping the backend service can be useful if you want to run it locally for debugging.
`docker-compose restart <service>`
```shell
$ docker-compose stop app
Stopping app_1 ... done
```
