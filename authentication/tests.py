from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from authentication.models import OTP, CustomUser


class AuthFlowTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.verify_url = reverse('authentication:verify-otp')
        self.refresh_url = reverse('authentication:refresh-otp')
        self.login_url = reverse('authentication:login')
        
        self.valid_user_data = {
            "email": "user@example.com",
            "password": "SecurePass123"
        }
        
    def tearDown(self):
        CustomUser.objects.all().delete()
        OTP.objects.all().delete()
    
    def test_full_registration_to_login(self):
        response = self.client.post(self.register_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)

        user = CustomUser.objects.get(email=self.valid_user_data["email"])
        self.assertFalse(user.is_email_verified)
        otp = OTP.objects.get(user=user)
     
        verify_data = {
            "email": user.email,
            "otp_code": otp.otp_code
        }
        response = self.client.post(self.verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

        response = self.client.post(self.login_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
    
    def test_invalid_registration(self):
        response = self.client.post(self.register_url, {"email": "user@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.register_url, {"email": "invalid", "password": "pass123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.register_url, {"email": "user@example.com", "password": "123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refresh_otp(self):
        self.client.post(self.register_url, self.valid_user_data)
        user = CustomUser.objects.get(email=self.valid_user_data["email"])
        original_otp = OTP.objects.get(user=user)

        response = self.client.post(self.refresh_url, {"email": user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        original_otp.refresh_from_db()
        self.assertTrue(original_otp.is_used)

        new_otp = OTP.objects.filter(user=user, is_used=False).first()
        self.assertIsNotNone(new_otp)
        self.assertNotEqual(original_otp.otp_code, new_otp.otp_code)
    
    def test_login_without_verification(self):

        self.client.post(self.register_url, self.valid_user_data)

        response = self.client.post(self.login_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)