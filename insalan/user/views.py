"""User module API Endpoints"""

from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
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

from .models import EmailConfirmationTokenGenerator, User, UserMailer


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
        error_text = _("Utilisateur ou jeton invalide (ou adresse déjà confirmée)")

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


class AskForPasswordReset(APIView):
    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        try:
            user_object: User = User.objects.get(email=request.data["email"])
            UserMailer.send_password_reset(user_object)
        except User.DoesNotExist:
            pass

        return Response()


class ResetPassword(APIView):
    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        data = request.data
        if not (
            "user" in data
            and "token" in data
            and "password" in data
            and "password_confirm" in data
        ):
            return Response(
                {"msg": _("Champ manquant dans la ré-initialisation de mot de passe")},
                status=HTTP_400_BAD_REQUEST,
            )
        try:
            user_object: User = User.objects.get(user=data["user"])
            if (
                default_token_generator.check_token(user_object, data["token"])
                and password == password_confirm
                and validate_password(password)
            ):
                user_object.set_password(password)
        except User.DoesNotExist:
            return Response(
                {"msg": _("Utilisateur non trouvé")}, status=HTTP_400_BAD_REQUEST
            )

        return Response()


class ResendEmailConfirmView(APIView):
    """
    API endpoint to re-send
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        error_text = _("Impossible de renvoyer le courriel de confirmation")

        username = request.data.get("username")

        if not username:
            return Response({"msg": error_text}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_object: User = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"msg": error_text}, status=status.HTTP_400_BAD_REQUEST)

        if user_object.email_active:
            return Response({"msg": error_text}, status=status.HTTP_400_BAD_REQUEST)

        UserMailer.send_email_confirmation(user_object)
        return Response()


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
