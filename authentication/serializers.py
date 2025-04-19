from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, OTP
import random


class UserRegistrationSerializer(serializers.ModelSerializer):
    
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ('email', 'password')

    def _generate_otp_code(self):
        otp_code = f"{random.randint(100000, 999999)}"
        while OTP.objects.filter(otp_code=otp_code).exists():
            otp_code = f"{random.randint(100000, 999999)}"
        return otp_code
    
    def _send_otp_email(self, email, otp_code, subject="Verify your account"):
        send_mail(
            subject=subject,
            message=f"Your OTP code is: {otp_code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        user = CustomUser.objects.create_user(
            username=email, email=email, password=password, is_email_verified=False
        )

        otp_code = self._generate_otp_code()
        otp = OTP.objects.create(user=user, otp_code=otp_code)
        self._send_otp_email(email, otp_code)

        return user

    def to_representation(self, instance):
        return {"email": instance.email, "message": "OTP sent to email for verification"}


class VerifyOTPSerializer(serializers.Serializer):
 
    email = serializers.EmailField()
    otp_code = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        otp_instance = OTP.objects.filter(user=user, otp_code=otp_code, is_used=False).order_by('-created_at').first()

        if not otp_instance:
            raise serializers.ValidationError({"otp_code": "No active OTP found with this code."})

        if otp_instance.is_expired():
            raise serializers.ValidationError({"otp_code": "OTP code is expired."})

        attrs['user'] = user
        attrs['otp_instance'] = otp_instance
        return attrs

    def save(self, **kwargs):
        otp_instance = self.validated_data['otp_instance']
        user = self.validated_data['user']

        otp_instance.is_used = True
        otp_instance.save()

        user.is_email_verified = True
        user.save()

        return user
    
    
class RefreshOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist."}
            )
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        
        OTP.objects.filter(user=user, is_used=False).update(is_used=True)

        registration_serializer = UserRegistrationSerializer()
        otp_code = registration_serializer._generate_otp_code()
        new_otp = OTP.objects.create(user=user, otp_code=otp_code)
        
        registration_serializer._send_otp_email(
            user.email, 
            otp_code, 
            subject="Your New OTP Code"
        )

        return new_otp
