from django.urls import path
from .views import (
    RegisterView,
    VerifyOTPView,
    RefreshOTPView,
    LoginView,
)

app_name = "auth"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/", VerifyOTPView.as_view(), name="verify"),
    path("refresh-otp/", RefreshOTPView.as_view(), name="refresh-otp"),
    path("login/", LoginView.as_view(), name="login"),
]
