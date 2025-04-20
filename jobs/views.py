from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets, exceptions
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from .models import Job, JobResult
from .serializers import JobSerializer, JobResultSerializer
from .tasks import execute_job


class IsEmailVerified(permissions.BasePermission):
    
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_email_verified
        )


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    http_method_names = ["get", "post", "delete"]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["scheduled_time", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Job.objects.filter(user=self.request.user)
            .select_related("result")
            .order_by(*self.ordering)
        )

    def perform_create(self, serializer):
        job = serializer.save()
        eta = job.scheduled_time + timedelta(seconds=1)
        execute_job.apply_async(args=[job.id], eta=eta)

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        if job.status != "pending":
            return Response(
                {"detail": "Only pending jobs can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        job.status = "failed"
        job.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
