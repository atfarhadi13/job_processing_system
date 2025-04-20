import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_processing_system.settings')

app = Celery('job_processing_system')


app.config_from_object(f'django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')