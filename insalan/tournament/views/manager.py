from django.core.exceptions import PermissionDenied, BadRequest
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.http import QueryDict

from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.user.models import User
import insalan.tournament.serializers as serializers

from ..models import Manager, Team, PaymentStatus

class ManagerRegistration(generics.RetrieveAPIView):
    """Show a manager registration"""

    serializer_class = serializers.ManagerSerializer
    queryset = Manager.objects.all().order_by("id")

    @swagger_auto_schema(
        responses={
            200: serializer_class,
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'avez pas la permission de voir cette inscription")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Inscription introuvable")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a manager
        """
        user = request.user

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the manager
        try:
            manager = Manager.objects.get(id=kwargs["pk"])
        except Manager.DoesNotExist as exc:
            raise NotFound() from exc

        # check if the user is related to the manager
        if manager.as_user().id != user.id:
            return Response({
                "manager": _("Vous n'avez pas la permission de supprimer cette inscription.")
            }, status=status.HTTP_403_FORBIDDEN)

        # if manager has paid, can't delete
        if manager.payment_status != PaymentStatus.NOT_PAID:
            return Response({
                "manager": _("Vous ne pouvez pas supprimer votre inscription si vous avez payé.")
            }, status=status.HTTP_403_FORBIDDEN)

        manager.delete()

        # if the team is empty, delete it
        if len(manager.team.get_players_id()) == 0 \
            and len(manager.team.get_managers_id()) == 0 \
            and len(manager.team.get_substitutes_id()) == 0:
            manager.team.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        responses={
            200: serializer_class,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Inscription introuvable")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get a manager
        """
        return super().get(request, *args, **kwargs)

class ManagerRegistrationList(generics.ListCreateAPIView):
    """Show all manager registrations"""

    pagination_class = None
    serializer_class = serializers.ManagerSerializer
    queryset = Manager.objects.all().order_by("id")

    @swagger_auto_schema(
        request_body=serializers.ManagerSerializer,
        responses={
            201: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "team": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Équipe introuvable")
                    ),
                    "password": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Mot de passe invalide")
                    ),
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à vous inscrire à ce tournoi")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        if user is None or not user.is_authenticated :
            raise PermissionDenied()

        if (
            "team" not in data
            or "payment_status" in data
            or "ticket" in data
            or "password" not in data
        ) :
            raise BadRequest()

        if not user.is_email_active():
            raise PermissionDenied(
                {
                    "email": [
                        _(
                            "Veuillez activer votre courriel pour vous inscrire à un tournoi"
                        )
                    ]
                }
            )

        if not check_password(data["password"], Team.objects.get(pk=data["team"]).get_password()):
            return Response(
                { "password": _("Mot de passe invalide.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # make the data dict mutable in the case of immutable QueryDict form django test client
        if isinstance(data, QueryDict):
            data._mutable = True
        data["user"] = user.id

        return super().post(request, *args, **kwargs)


class ManagerRegistrationListId(generics.ListAPIView):
    """Find all player registrations of a user from their ID"""

    pagination_class = None
    serializer_class = serializers.ManagerIdSerializer

    def get_queryset(self):
        """Obtain the queryset fot this view"""
        return Manager.objects.filter(user_id=self.kwargs["user_id"])
    
    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("ID de l'inscription")
                        ),
                        "team": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("ID de l'équipe")
                        ),
                        "payment_status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Statut de paiement")
                        ),
                        "ticket": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Ticket")
                        )
                    }
                )
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get all manager registrations of a user from their ID
        """
        return super().get(request, *args, **kwargs)


class ManagerRegistrationListName(generics.ListAPIView):
    """Find all player registrations of a user from their username"""

    pagination_class = None
    serializer_class = serializers.ManagerIdSerializer

    def get_queryset(self):
        """Obtain the queryset fot this view"""
        user = None
        try:
            user = User.objects.get(username=self.kwargs["username"])
        except User.DoesNotExist as exc:
            raise NotFound() from exc
        return Manager.objects.filter(user=user)
    
    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("ID de l'inscription")
                        ),
                        "team": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("ID de l'équipe")
                        ),
                        "payment_status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Statut de paiement")
                        ),
                        "ticket": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Ticket")
                        )
                    }
                )
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get all manager registrations of a user from their username
        """
        return super().get(request, *args, **kwargs)