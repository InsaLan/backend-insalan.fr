"""User module API Endpoints"""

import sys

from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, BadRequest
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
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

from .models import EmailConfirmationTokenGenerator, User, UserMailer, UserManager


@require_GET
@ensure_csrf_cookie
def get_csrf(request):
    """
    Returns a response setting CSRF cookie in headers
    """
    return JsonResponse({"csrf": _("Le cookie a été défini")})


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
        """
        Returns an user's own informations
        """
        user = UserSerializer(request.user, context={"request": request})
        return Response(user.data)

    def patch(self, request):
        """
        Edit the current user following some limitations
        """
        user: User = request.user
        data = request.data
        resp = Response()

        if user is None:
            raise PermissionDenied()
        if "new_password" in data and "password_validation" in data:
            # We need the old password to change...
            if "current_password" not in data:
                raise BadRequest()
            # ...and we need it to be correct
            if not user.check_password(data["current_password"]):
                raise PermissionDenied()

            # We need password and its confirmation
            if data["new_password"] != data["password_validation"]:
                raise BadRequest()

            # We need a strong-enough password
            validation_errors = validate_password(data["new_password"], user=user)
            if validation_errors is not None:
                raise BadRequest(validation_errors)

            # Everything good, we set the new password
            user.set_password(data["new_password"])

            # And we log-out
            logout(request)
            resp.data = {
                "logout": [
                    _(
                        "Votre mot de passe a bien été changé. Merci de vous re-connecter"
                    )
                ]
            }

        if "email" in data:
            user.email = UserManager.normalize_email(data["email"])
            UserMailer.send_email_confirmation(user)

        if "first_name" in data:
            user.first_name = data["first_name"]

        if "last_name" in data:
            user.last_name = data["last_name"]

        user.save()
        return resp


# TODO: change permission
class PermissionViewSet(generics.ListCreateAPIView):
    """
    Django's `Permission` ViewSet to be able to add them to the admin panel
    """

    queryset = Permission.objects.all().order_by("name")
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupViewSet(generics.ListCreateAPIView):
    """
    Django's `Group` ViewSet to be able to add them to the admin panel
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class EmailConfirmView(APIView):
    """
    Email confirmation user API Endpoint
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def get(self, request, user=None, token=None):
        """
        If requested with valid parameters, will validate an user's email
        """
        error_text = _("Utilisateur·rice ou jeton invalide (ou adresse déjà confirmée)")

        if user and token:
            try:
                user_object: User = User.objects.get(username=user)
            except User.DoesNotExist:
                return Response(
                    {"user": [error_text]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if EmailConfirmationTokenGenerator().check_token(
                user_object,
                token,
            ):
                user_object.user_permissions.add(
                    Permission.objects.get(codename="email_active")
                )
                user_object.last_login = timezone.make_aware(datetime.now())
                user_object.save()
                return Response()

        return Response({"user": [error_text]}, status=status.HTTP_400_BAD_REQUEST)


class AskForPasswordReset(APIView):
    """
    Asking for a password reset API Endpoint
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        """
        If requested with valid parameters, will send a password reset email to
        an user given their email address
        """
        try:
            user_object: User = User.objects.get(email=request.data["email"])
            UserMailer.send_password_reset(user_object)
        except User.DoesNotExist:
            pass

        return Response()


class ResetPassword(APIView):
    """
    Password Reset API Endpoint
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        """
        If requested with valid parameters, will reset an user password
        """
        data = request.data
        if not (
            "user" in data
            and "token" in data
            and "password" in data
            and "password_confirm" in data
        ):
            return Response(
                {"user": [_("Champ manquant")]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user_object: User = User.object.get(username=data["user"])
            if default_token_generator.check_token(user_object, data["token"]):
                if data["password"] == data["password_confirm"]:
                    validation_errors = validate_password(
                        data["password"], user=user_object
                    )
                    if validation_errors is None:
                        user_object.set_password(data["password"])
                        user_object.save()
                        return Response()
                    return Response(
                        {
                            "user": [_("Mot de passe trop simple ou invalide")],
                            "errors": validation_errors,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {"user": [_("Les mots de passe diffèrent")]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"user": [_("Jeton de ré-initialisation invalide")]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except User.DoesNotExist:
            return Response(
                {"user": [_("Utilisateur⋅rice non trouvé⋅e")]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ResendEmailConfirmView(APIView):
    """
    API endpoint to re-send a confirmation email
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        """
        If the user is found, will send again a confirmation email
        """
        error_text = _("Impossible de renvoyer le courriel de confirmation")

        username = request.data.get("username")

        if not username:
            return Response(
                {"user": [error_text]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_object: User = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"user": [error_text]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_object.has_perm("email_active"):
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
        """
        Submit a login form
        """
        data = request.data
        serializer = UserLoginSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            user = serializer.check_validity(data)
            if user is None:
                return Response(
                    {"user": [_("Nom d'utilisateur·rice ou mot de passe incorrect")]},
                    status=status.HTTP_404_NOT_FOUND,
                )
            login(request, user)
            return Response(status=status.HTTP_200_OK)
        return Response(
            {"user": [_("Format des données soumises invalide")]},
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserLogout(APIView):
    """
    API endpoint that allows a user to logout.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Will logout an user.
        """
        logout(request)
        return Response(status=status.HTTP_200_OK)
