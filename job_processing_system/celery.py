# job_processing_system/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_processing_system.settings")

app = Celery("job_processing_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# example periodic task (optional dashboard refresh)
# from celery.schedules import crontab
# app.conf.beat_schedule = {
#     "debug-print-every-midnight": {
#         "task": "jobs.tasks.debug_print",
#         "schedule": crontab(minute=0, hour=0),
#     },
# }
