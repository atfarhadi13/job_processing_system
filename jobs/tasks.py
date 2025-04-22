import time
from celery import shared_task, current_task
from django.utils import timezone
from .models import Job, JobResult

@shared_task(bind=True, ignore_result=True)
def process_job(self, job_id):
    job = Job.objects.get(pk=job_id)
    job.status = Job.STATUS_CHOICES[1][0]
    job.save(update_fields=['status'])

    try:
        time.sleep(10)
        output = f"Processed job {job.id} ({job.name}) at {timezone.now()}"

        JobResult.objects.create(
            job=job,
            output=output,
            completed_at=timezone.now()
        )
        job.status = Job.STATUS_CHOICES[2][0]
        job.save(update_fields=['status'])

    except Exception as exc:
        JobResult.objects.create(
            job=job,
            error_message=str(exc),
            completed_at=timezone.now()
        )
        job.status = Job.STATUS_CHOICES[3][0]
        job.save(update_fields=['status'])
        raise