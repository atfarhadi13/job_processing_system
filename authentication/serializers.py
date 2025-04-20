# authentication/serializers.py
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import serializers

from .models import OTPVerification

User = get_user_model()


# ────────────────  helpers  ──────────────────────────────────
def _send_otp_email(email: str, otp_code: str) -> None:
    subject = "Your verification code"
    message = f"Use the following OTP to verify your e‑mail: {otp_code}"
    send_mail(subject, message, None, [email], fail_silently=False)


def _create_and_email_otp(user: User) -> OTPVerification:
    # mark any previous codes as used
    OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
    otp = OTPVerification.objects.create(user=user)
    _send_otp_email(user.email, otp.otp_code)
    return otp


# ────────────────  serializers  ──────────────────────────────
class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save(update_fields=["password"])
        _create_and_email_otp(user)
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs["email"].lower()
        otp_code = attrs["otp_code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        try:
            otp = OTPVerification.objects.get(
                user=user, otp_code=otp_code, is_used=False
            )
        except OTPVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        if otp.is_expired:
            raise serializers.ValidationError("OTP has expired.")

        attrs["user"] = user
        attrs["otp"] = otp
        return attrs

    def save(self, **kwargs):
        user: User = self.validated_data["user"]
        otp: OTPVerification = self.validated_data["otp"]

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return user


class RefreshOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value.lower())
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if user.is_email_verified:
            raise serializers.ValidationError("E‑mail already verified.")
        return value

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data["email"].lower())

        latest = (
            OTPVerification.objects.filter(user=user).order_by("-created_at").first()
        )
        if latest and timezone.now() - latest.created_at < timedelta(seconds=60):
            raise serializers.ValidationError("Please wait before requesting another OTP.")

        _create_and_email_otp(user)
        return {"detail": "OTP sent"}
