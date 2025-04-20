import logging
import time
import traceback
from datetime import datetime

from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import Job, JobResult

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_job(self, job_id):
    try:
        job = Job.objects.get(id=job_id)

        now = timezone.now()
        if job.scheduled_time > now:
            delay_seconds = (job.scheduled_time - now).total_seconds()
            logger.info(f"Job {job_id} scheduled for future execution after {delay_seconds:.1f}s")
            time.sleep(delay_seconds)

        if job.status != "pending":
            logger.warning(f"Job {job_id} has status '{job.status}', skipping execution.")
            return {"status": "skipped", "message": f"Job {job.status} not pending"}

        job.status = "in-progress"
        job.save(update_fields=["status"])
        logger.info(f"Job {job_id} status set to in-progress.")

        start_time = time.time()
        output = simulate_job_execution(job)
        execution_time = time.time() - start_time

        JobResult.objects.update_or_create(
            job=job,
            defaults={
                "output": output,
                "completed_at": timezone.now(),
            }
        )

        job.status = "completed"
        job.save(update_fields=["status"])
        logger.info(f"Job {job_id} status set to completed.")

        return {
            "status": "success",
            "job_id": job_id,
            "execution_time": execution_time
        }

    except ObjectDoesNotExist:
        logger.error(f"Job {job_id} not found.")
        return {"status": "error", "message": f"Job {job_id} not found"}

    except Exception as exc:
        logger.error(f"Error executing job {job_id}: {str(exc)}")
        JobResult.objects.update_or_create(
            job_id=job_id,
            defaults={
                "error_message": str(exc),
                "completed_at": timezone.now(),
            }
        )
        Job.objects.filter(id=job_id).update(status="failed")
        try:
            raise self.retry(exc=exc, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for job {job_id}")

        return {"status": "error", "message": str(exc)}

def simulate_job_execution(job):
    time.sleep(2)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = f"Job executed at {current_time}\n"
    output += f"Job name: {job.name}\n"
    if job.description:
        output += f"Description: {job.description}\n"
    output += "Job completed successfully."
    return output
