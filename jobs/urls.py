from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JobViewSet, JobResultView, JobSummaryView

app_name = 'jobs'

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')

urlpatterns = [
    path('jobs/summary/', JobSummaryView.as_view(), name='job-summary'),

    path('jobs/<int:pk>/result/', JobResultView.as_view(), name='job-result'),

    path('', include((router.urls, app_name), namespace=app_name)),
]
