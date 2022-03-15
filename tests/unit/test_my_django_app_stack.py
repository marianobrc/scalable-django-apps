import aws_cdk as core
import aws_cdk.assertions as assertions

from my_django_app.my_django_app_stack import MyDjangoAppStack

# example tests. To run these tests, uncomment this file along with the example
# resource in my_django_app/my_django_app_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MyDjangoAppStack(app, "my-django-app")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
