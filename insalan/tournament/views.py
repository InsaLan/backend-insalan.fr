"""Views for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

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

from insalan.user.models import User, UserMailer
import insalan.tournament.serializers as serializers
from insalan.tickets.serializers import TicketSerializer
from insalan.tickets.models import Ticket

from .models import Player, Manager, Substitute, Event, Tournament, Game, Team, PaymentStatus

class ReadOnly(BasePermission):
    """Read-Only permissions"""

    def has_permission(self, request, _view):
        """Define the permissions for this class"""
        return request.method in SAFE_METHODS

class Patch(BasePermission):
    """Is the request using HTTP Method PATCH"""

    def has_permission(self, request, _view):
        """Define the permissions for this class"""
        return request.method == "PATCH"


class EventList(generics.ListCreateAPIView):
    """List all of the existing events"""

    pagination_class = None
    queryset = Event.objects.all().order_by("id")
    serializer_class = serializers.EventSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]


class OngoingEventList(generics.ListAPIView):
    """List all of the ongoing events"""

    pagination_class = None
    queryset = Event.objects.filter(ongoing=True).order_by("id")
    serializer_class = serializers.EventSerializer
    permission_classes = [permissions.AllowAny]


class EventDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about an Event"""

    serializer_class = serializers.EventSerializer
    queryset = Event.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]


class EventDetailsSomeDeref(APIView):
    """Details about an Event that dereferences tournaments, but nothing else"""

    def get(self, request, primary_key: int):
        """GET handler"""
        candidates = Event.objects.filter(id=primary_key)
        if len(candidates) == 0:
            raise Http404
        if len(candidates) > 1:
            return Response("", status=status.HTTP_400_BAD_REQUEST)

        event = candidates[0]

        event_serialized = serializers.EventSerializer(
            event, context={"request": request}
        ).data

        event_serialized["tournaments"] = [
            serializers.TournamentSerializer(
                Tournament.objects.get(id=id), context={"request": request}
            ).data
            for id in event_serialized["tournaments"]
        ]

        for tourney in event_serialized["tournaments"]:
            if tourney["is_announced"] :
                del tourney["event"]

        return Response(event_serialized, status=status.HTTP_200_OK)


class EventByYear(generics.ListAPIView):
    """Get all of the events of a year"""

    pagination_class = None
    serializer_class = serializers.EventSerializer

    def get_queryset(self):
        """Return the queryset"""
        return Event.objects.filter(year=int(self.kwargs["year"]))


# Games
class GameList(generics.ListCreateAPIView):
    """List all known games"""

    pagination_class = None
    queryset = Game.objects.all().order_by("id")
    serializer_class = serializers.GameSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]


class GameDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a game"""

    serializer_class = serializers.GameSerializer
    queryset = Game.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]


# Tournament
class TournamentList(generics.ListCreateAPIView):
    """List all known tournaments"""

    pagination_class = None
    queryset = Tournament.objects.all().order_by("id")
    serializer_class = serializers.TournamentSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]


class TournamentDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a tournament"""

    queryset = Tournament.objects.all().order_by("id")
    serializer_class = serializers.TournamentSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]


class TournamentDetailsFull(APIView):
    """Details about a tournament, with full dereferencing of data"""

    def get(self, request, primary_key: int):
        """Handle the GET word"""

        # Alright, let's try and get the object
        tourneys = Tournament.objects.filter(id=primary_key)
        if len(tourneys) == 0:
            raise Http404
        if len(tourneys) > 1:
            return Response("", status=status.HTTP_400_BAD_REQUEST)
        tourney = tourneys[0]

        tourney_serialized = serializers.TournamentSerializer(
            tourney, context={"request": request}
        ).data

        if tourney_serialized["is_announced"]:
            # Dereference the event
            event = tourney.event
            tourney_serialized["event"] = serializers.EventSerializer(
                event, context={"request": request}
            ).data
            del tourney_serialized["event"]["tournaments"]

            # Dereference the game
            tourney_serialized["game"] = serializers.GameSerializer(
                tourney.game, context={"request": request}
            ).data

            user_player = None
            user_manager = None
            user_substitue = None
            if request.user.is_authenticated:
                try:
                    user_player = Player.objects.get(user=request.user, team__tournament=tourney)
                except Player.DoesNotExist:
                    pass
                try:
                    user_manager = Manager.objects.get(user=request.user, team__tournament=tourney)
                except Manager.DoesNotExist:
                    pass
                try:
                    user_substitue = Substitute.objects.get(user=request.user, team__tournament=tourney)
                except Substitute.DoesNotExist:
                    pass

            # Dereference the teams
            teams_serialized = []
            for team in tourney_serialized["teams"]:
                team_preser = serializers.TeamSerializer(
                    Team.objects.get(id=team), context={"request": request}
                ).data
                del team_preser["tournament"]

                can_see_payment_status: bool = (
                    request.user.is_staff or
                    user_player is not None and user_player.id in team_preser["players"] or
                    user_manager is not None and user_manager.id in team_preser["managers"] or
                    user_substitue is not None and user_substitue.id in team_preser["substitutes"]
                )
                # Dereference players/managers to name_in_game
                team_preser["players"] = [
                    {
                        "user": Player.objects.get(id=pid).as_user().username,
                        "name_in_game": Player.objects.get(id=pid).name_in_game,
                        "payment_status": Player.objects.get(id=pid).payment_status if can_see_payment_status else None
                    } for pid in team_preser["players"]
                ]
                team_preser["managers"] = [
                    Manager.objects.get(id=pid).as_user().username for pid in team_preser["managers"]
                ]
                team_preser["substitutes"] = [
                    {
                        "user": Substitute.objects.get(id=pid).as_user().username,
                        "name_in_game": Substitute.objects.get(id=pid).name_in_game,
                        "payment_status": Substitute.objects.get(id=pid).payment_status if can_see_payment_status else None
                    } for pid in team_preser["substitutes"]
                ]
                teams_serialized.append(team_preser)


            tourney_serialized["teams"].clear()
            tourney_serialized["teams"] = teams_serialized

        return Response(tourney_serialized, status=status.HTTP_200_OK)


class TournamentMe(APIView):
    """
    Details on tournament of a logged user
    This endpoint does many requests to the database and should be used wisely
    """
    authentication_classes =  [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated & ReadOnly]

    def get(self, request):
        """
        GET handler
        """
        user: User = request.user

        if user is None:
            raise PermissionDenied()

        # retrieve registration as Player
        players = Player.objects.filter(user=user)
        # serialize it
        players = serializers.PlayerSerializer(
            players, context={"request": request}, many=True
        ).data
        for player in players:
            # dereference team
            player["team"] = serializers.TeamSerializer(
                Team.objects.get(id=player["team"]), context={"request": request}
            ).data
            # dereference tournament
            player["team"]["tournament"] = serializers.TournamentSerializer(
                Tournament.objects.get(id=player["team"]["tournament"]),
                context={"request": request},
            ).data
            # dereference event
            player["team"]["tournament"]["event"] = serializers.EventSerializer(
                Event.objects.get(id=player["team"]["tournament"]["event"]),
                context={"request": request},
            ).data
            player["ticket"] = Ticket.objects.get(id=player["ticket"]).token if player["ticket"] is not None else None

        # retrieve registration as Manager
        managers = Manager.objects.filter(user=user)
        # serialize it
        managers = serializers.ManagerSerializer(
            managers, context={"request": request}, many=True
        ).data
        for manager in managers:
            # dereference team
            manager["team"] = serializers.TeamSerializer(
                Team.objects.get(id=manager["team"]), context={"request": request}
            ).data
            # dereference tournament
            manager["team"]["tournament"] = serializers.TournamentSerializer(
                Tournament.objects.get(id=manager["team"]["tournament"]),
                context={"request": request},
            ).data
            # dereference event
            manager["team"]["tournament"]["event"] = serializers.EventSerializer(
                Event.objects.get(id=manager["team"]["tournament"]["event"]),
                context={"request": request},
            ).data
            manager["ticket"] = Ticket.objects.get(id=manager["ticket"]).token if manager["ticket"] is not None else None

        # retrieve registration as Substitute
        substitutes = Substitute.objects.filter(user=user)
        # serialize it
        substitutes = serializers.SubstituteSerializer(
            substitutes, context={"request": request}, many=True
        ).data
        for substitute in substitutes:
            # dereference team
            substitute["team"] = serializers.TeamSerializer(
                Team.objects.get(id=substitute["team"]), context={"request": request}
            ).data
            # dereference tournament
            substitute["team"]["tournament"] = serializers.TournamentSerializer(
                Tournament.objects.get(id=substitute["team"]["tournament"]),
                context={"request": request},
            ).data
            # dereference event
            substitute["team"]["tournament"]["event"] = serializers.EventSerializer(
                Event.objects.get(id=substitute["team"]["tournament"]["event"]),
                context={"request": request},
            ).data
            substitute["ticket"] = Ticket.objects.get(id=substitute["ticket"]).token if substitute["ticket"] is not None else None

        return Response({"player": players, "manager": managers, "substitute": substitutes}, status=status.HTTP_200_OK)


# Teams
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
                    UserMailer.send_kick_mail(player.as_user(), team.name)
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
                    UserMailer.send_kick_mail(manager.as_user(), team.name)
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
                    UserMailer.send_kick_mail(substitute.as_user(), team.name)
                    substitute.delete()

        team.save()

        serializer = serializers.TeamSerializer(team, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

# Registration finders
class PlayerRegistration(generics.RetrieveAPIView):
    """Get the registration of a player"""

    serializer_class = serializers.PlayerSerializer
    queryset = Player.objects.all().order_by("id")

    def patch(self, request, *args, **kwargs):
        """
        Patch a player
        """
        user = request.user
        data = request.data

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the player
        player = Player.objects.get(id=kwargs["pk"])

        # check if the user is related to the player
        if player.as_user().id != user.id:
            return Response({
                "player": _("Vous n'avez pas la permission de modifier cette inscription.")
            }, status=status.HTTP_403_FORBIDDEN)

        if "name_in_game" in data:
            player.name_in_game = data["name_in_game"]

        player.save()

        serializer = serializers.PlayerSerializer(player, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Delete a player
        """
        user = request.user

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the player
        player = Player.objects.get(id=kwargs["pk"])

        # check if the user is related to the player
        if player.as_user().id != user.id:
            return Response({
                "player": _("Vous n'avez pas la permission de supprimer cette inscription.")
            }, status=status.HTTP_403_FORBIDDEN)

        # if player has paid, can't delete
        if player.payment_status != PaymentStatus.NOT_PAID:
            return Response({
                "player": _("Vous ne pouvez pas supprimer votre inscription si vous avez payé.")
            }, status=status.HTTP_403_FORBIDDEN)

        player.delete()

        # if the team is empty, delete it
        if len(player.team.get_players_id()) == 0 \
            and len(player.team.get_managers_id()) == 0 \
            and len(player.team.get_substitutes_id()) == 0:
            player.team.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PlayerRegistrationList(generics.ListCreateAPIView):
    """Get all player registrations"""

    pagination_class = None
    serializer_class = serializers.PlayerSerializer
    queryset = Player.objects.all().order_by("id")

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        if (
            user is None
            or not user.is_authenticated
        ):
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


class PlayerRegistrationListId(generics.ListAPIView):
    """Find all player registrations of a user from their ID"""

    pagination_class = None
    serializer_class = serializers.PlayerIdSerializer

    def get_queryset(self):
        """Obtain the queryset fot this view"""
        return Player.objects.filter(user_id=self.kwargs["user_id"])


class PlayerRegistrationListName(generics.ListAPIView):
    """Find all player registrations of a user from their username"""

    pagination_class = None
    serializer_class = serializers.PlayerIdSerializer

    def get_queryset(self):
        """Obtain the queryset fot this view"""
        user = None
        try:
            user = User.objects.get(username=self.kwargs["username"])
        except User.DoesNotExist as exc:
            raise NotFound() from exc
        return Player.objects.filter(user=user)


class ManagerRegistration(generics.RetrieveAPIView):
    """Show a manager registration"""

    serializer_class = serializers.ManagerSerializer
    queryset = Manager.objects.all().order_by("id")

    def delete(self, request, *args, **kwargs):
        """
        Delete a manager
        """
        user = request.user

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the manager
        manager = Manager.objects.get(id=kwargs["pk"])

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


class ManagerRegistrationList(generics.ListCreateAPIView):
    """Show all manager registrations"""

    pagination_class = None
    serializer_class = serializers.ManagerSerializer
    queryset = Manager.objects.all().order_by("id")

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

class SubstituteRegistration(generics.RetrieveAPIView):
    """Show a substitute registration"""

    serializer_class = serializers.SubstituteSerializer
    queryset = Substitute.objects.all().order_by("id")

    def patch(self, request, *args, **kwargs):
        """
        Patch a substitute
        """
        user = request.user
        data = request.data

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the substitute
        substitute = Substitute.objects.get(id=kwargs["pk"])

        # check if the user is related to the substitute
        if substitute.as_user().id != user.id:
            return Response({
                "substitute": _("Vous n'avez pas la permission de modifier cette inscription.")
            }, status=status.HTTP_403_FORBIDDEN)

        if "name_in_game" in data:
            substitute.name_in_game = data["name_in_game"]

        substitute.save()

        serializer = serializers.SubstituteSerializer(substitute, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Delete a substitute
        """
        user = request.user

        if user is None or not user.is_authenticated:
            raise PermissionDenied()

        # get the substitute
        substitute = Substitute.objects.get(id=kwargs["pk"])

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
