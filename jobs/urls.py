from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import JobViewSet, JobResultView, JobSummaryView

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")

urlpatterns = [
    path("", include(router.urls)),

    path("jobs/<int:pk>/result/", JobResultView.as_view(), name="job-result"),
    
    path("jobs/summary/", JobSummaryView.as_view(), name="job-summary"),
]

app_name = 'jobs'
