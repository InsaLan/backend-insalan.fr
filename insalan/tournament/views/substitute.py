from django.core.exceptions import PermissionDenied, BadRequest
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.http import QueryDict

from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.tournament.models.validators import valid_name
from insalan.user.models import User
from insalan.tournament import serializers

from ..models import Substitute, Team, PaymentStatus

class SubstituteRegistration(generics.RetrieveAPIView):
    """Show a substitute registration"""

    serializer_class = serializers.SubstituteSerializer
    queryset = Substitute.objects.all().order_by("id")

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
    def get(self, request, *args, **kwargs):
        """
        Get a substitute
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
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
    def patch(self, request, *args, **kwargs):
        """
        Patch a substitute
        """
        user = request.user
        data = request.data

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the substitute
        try:
            substitute = Substitute.objects.get(id=kwargs["pk"])
        except Substitute.DoesNotExist as exc:
            raise NotFound() from exc

        # check if the user is related to the substitute
        if substitute.as_user().id != user.id:
            return Response({
                "substitute": _("Vous n'avez pas la permission de modifier cette inscription.")
            }, status=status.HTTP_403_FORBIDDEN)

        if "name_in_game" in data:
            if(valid_name(substitute.team.tournament.game, data["name_in_game"])):
                substitute.name_in_game = data["name_in_game"]
            else:
                return Response(
                    {"name_in_game": _("Pseudo invalide")},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            substitute.save()
        except Exception as exc:
            return Response(
                {"player": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = serializers.SubstituteSerializer(substitute, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: serializer_class,
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'avez pas la permission de supprimer cette inscription")
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
        Delete a substitute
        """
        user = request.user

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the substitute
        try:
            substitute = Substitute.objects.get(id=kwargs["pk"])
        except Substitute.DoesNotExist as exc:
            raise NotFound() from exc

        # check if the user is related to the substitute
        if substitute.as_user().id != user.id:
            return Response({
                "substitute": _("Vous n'avez pas la permission de supprimer cette inscription.")
            }, status=status.HTTP_403_FORBIDDEN)

        # if substitute has paid, can't delete
        if substitute.payment_status != PaymentStatus.NOT_PAID:
            return Response({
                "substitute": _("Vous ne pouvez pas supprimer votre inscription si vous avez payé.")
            }, status=status.HTTP_403_FORBIDDEN)

        substitute.delete()

        # if the team is empty, delete it
        if len(substitute.team.get_players_id()) == 0 \
            and len(substitute.team.get_managers_id()) == 0 \
            and len(substitute.team.get_substitutes_id()) == 0:
            substitute.team.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class SubstituteRegistrationList(generics.ListCreateAPIView):
    """Show all substitute registrations"""

    pagination_class = None
    serializer_class = serializers.SubstituteSerializer
    queryset = Substitute.objects.all().order_by("id")

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "team": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("ID de l'équipe")
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Mot de passe de l'équipe")
                ),
                "name_in_game": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Pseudo en jeu")
                ),
            },
        ),
        responses={
            200: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "team": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("ID de l'équipe")
                    ),
                    "password": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Mot de passe de l'équipe")
                    ),
                    "name_in_game": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Pseudo en jeu")
                    ),
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à vous inscrire à un tournoi")
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
            or "name_in_game" not in data
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

class SubstituteRegistrationListId(generics.ListAPIView):
    """Find all substitute registrations of a user from their ID"""

    pagination_class = None
    serializer_class = serializers.SubstituteIdSerializer

    def get_queryset(self):
        """Obtain the queryset fot this view"""
        return Substitute.objects.filter(user_id=self.kwargs["user_id"])

class SubstituteRegistrationListName(generics.ListAPIView):
    """Find all substitute registrations of a user from their username"""

    pagination_class = None
    serializer_class = serializers.SubstituteIdSerializer

    def get_queryset(self):
        """Obtain the queryset fot this view"""
        user = None
        try:
            user = User.objects.get(username=self.kwargs["username"])
        except User.DoesNotExist as exc:
            raise NotFound() from exc
        return Substitute.objects.filter(user=user)
