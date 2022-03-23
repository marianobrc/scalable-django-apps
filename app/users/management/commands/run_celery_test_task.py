from django.core.management import BaseCommand
from ...tasks import test_task


class Command(BaseCommand):
    help = "Trigger a test task with celery"

    def handle(self, *args, **options):
        print(f"Starting test task..")
        test_task.delay()
        print(f"Task msg sent successfully")
