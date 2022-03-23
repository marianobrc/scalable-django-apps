from celery import shared_task


@shared_task
def test_task():
    print("This is a test task running with celery!")
