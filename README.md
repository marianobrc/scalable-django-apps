# Scalable Django Apps
A sample project for auto-scalable Django apps, ready to be deployed in AWS with Docker and CDK.


At the root of this repository you will find a CDK (v2) project. 

You will find the Django project and more details about how to set up the development environment is inside the `app/` directory.


## The Architecture Features
* A load-balanced, highly-available, auto-scalable Django app running in Amazon ECS+Fargate (a.k.a Serverless Containers).
* Fully-managed Queues and auto-scalable Workers using Amazon SQS and Celery Workers running in Amazon ECS+Fargate.
* A fully-managed serverless database using Amazon Aurora Serverless.
* Static files are stored in a private S3 bucket and served through CloudFront.
* Private Isolated subnets and VPC Endpoints are used for improved security and performance, also allowing to remove NAT GWs.
* Sensitive data such as API KEYs or Passwords are stored in AWS Secrets Manager. Other parameters are stored in AWS SSM Parameter Store.

## DevOps
* IaC support using CDK v2
* CI/CD using CDK Pipelines
* Docker support for local development with `docker-compose`.


## CDK

The entrypoint for the CDK project is app.py.
Other Stacks and stages are defined in `my_django_app/`.

## Prerequisites to work with CDK
- Python 3.6 or later including pip and virtualenv.

- Node.js 10.13.0 or later

- Install the aws client v2:
  
  https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-mac.html
  
- Setup API Keys of an administrator user and set the region running:
  
    `aws configure`

  CDK requires API KEYs with enough permissions to create and destroy resources in your AWS Account. Hence, it's recommended to create a user with `Administrator` role.
 
- Install the cdk client:
  
    `npm install -g aws-cdk`

### Working with CDK
To work with CDK first activate the virtualenv located at `.venv` and install dependencies.

```shell
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
(.venv) $ pip install -r requirements-dev.txt
```

### Bootstrapping
The usage of CDK Pipelines require an extra command, [cdk bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/cli.html#cli-bootstrap), to provision resources used by CDK during the deploy.
This command needs to be executed once per account/region combination as: `cdk bootstrap ACCOUNT-NUMBER/REGION`.

```shell
(.venv) $ cdk bootstrap aws://123456789123/us-east-1
 ⏳  Bootstrapping environment aws://123456789123/us-east-1...
...
 ✅  Environment aws://123456789123/us-east-1 bootstrapped
```

### Deploying to AWS
#### Set up CDK environment variables
The required env vars for CDK can be found in .env.template
You can either set them manually or, if using linux, use the helper script `./scripts/set_env_vars.sh`
```shell
$ cp .env.template .env
# Edit .env and set your values
$ . ./scripts/set_env_vars.sh
```

#### GitHub connection
Create a CodeStar connection in [AWS CodeSuite Console](https://console.aws.amazon.com/codesuite/settings/connections) and link it to the GitHub repo so it can be used to trigger CI/CD pipelines.

The connection arn must be stored as a parameter to be used later.

#### Parameters
Parameters containing non-sensitive data are sotred in AWS System Manager Parameter Store.
The required parameters are listed in `.parameters.template.json`.
These parameters can be manually created from the AWS Console, or using the helper script `scripts/set_parameters.py`:
```shell
(.venv) $ python ./scripts/set_parameters.py .parameters.json 
Settings parameters in AWS..
...  # Parameters or Errors will be printed out
Finished.
```

#### Secrets
Sensitive information is stored encrypted in AWS Secrets Manager.

The required secrets are listed in `.secrets.template.json`.
These secrets can be manually created from the AWS Console, or using the helper script `scripts/set_parameters.py` with the `--secret` option:
```shell
(.venv) $ cp .secrets.template.json .secrets.json
# Replace the placeholders with your secret values
(.venv) $ python ./scripts/set_parameters.py --secret .secrets.json 
Settings parameters in AWS..
...  # Parameters or Errors will be printed out
Finished.
```

#### Deploying
IMPORTANT: Before deploying the pipeline you need to set the secrets and parameters described above with your own values. You also need to set your own domain and SSL certificate.

Now you can deploy de CI/CD Pipeline:
```shell
$ cdk deploy MyDjangoAppPipeline
```
CDK will ask for confirmation before creating roles, policies and security groups. Enter 'y' for yes and the deployment process will start.You will see the deployment progress in your shell and once finished you will see the pipeline in the CodePipeline panel at the AWS Console.

After the pipeline is deployed it will be triggered and all the stacks will be created. You can monitor the stacks creation in the CloudFormation panel at  the AWS Console.

This is the only time you need to run the deploy command. The next time you commit any changes in the infrastructure code, or the app code, the pipepile will update the infrastructure and will update the ecs services as needed.

# License
You are free to use, copy or distribute this code. Knowledge is meant to be shared :)

THIS SOFTWARE COMES WITH NO WARRANTIES, USE AT YOUR OWN RISK

Enjoy!
=======
