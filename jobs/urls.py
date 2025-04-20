from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import JobViewSet, JobResultView, JobSummaryView

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

urlpatterns = [
    path("jobs/summary/", JobSummaryView.as_view(), name="job-summary"),
    path("jobs/<int:pk>/result/", JobResultView.as_view(), name="job-result"),
    path("", include(router.urls)),
]

app_name = 'jobs'
