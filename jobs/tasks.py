# jobs/tasks.py  ───────────────────────────────────────────────
import logging
import time
import traceback
from datetime import datetime

from celery import shared_task
from django.utils import timezone

from .models import Job, JobResult

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_job(self, job_id):
    try:
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            logger.error(f"Job {job_id} not found")
            return {"status": "error", "message": f"Job {job_id} not found"}

        if job.status != "pending":
            logger.warning(f"Job {job_id} has status {job.status}, not executing")
            return {"status": "skipped", "message": f"Job {job.status} not in pending state"}
        
        job.status = "in-progress"
        job.save(update_fields=["status"])
        
        logger.info(f"Executing job {job_id}: {job.name}")
        start_time = time.time()
        
        output = simulate_job_execution(job)

        execution_time = time.time() - start_time
        logger.info(f"Job {job_id} completed in {execution_time:.2f} seconds")

        JobResult.objects.update_or_create(
            job=job,
            defaults={
                "output": output,
                "completed_at": timezone.now(),
            }
        )
        
        job.status = "completed"
        job.save(update_fields=["status"])
        
        return {
            "status": "success", 
            "job_id": job_id,
            "execution_time": execution_time
        }
        
    except Exception as exc:
        logger.error(f"Error executing job {job_id}: {str(exc)}")
        logger.error(traceback.format_exc())
        
        try:
            job = Job.objects.get(id=job_id)
            JobResult.objects.update_or_create(
                job=job,
                defaults={
                    "error_message": str(exc),
                    "completed_at": timezone.now(),
                }
            )

            job.status = "failed"
            job.save(update_fields=["status"])
            
        except Exception as inner_exc:
            logger.error(f"Error updating job status: {str(inner_exc)}")

        try:
            if not isinstance(exc, Job.DoesNotExist):
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
