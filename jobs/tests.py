from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from jobs.models import Job, JobResult
from authentication.models import CustomUser


class JobApiTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="test@example.com",
            email="test@example.com", 
            password="SecurePass123", 
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)
        
        self.jobs_url = reverse('jobs:job-list')
        self.summary_url = reverse('jobs:job-summary')
        
        self.future_time = timezone.now() + timedelta(minutes=5)
        self.valid_job_data = {
            "name": "Test Job",
            "description": "A job for testing",
            "scheduled_time": self.future_time.isoformat()
        }
    
    def tearDown(self):
        Job.objects.all().delete()
        JobResult.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_create_future_job_and_cancel(self):
        response = self.client.post(self.jobs_url, self.valid_job_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job_id = response.data["id"]
        
        job = Job.objects.get(id=job_id)
        self.assertEqual(job.status, "pending")
        
        cancel_url = reverse('jobs:job-detail', args=[job_id])
        response = self.client.delete(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        job.refresh_from_db()
        self.assertEqual(job.status, "failed")

    def test_past_time_rejected(self):
        past_data = {
            "name": "Past Job",
            "description": "This should be rejected",
            "scheduled_time": (timezone.now() - timedelta(minutes=1)).isoformat()
        }
        response = self.client.post(self.jobs_url, past_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("scheduled_time", response.data)
    
    @patch('jobs.tasks.execute_job.apply_async')
    def test_job_execution_scheduled(self, mock_apply_async):
        self.client.post(self.jobs_url, self.valid_job_data, format="json")
        mock_apply_async.assert_called_once()
        
    def test_job_result_access(self):
        job = Job.objects.create(
            user=self.user, 
            name="Completed Job", 
            description="This job is complete", 
            scheduled_time=self.future_time,
            status="completed"
        )
        result = JobResult.objects.create(
            job=job,
            output="Job completed successfully",
            completed_at=timezone.now()
        )
        
        result_url = reverse('jobs:job-result', args=[job.id])
        response = self.client.get(result_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["output"], "Job completed successfully")
    
    def test_job_result_not_available(self):
        job = Job.objects.create(
            user=self.user, 
            name="Pending Job", 
            description="This job is pending", 
            scheduled_time=self.future_time,
            status="pending"
        )
        
        result_url = reverse('jobs:job-result', args=[job.id])
        response = self.client.get(result_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_job_summary(self):
        Job.objects.create(user=self.user, name="Job 1", scheduled_time=self.future_time, status="pending")
        Job.objects.create(user=self.user, name="Job 2", scheduled_time=self.future_time, status="in-progress")
        Job.objects.create(user=self.user, name="Job 3", scheduled_time=self.future_time, status="completed")
        Job.objects.create(user=self.user, name="Job 4", scheduled_time=self.future_time, status="completed")

        response = self.client.get(self.summary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.data["pending"], 1)
        self.assertEqual(response.data["in-progress"], 1)
        self.assertEqual(response.data["completed"], 2)
        self.assertEqual(response.data["failed"], 0)
    
    def test_permission_checks(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.jobs_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        unverified_user = CustomUser.objects.create_user(
            username="unverified@example.com",
            email="unverified@example.com", 
            password="SecurePass123", 
            is_email_verified=False
        )
        self.client.force_authenticate(user=unverified_user)
        response = self.client.get(self.jobs_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)