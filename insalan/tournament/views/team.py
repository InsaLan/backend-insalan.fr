from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied, BadRequest
from django.utils.translation import gettext_lazy as _

from drf_yasg.utils import swagger_auto_schema  # type: ignore[import]
from drf_yasg import openapi  # type: ignore[import]

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from insalan.mailer import MailManager
from insalan.settings import EMAIL_AUTH
from insalan.tournament import serializers
from insalan.user.models import User

from ..models import Player, Manager, Substitute, Team, PaymentStatus, SeatSlot
from .permissions import ReadOnly, Patch


class TeamList(generics.ListCreateAPIView[Team]): # pylint: disable=unsubscriptable-object
    """List all known teams"""

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAuthenticated | ReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        assert isinstance(user, User), 'User must be authenticated to access this route.'

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

        if self.queryset.filter(name__exact=request.data["name"],
                                tournament=request.data["tournament"]).exists():
            return Response({
                "name": _("Ce nom d'équipe est déjà pris.")
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().post(request, *args, **kwargs)



# pylint: disable-next=unsubscriptable-object
class TeamDetails(generics.RetrieveAPIView[Team], generics.DestroyAPIView[Team]):
    """Details about a team"""

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAdminUser | Patch | permissions.IsAuthenticatedOrReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Patch a team."""
        user = request.user
        data = request.data

        if not user.is_authenticated:
            raise PermissionDenied()

        # get the team
        try:
            team = Team.objects.get(id=kwargs["pk"])
        except Team.DoesNotExist as exc:
            raise NotFound() from exc

        # check if the user is registered in the team
        player_query = Player.objects.filter(user=user, team=team)
        manager_query = Manager.objects.filter(user=user, team=team)
        if len(player_query) == 0 and len(manager_query) == 0:
            return Response({
                "team": _("Vous n'êtes pas inscrit dans cette équipe.")
            }, status=status.HTTP_403_FORBIDDEN)

        # check if the player is the team's captain or a manager
        if (len(manager_query) == 0 and
            (team.captain is None or team.captain.id != player_query[0].id)):
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
            players_set = set(data["players"])
            removed = existing - players_set
            for uid in removed:
                player = Player.objects.get(id=uid)
                # if player hasn't paid, remove him from the team
                if (player.as_user().id != user.id and
                    player.payment_status == PaymentStatus.NOT_PAID):
                    mailer = MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"])
                    assert mailer is not None
                    mailer.send_kick_mail(
                        player.as_user(),
                        team.name,
                    )
                    player.delete()

        # manager edit
        if "managers" in data:
            existing = set(team.get_managers_id())
            managers_set = set(data["managers"])
            removed = existing - managers_set
            for uid in removed:
                manager = Manager.objects.get(id=uid)
                # if manager hasn't paid, remove him from the team
                if (manager.as_user().id != user.id and
                    manager.payment_status == PaymentStatus.NOT_PAID):
                    mailer = MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"])
                    assert mailer is not None
                    mailer.send_kick_mail(
                        manager.as_user(),
                        team.name,
                    )
                    manager.delete()

        # substitute edit
        if "substitutes" in data:
            existing = set(team.get_substitutes_id())
            substitutes_set = set(data["substitutes"])
            removed = existing - substitutes_set
            for uid in removed:
                substitute = Substitute.objects.get(id=uid)
                # if substitute hasn't paid, remove him from the team
                if (substitute.as_user().id != user.id and
                    substitute.payment_status == PaymentStatus.NOT_PAID):
                    mailer = MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"])
                    assert mailer is not None
                    mailer.send_kick_mail(
                        substitute.as_user(),
                        team.name,
                    )
                    substitute.delete()

        if "seat_slot" in data:
            if not team.validated:
                return Response({
                    "seat_slot": _("Équipe non validée.")
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                seat_slot = SeatSlot.objects.get(id=data["seat_slot"])
            except SeatSlot.DoesNotExist:
                return Response({
                    "seat_slot": _("Slot invalide.")
                }, status=status.HTTP_400_BAD_REQUEST)

            if seat_slot.tournament.id != team.tournament.id:
                return Response({
                    "seat_slot": _("Slot appartient à un autre tournoi.")
                }, status=status.HTTP_400_BAD_REQUEST)

            if hasattr(seat_slot, "team") and seat_slot.team.id != team.id:
                return Response({
                    "seat_slot": _("Slot déjà utilisé.")
                }, status=status.HTTP_400_BAD_REQUEST)

            if seat_slot.seats.count() != team.tournament.game.players_per_team:
                return Response({
                    "seat_slot": _("Slot inadapté au tournoi.")
                }, status=status.HTTP_400_BAD_REQUEST)

            team.seat_slot = seat_slot


        team.save()

        serializer = serializers.TeamSerializer(team, context={"request": request}).data

        players: list[Player] = []
        for player_id in serializer["players"]:
            players.append(Player.objects.get(id=player_id))
        serializer["players"] = serializers.FullDerefPlayerSerializer(
            players,
            many=True,
            context={"request": request},
        ).data

        managers = []
        for manager_id in serializer["managers"]:
            managers.append(Manager.objects.get(id=manager_id))
        serializer["managers"] = serializers.FullDerefManagerSerializer(
            managers,
            many=True,
            context={"request": request},
        ).data

        substitutes = []
        for substitute_id in serializer["substitutes"]:
            substitutes.append(Substitute.objects.get(id=substitute_id))
        serializer["substitutes"] = serializers.FullDerefSubstituteSerializer(
            substitutes,
            many=True,
            context={"request": request},
        ).data

        return Response(serializer, status=status.HTTP_200_OK)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
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
    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a team
        """
        return super().delete(request, *args, **kwargs)


class TeamMatchs(generics.RetrieveAPIView[Team]):  # pylint: disable=unsubscriptable-object
    """
    Get all matchs of a team
    """

    queryset = Team.objects.all().order_by("id")
    serializer_class = serializers.TeamMatchsSerializer
    permission_classes = [permissions.IsAdminUser | permissions.IsAuthenticated]
    pagination_class = None


class AdminTeamSeeding(generics.UpdateAPIView[Team]):  # pylint: disable=unsubscriptable-object
    queryset = Team.objects.all()
    serializer_class = serializers.TeamSeedingSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        new_seeding = self.get_serializer(self.get_queryset(), data=request.data, many=True)
        if not new_seeding.is_valid():
            raise BadRequest(_("Les données sont invalides."))

        saved_seeding = new_seeding.save()

        saved_seeding_serialized = self.get_serializer(saved_seeding, many=True).data

        return Response(saved_seeding_serialized, status=status.HTTP_200_OK)
