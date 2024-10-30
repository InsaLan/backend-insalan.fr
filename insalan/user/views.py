"""User module API Endpoints"""

from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.core.exceptions import ValidationError
from rest_framework import generics, permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.user.serializers import (
    GroupSerializer,
    PermissionSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

from insalan.settings import EMAIL_AUTH
from insalan.mailer import EmailConfirmationTokenGenerator, MailManager
from .models import User, UserManager

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


class UserMe(generics.RetrieveAPIView):
    """
    API endpoint that allows a logged in user to get and set some of their own
    account fields.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        """
        Returns an user's own informations
        """
        user = UserSerializer(request.user, context={"request": request}).data

        user_groups = []
        for group in request.user.groups.all():
            user_groups.append(group.name)

        user["groups"] = user_groups

        return Response(user)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Adresse de courriel")
                ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Prénom")
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nom de famille")
                ),
                "display_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nom d'affichage")
                ),
                "pronouns": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Pronoms")
                ),
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Statut")
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nouveau mot de passe")
                ),
                "password_validation": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Validation du mot de passe")
                ),
                "current_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Mot de passe actuel")
                ),
            },
        ),
        responses={
            200: UserSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "password": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Mot de passe invalide")
                        )
                    ),
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Données invalides")
                        )
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "password": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Mot de passe actuel invalide")
                        )
                    )
                }
            )
        }
    )
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
                return Response(
                    {"password": [_("Le mot de passe actuel doit être renseigné")]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # ...and we need it to be correct
            if not user.check_password(data["current_password"]):
                raise PermissionDenied()

            # We need password and its confirmation
            if data["new_password"] != data["password_validation"]:
                return Response(
                    {"password": [_("Les mots de passe diffèrent")]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # We need a strong-enough password
            try:
                validate_password(data["new_password"], user=user)
            except ValidationError as err:
                return Response(
                    {"user": err.messages}, status=status.HTTP_400_BAD_REQUEST
                )

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
            MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_email_confirmation(user)

        if "first_name" in data:
            user.first_name = data["first_name"]

        if "last_name" in data:
            user.last_name = data["last_name"]

        if "display_name" in data:
            user.display_name = data["display_name"]

        if "pronouns" in data:
            user.pronouns = data["pronouns"]

        if "status" in data:
            user.status = data["status"]

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

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "msg": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Adresse de courriel confirmée")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Utilisateur·rice ou jeton invalide (ou adresse déjà confirmée)")
                        )
                    )
                }
            )
        }
    )
    def get(self, request, pk=None, token=None):
        """
        If requested with valid parameters, will validate an user's email
        """
        error_text = _("Utilisateur·rice ou jeton invalide (ou adresse déjà confirmée)")

        if pk and token:
            try:
                user_object: User = User.objects.get(pk=pk)
            except User.DoesNotExist:
                return Response(
                    {"user": [error_text]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if EmailConfirmationTokenGenerator().check_token(
                user_object,
                token,
            ):
                user_object.set_email_active()
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Adresse de courriel")
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "msg": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Courriel de ré-initialisation envoyé")
                    )
                }
            ),
        }
    )
    def post(self, request):
        """
        If requested with valid parameters, will send a password reset email to
        an user given their email address
        """
        try:
            user_object: User = User.objects.get(email=request.data["email"])
            MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_password_reset(user_object)
        except User.DoesNotExist:
            pass

        return Response()


class ResetPassword(APIView):
    """
    Password Reset API Endpoint
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nom d'utilisateur")
                ),
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Jeton de ré-initialisation")
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nouveau mot de passe")
                ),
                "password_confirm": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Confirmation du nouveau mot de passe")
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "msg": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Mot de passe ré-initialisé")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Champ manquant/mot de passe invalide")
                        )
                    )
                }
            )
        }
    )
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
                    try:
                        validate_password(
                            data["password"], user=user_object
                        )
                    except ValidationError as err:
                        validation_errors = err.messages
                        return Response(
                            {
                                "user": [_("Mot de passe trop simple ou invalide")],
                                "errors": validation_errors,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    user_object.set_password(data["password"])
                    user_object.save()
                    return Response()
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

class ResendEmailConfirmView(APIView):
    """
    API endpoint to re-send a confirmation email
    """

    permissions_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nom d'utilisateur")
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "msg": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Courriel de confirmation renvoyé")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Impossible de renvoyer le courriel de confirmation")
                        )
                    )
                }
            )
        }
    )
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

        MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_email_confirmation(user_object)
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Nom d'utilisateur")
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Mot de passe")
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Utilisateur·rice connecté·e")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Format des données soumises invalide")
                        )
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Nom d'utilisateur·rice ou mot de passe incorrect")
                        )
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Veuillez confirmer votre adresse de courriel")
                        )
                    )
                }
            )
        }
    )
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
            if not user.user_permissions.filter(codename="email_active").exists():
                return Response(
                    {"user": [_("Veuillez confirmer votre adresse de courriel")]},
                    status=status.HTTP_403_FORBIDDEN,
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
