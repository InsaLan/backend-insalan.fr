"""User module API Endpoints"""

from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib.auth.models import Group, Permission
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from rest_framework import generics, permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from insalan.user.serializers import (
    GroupSerializer,
    PermissionSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

from .models import EmailConfirmationTokenGenerator, User


@require_GET
@ensure_csrf_cookie
def get_csrf(request):
    return JsonResponse({"csrf": "Cookie has been set"})


class UserView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [SessionAuthentication]
    serializer_class = UserSerializer


class UserMe(APIView):
    """
    API endpoint that allows a logged in user to get and set some of their own
    account fields.
    """

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


class GroupViewSet(generics.ListCreateAPIView):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class EmailConfirmView(APIView):
    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def get(self, request, user=None, token=None):
        # For some reason, request.query_params gives an empty dict
        # user = request.query_params.get("user", None)
        # token = request.query_params.get("token", None)

        error_text = _("Invalid confirmation user or token (or already confirmed)")

        if user and token:
            try:
                user_object: User = User.objects.get(username=user)
            except User.DoesNotExist:
                return Response({"msg": error_text}, status=status.HTTP_400_BAD_REQUEST)

            if EmailConfirmationTokenGenerator().check_token(
                user_object,
                token,
            ):
                user_object.email_active = True
                user_object.last_login = datetime.now()
                user_object.save()
                return Response()

        return Response({"msg": error_text}, status=status.HTTP_400_BAD_REQUEST)


class UserRegister(generics.CreateAPIView):
    """
    API endpoint that allows user creation.
    """

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer


class UserLogin(APIView):
    """
    API endpoint that allows user login.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        data = request.data
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            user = serializer.check_validity(data)
            if user is None:
                return Response({"user":[_("Wrong username or password")]}, status=status.HTTP_404_NOT_FOUND)
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        return Response(
            {"msg": "Invalid data submitted"}, status=status.HTTP_400_BAD_REQUEST
        )


class UserLogout(APIView):
    """
    API endpoint that allows a user to logout.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
