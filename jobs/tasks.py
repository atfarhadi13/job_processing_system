import time
from celery import shared_task
from django.utils import timezone
from django.core.cache import caches

from .models import Job, JobResult

state_cache = caches['job_state']


@shared_task(ignore_result=True)
def start_job(job_id):
    job = Job.objects.get(pk=job_id)
    job.status = Job.STATUS_CHOICES[1][0]
    job.save(update_fields=['status'])

    state_cache.set(f"job:{job_id}", 'in-progress')


@shared_task(ignore_result=True)
def complete_job(job_id):
    """
    1) Mark in-progress → completed
    2) Write a JobResult
    3) Remove from Redis
    """
    job = Job.objects.get(pk=job_id)
    if state_cache.get(f"job:{job_id}") != 'in-progress':
        return
    
    time.sleep(1)

    JobResult.objects.create(
        job=job,
        output=f"Manually completed at {timezone.now()}",
        completed_at=timezone.now()
    )

    job.status = Job.STATUS_CHOICES[2][0]
    job.save(update_fields=['status'])

    state_cache.delete(f"job:{job_id}")


@shared_task(ignore_result=True)
def cancel_job(job_id):
    job = Job.objects.get(pk=job_id)
    if state_cache.get(f"job:{job_id}") != 'in-progress':
        return

    JobResult.objects.create(
        job=job,
        error_message="Cancelled by user",
        completed_at=timezone.now()
    )
    job.status = Job.STATUS_CHOICES[3][0]
    job.save(update_fields=['status'])

    state_cache.delete(f"job:{job_id}")