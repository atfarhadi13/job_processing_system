from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import (
    RegistrationSerializer,
    VerifyOTPSerializer,
    RefreshOTPSerializer,
)
from .models import CustomUser


# ─────────────  Registration / OTP endpoints  ────────────────
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegistrationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = VerifyOTPSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response({"detail": "OTP verified."}, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RefreshOTPSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response({"detail": "New OTP sent."}, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────  JWT login (email verified only)  ──────────────
class EmailVerifiedTokenSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_email_verified:
            raise permissions.PermissionDenied("Email is not verified.")
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerifiedTokenSerializer
