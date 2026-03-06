# from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserAuthFlowTests(APITestCase):
    def test_register_without_password2_succeeds(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'N3wuserpassword!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_login_with_username_succeeds(self):
        password = 'S3curePassword!'
        User.objects.create_user(
            username='flowuser',
            email='flowuser@example.com',
            password=password,
        )

        response = self.client.post(
            reverse('token_obtain_pair'),
            {
                'username': 'flowuser',
                'password': password,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'flowuser')