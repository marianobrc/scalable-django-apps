# Scalable Django Apps
A sample project for auto-scalable Django apps, ready to be deployed in AWS with Docker and CDK.

## The Architecture Features
* A load-balanced, highly-available, auto-scalable Django app running in Amazon ECS+Fargate (a.k.a Serverless Containers).
* Fully-managed Queues and auto-scalable Workers using Amazon SQS and Celery Workers running in Amazon ECS+Fargate.
* A fully-managed serverless database using Amazon Aurora Serverless.
* Static files stored in a private S3 bucket and served through CloudFront.
* Private Isolated subnets and VPC Endpoints are used for improved security and performance, also allowing to remove NAT GWs.
* Sensitive data such as API KEYs or Passwords are stored in AWS Secrets Manager. Other parameters are stored in AWS SSM Parameter Store.

## DevOps
* IaC support using CDK v2
* CI/CD using CDK Pipelines
* Docker support for local development with `docker-compose`.

# The Repository Structure

At the root of this repository you will find a CDK (v2) project. 

You will find the Django project and more details about how to set up the development environment is inside the `app/` directory.

## CDK

The entrypoint for the CDK project is app.py.
Other Stacks and stages are defined in `my_django_app/`.

## Prerequisites to work with CDK
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
$ cdk bootstrap aws://123456789123/us-east-2
 ⏳  Bootstrapping environment aws://123456789123/us-east-2...
...
 ✅  Environment aws://123456789123/us-east-2 bootstrapped
```

### Deploying to AWS
#### Set up CDK env vars
Set the following env vars:
```shell
CDK_DEFAULT_ACCOUNT=111111111111
CDK_DEFAULT_REGION=us-east-1
```

Set the following secrets and parameters in the AWS Console
#### Secrets
```shell
>>>>>>>>>>>>>>>>>>ToDo
```
#### Parameters
```shell
>>>>>>>>>>>>>>>>>>ToDo
```
#### Deploying
Now you can deploy de CI/CD Pipeline:
```shell
$ cdk deploy MyDjangoAppPipeline
```
CDK will ask for confirmation before creating roles, policies and security groups. Enter 'y' for yes and the deployment process will start.You will see the deployment progress in your shell and once finished you will see the pipeline in the CodePipeline panel at the AWS Console.

After the pipeline is deployed it will be triggered and all the stacks will be created. You can monitor the stacks creation in the CloudFormation panel at  the AWS Console.

This is the only time you need to run the deploy command. The next time you commit any changes in the infrastructure code, or the app code, the pipepile will update the infrastructure and will update the ecs services as needed.


Enjoy!
=======
