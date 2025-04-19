from django.db import models
from django.conf import settings
from django.utils import timezone

class Job(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='jobs')
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    def __str__(self):
        return f"{self.name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_time']),
        ]
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
    
    @property
    def is_active(self):
        return self.status in ['pending', 'in-progress']
    

class JobResult(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='result')
    output = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for {self.job.name}"
    
    class Meta:
        ordering = ['-completed_at']
        verbose_name = "Job Result"
        verbose_name_plural = "Job Results"