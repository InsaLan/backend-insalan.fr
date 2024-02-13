from django.core.exceptions import PermissionDenied, BadRequest
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.http import QueryDict
from django.contrib.auth.hashers import make_password

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from insalan.settings import EMAIL_AUTH
from insalan.mailer import MailManager
from insalan.user.models import User
import insalan.tournament.serializers as serializers

from ..models import Player, Manager, Substitute, Event, Tournament, Game, Team, PaymentStatus
from .permissions import ReadOnly, Patch


class TeamList(generics.ListCreateAPIView):
    """List all known teams"""

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAuthenticated | ReadOnly]

    def post(self, request, *args, **kwargs):
        user = request.user

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

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


class TeamDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a team"""

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly | Patch]

    def patch(self, request, *args, **kwargs):
        """
        Patch a team
        """
        user = request.user
        data = request.data

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the team
        team = Team.objects.get(id=kwargs["pk"])

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

        serializer = serializers.TeamSerializer(team, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

class TeamMatchs(generics.RetrieveAPIView):

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamMatchsSerializer
    permission_classes = [permissions.IsAdminUser | permissions.IsAuthenticated]
    pagination_class = None