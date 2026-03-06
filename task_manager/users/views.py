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
        if request.data.get('username') and not request.data.get('email'):
            mutable_data = request.data.copy()
            try:
                mutable_data['email'] = User.objects.only('email').get(username=mutable_data['username']).email
                request._full_data = mutable_data
            except ObjectDoesNotExist:
                pass
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Check both email and username as identifiers
            login_identifier = request.data.get('email') or request.data.get('username')
            if login_identifier:
                try:
                    # Retrieve user by email to include profile data in response
                    user = User.objects.get(email=login_identifier)
                except ObjectDoesNotExist:
                    # If user is not found by email, try fetching by username
                    try:
                        user = User.objects.get(username=login_identifier)
                        response.data['user'] = UserSerializer(user).data
                    except ObjectDoesNotExist:
                        user = None
                if user is not None:
                    response.data['user'] = UserSerializer(user).data
        return response


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user