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

from ..models import Player, Manager, Substitute, Event, Tournament, Game, Team, PaymentStatus, Group, Bracket, SwissRound
from .permissions import ReadOnly, Patch


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

            for group in tourney.get_groups():
                group_data = serializers.GroupSerializer(Group.objects.get(pk=group), context={"request": request}).data
                for match in group_data["matchs"]:
                    del match["group"]
                tourney_serialized["groups"].append(group_data)

            for bracket in tourney.get_brackets():
                bracket_data = serializers.BracketSerializer(Bracket.objects.get(pk=bracket), context={"request": request}).data
                for match in bracket_data["matchs"]:
                    del match["bracket"]
                tourney_serialized["brackets"].append(bracket_data)
            
            for swissRound in tourney.get_swissRounds():
                swiss_data = serializers.SwissRoundSerializer(SwissRound.objects.get(pk=swissRound), context={"request": request}).data
                for match in swiss_data["matchs"]:
                    del match["swiss"]
                tourney_serialized["swissRounds"].append(swiss_data)

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

        return Response({"player": players, "manager": managers, "substitute": substitutes}, status=status.HTTP_200_OK)
