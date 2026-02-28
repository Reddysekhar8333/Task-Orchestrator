from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Task

User = get_user_model()


class TaskOrchestratorTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'test_devops_user',
            'password': 'securepassword123',
            'email': 'test@example.com',
        }
        self.user = User.objects.create_user(**self.user_data)

        # Get JWT Token for authenticated requests
        login_url = reverse('token_obtain_pair')
        response = self.client.post(
            login_url,
            {
                'email': self.user_data['email'],
                'password': self.user_data['password'],
            },
            format='json',
        )
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_create_task_authenticated(self):
        url = reverse('task-list')
        data = {'title': 'CI/CD Test Task', 'description': 'Testing Jenkins Pipeline'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.get().title, 'CI/CD Test Task')

    def test_query_optimization_logic(self):
        Task.objects.create(user=self.user, title='Existing Task')
        url = reverse('task-list')
        response = self.client.get(url)

        # Check if the list returns only the user's tasks
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_access(self):
        self.client.credentials()  # Clear tokens
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)