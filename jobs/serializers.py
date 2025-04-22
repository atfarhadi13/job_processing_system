from rest_framework import serializers
from django.utils import timezone

from .models import Job, JobResult


class JobResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobResult
        fields = ("output", "error_message", "completed_at")
        read_only_fields = fields


class JobSerializer(serializers.ModelSerializer):
    result = JobResultSerializer(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Job
        fields = (
            "id",
            "name",
            "description",
            "scheduled_time",
            "created_at",
            "status",
            "result",
            "user",
        )
        read_only_fields = ("id", "created_at", "status")

    def validate_scheduled_time(self, value):
        now = timezone.now()
        if value <= now:
            raise serializers.ValidationError(
                f"Scheduled time ({value}) must be in the future. Current time is {now}."
            )
        return value