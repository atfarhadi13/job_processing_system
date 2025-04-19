from django.urls import path
from .views import UserRegistrationView, VerifyOTPView, RefreshOTPView, UserLoginView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('refresh-otp/', RefreshOTPView.as_view(), name='refresh-otp'),
    path('login/', UserLoginView.as_view(), name='login'),
]
