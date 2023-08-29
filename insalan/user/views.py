from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import permissions, status, generics
from rest_framework.authentication import SessionAuthentication
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError
from django.views.decorators.http import require_GET
from .models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from insalan.user.serializers import (
    GroupSerializer,
    PermissionSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

@require_GET
@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({'csrf':'Cookie has been set'})

class UserView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [SessionAuthentication]
    serializer_class = UserSerializer


class UserMe(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = UserSerializer(request.user)
        return Response(user.data)


# TODO: change permission
class PermissionViewSet(generics.ListCreateAPIView):

    queryset = Permission.objects.all().order_by("name")
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]


# TODO: change permission
class GroupViewSet(generics.ListCreateAPIView):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]

class UserRegister(generics.CreateAPIView):
    """
    API endpoint that allows user creation.
    """

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

class UserLogin(APIView):
    """
    API endpoint that allows user login
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        data = request.data
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            user = serializer.check_validity(data)
            if user is None:
                return Response(
                    {"msg": _("Wrong username or password")},
                    status=status.HTTP_404_NOT_FOUND,
                )
            login(request, user)
            return Response(status=status.HTTP_200_OK)


class UserLogout(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
