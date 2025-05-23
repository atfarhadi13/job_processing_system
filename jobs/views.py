from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Job, JobResult
from .serializers import JobSerializer, JobResultSerializer
from .tasks import start_job, complete_job, cancel_job


class IsEmailVerified(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_email_verified
        )


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsEmailVerified]

    def perform_create(self, serializer):
        job = serializer.save()
        start_job.delay(job.id)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        print(f"Completing job {pk}")
        complete_job.delay(pk)
        return Response(
            {"detail": "Completion requested."},
            status=status.HTTP_202_ACCEPTED
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        cancel_job.delay(pk)
        return Response(
            {"detail": "Cancellation requested."},
            status=status.HTTP_202_ACCEPTED
        )


class JobResultView(generics.RetrieveAPIView):
    serializer_class = JobResultSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def get_object(self):

        job_id = self.kwargs["pk"]
        job = get_object_or_404(Job, pk=job_id, user=self.request.user)
        
        if job.status != "completed":
            raise exceptions.ValidationError(
                "Result not available until job is completed."
            )
        
        if not hasattr(job, 'result') or not job.result:
            raise exceptions.NotFound(
                "Result data not found for this job."
            )
            
        return job.result


class JobSummaryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def get(self, request, *args, **kwargs):
        qs = (
            Job.objects.filter(user=request.user)
            .values("status")
            .annotate(count=Count("id"))
        )

        result = {status: 0 for status in ["pending", "in-progress", "completed", "failed"]}
        result.update({item["status"]: item["count"] for item in qs})
        
        return Response(result)
