from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Check both email and username as identifiers
            login_identifier = request.data.get('email') or request.data.get('username')
            if login_identifier:
                try:
                    # Retrieve user by email to include profile data in response
                    user = User.objects.get(email=login_identifier)
                    response.data['user'] = UserSerializer(user).data
                except ObjectDoesNotExist:
                    # If user is not found by email, try fetching by username
                    try:
                        user = User.objects.get(username=login_identifier)
                        response.data['user'] = UserSerializer(user).data
                    except ObjectDoesNotExist:
                        pass
        return response


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user