from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.settings import EMAIL_AUTH
from insalan.mailer import MailManager
import insalan.tournament.serializers as serializers

from ..models import Player, Manager, Substitute, Team, PaymentStatus
from .permissions import ReadOnly, Patch


class TeamList(generics.ListCreateAPIView):
    """List all known teams"""

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAuthenticated | ReadOnly]

    @swagger_auto_schema(
        responses={
            201: serializer_class,
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
                        description=_("Vous n'êtes pas autorisé à créer une équipe")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user

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

        return super().post(request, *args, **kwargs)


class TeamDetails(generics.RetrieveAPIView, generics.DestroyAPIView):
    """Details about a team"""

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAdminUser | Patch | permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        request_body=serializers.TeamSerializer,
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
                        description=_("Vous n'êtes pas autorisé à modifier cette équipe")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Équipe introuvable")
                    )
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Patch a team
        """
        user = request.user
        data = request.data

        # get the team
        try:
            team = Team.objects.get(id=kwargs["pk"])
        except Team.DoesNotExist:
            raise NotFound()

        # check if the user is registered in the team
        player = Player.objects.filter(user=user, team=team)
        manager = Manager.objects.filter(user=user, team=team)
        if len(player) == 0 and len(manager) == 0:
            return Response({
                "team": _("Vous n'êtes pas inscrit dans cette équipe.")
            }, status=status.HTTP_403_FORBIDDEN)

        # check if the player is the team's captain or a manager
        if len(manager) == 0 and team.captain.id != player[0].id:
            return Response({
                "team": _("Vous n'avez pas la permission de modifier cette équipe.")
            }, status=status.HTTP_403_FORBIDDEN)

        # team name edit
        if "name" in data and len(data["name"]) >= 3:
            team.name = data["name"]

        # team password edit
        if "password" in data:
            if len(data["password"]) >= 8:
                team.password = make_password(data["password"])
            else:
                return Response({
                    "password": _("Mot de passe invalide.")
                }, status=status.HTTP_400_BAD_REQUEST)

        # player edit
        if "players" in data:
            existing = set(team.get_players_id())
            players = set(data["players"])
            removed = existing - players
            for uid in removed:
                player = Player.objects.get(id=uid)
                # if player hasn't paid, remove him from the team
                if player.as_user().id != user.id and player.payment_status == PaymentStatus.NOT_PAID:
                    MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"]).send_kick_mail(player.as_user(), team.name)
                    player.delete()

        # manager edit
        if "managers" in data:
            existing = set(team.get_managers_id())
            managers = set(data["managers"])
            removed = existing - managers
            for uid in removed:
                manager = Manager.objects.get(id=uid)
                # if manager hasn't paid, remove him from the team
                if manager.as_user().id != user.id and manager.payment_status == PaymentStatus.NOT_PAID:
                    MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"]).send_kick_mail(manager.as_user(), team.name)
                    manager.delete()

        # substitute edit
        if "substitutes" in data:
            existing = set(team.get_substitutes_id())
            substitutes = set(data["substitutes"])
            removed = existing - substitutes
            for uid in removed:
                substitute = Substitute.objects.get(id=uid)
                # if substitute hasn't paid, remove him from the team
                if substitute.as_user().id != user.id and substitute.payment_status == PaymentStatus.NOT_PAID:
                    MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"]).send_kick_mail(substitute.as_user(), team.name)
                    substitute.delete()

        team.save()

        serializer = serializers.TeamSerializer(team, context={"request": request}).data

        players = []
        for player in serializer["players"]:
            players.append(Player.objects.get(id=player))
        serializer["players"] = serializers.FullDerefPlayerSerializer(players, many=True, context={"request": request}).data

        managers = []
        for manager in serializer["managers"]:
            managers.append(Manager.objects.get(id=manager))
        serializer["managers"] = serializers.FullDerefManagerSerializer(managers, many=True, context={"request": request}).data

        substitutes = []
        for substitute in serializer["substitutes"]:
            substitutes.append(Substitute.objects.get(id=substitute))
        serializer["substitutes"] = serializers.FullDerefSubstituteSerializer(substitutes, many=True, context={"request": request}).data

        return Response(serializer, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            204: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Équipe supprimée")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à supprimer cette équipe")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Équipe introuvable")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a team
        """
        return super().delete(request, *args, **kwargs)

class TeamMatchs(generics.RetrieveAPIView):
    """
    Get all matchs of a team
    """

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamMatchsSerializer
    permission_classes = [permissions.IsAdminUser | permissions.IsAuthenticated]
    pagination_class = None