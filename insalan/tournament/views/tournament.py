from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.tickets.models import Ticket
from insalan.user.models import User
import insalan.tournament.serializers as serializers

from ..models import Player, Manager, Substitute, Event, Tournament, Team, Group, Bracket, SwissRound, GroupMatch, KnockoutMatch, SwissMatch
from .permissions import ReadOnly

class TournamentList(generics.ListCreateAPIView):
    """List all known tournaments"""

    pagination_class = None
    queryset = Tournament.objects.all().order_by("id")
    serializer_class = serializers.TournamentSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

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
                        description=_("Vous n'êtes pas autorisé à créer un tournoi")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """Create a tournament"""
        return super().post(request, *args, **kwargs)


class TournamentDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a tournament"""

    queryset = Tournament.objects.all().order_by("id")
    serializer_class = serializers.TournamentSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
        responses={
            200: serializer_class,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Tournoi introuvable")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """Get a tournament"""
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
                        description=_("Vous n'êtes pas autorisé à modifier un tournoi")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Tournoi introuvable")
                    )
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """Patch a tournament"""
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        responses={
            204: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Tournoi supprimé")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à supprimer un tournoi")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Tournoi introuvable")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """Delete a tournament"""
        return super().delete(request, *args, **kwargs)
    
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
                        description=_("Vous n'êtes pas autorisé à modifier un tournoi")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Tournoi introuvable")
                    )
                }
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """Put a tournament"""
        return super().put(request, *args, **kwargs)


class TournamentDetailsFull(generics.RetrieveAPIView):
    """Details about a tournament, with full dereferencing of data"""
    serializer_class = serializers.TournamentSerializer

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
                team_preser["captain"] = Player.objects.get(id=team_preser["captain"]).as_user().username if team_preser["captain"] is not None else None
                teams_serialized.append(team_preser)
            # deref groups
            group_serialized = []
            for group in tourney.get_groups():
                group_data = serializers.GroupSerializer(Group.objects.get(pk=group), context={"request": request}).data
                for match in group_data["matchs"]:
                    del match["group"]
                group_serialized.append(group_data)
            # deref bracket

            bracket_serialized = []
            for bracket in tourney.get_brackets():
                bracket_data = serializers.BracketSerializer(Bracket.objects.get(pk=bracket), context={"request": request}).data
                for match in bracket_data["matchs"]:
                    del match["bracket"]

                bracket_serialized.append(bracket_data)
            # deref swissRound 
            swiss_serialized = []
            for swissRound in tourney.get_swissRounds():
                swiss_data = serializers.SwissRoundSerializer(SwissRound.objects.get(pk=swissRound), context={"request": request}).data
                for match in swiss_data["matchs"]:
                    del match["swiss"]

                swiss_serialized.append(swiss_data)


            tourney_serialized["groups"].clear()
            tourney_serialized["brackets"].clear()
            tourney_serialized["swissRounds"].clear()
            tourney_serialized["teams"].clear()
            tourney_serialized["teams"] = teams_serialized
            tourney_serialized["groups"] = group_serialized
            tourney_serialized["brackets"] = bracket_serialized
            tourney_serialized["swissRounds"] = swiss_serialized

        return Response(tourney_serialized, status=status.HTTP_200_OK)


class TournamentMe(generics.RetrieveAPIView):
    """
    Details on tournament of a logged user
    This endpoint does many requests to the database and should be used wisely
    """
    authentication_classes =  [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated & ReadOnly]
    serializer_class = serializers.PlayerSerializer
    pagination_class = None

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "player": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "name_in_game": openapi.Schema(type=openapi.TYPE_STRING),
                                "team": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                                        "tournament": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                                "event": openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        "name": openapi.Schema(type=openapi.TYPE_STRING)
                                                    }
                                                )
                                            }
                                        )
                                    }
                                ),
                                "ticket": openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    "manager": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "team": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                                        "tournament": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                                "event": openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        "name": openapi.Schema(type=openapi.TYPE_STRING)
                                                    }
                                                )
                                            }
                                        )
                                    }
                                ),
                                "ticket": openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    "substitute": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "name_in_game": openapi.Schema(type=openapi.TYPE_STRING),
                                "team": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "name": openapi.Schema(type=openapi.TYPE_STRING),
                                        "tournament": openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                                "event": openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                                        "name": openapi.Schema(type=openapi.TYPE_STRING)
                                                    }
                                                )
                                            }
                                        )
                                    }
                                ),
                                "ticket": openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    ),
                    "ongoing_match": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "match_type": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "type": openapi.Schema(type=openapi.TYPE_STRING),
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            ),
                            "teams": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
                            )
                        }
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à accéder à ces informations")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        GET handler
        """
        user: User = request.user
        ongoing_matchs = []

        if user is None:
            raise PermissionDenied()

        # retrieve registration as Player
        players = Player.objects.filter(user=user)

        # serialize current ongoing match
        for player in players :
            ongoing_matchs += player.get_ongoing_match()

        if len(ongoing_matchs) > 0:
            if type(ongoing_matchs[0]) == GroupMatch:
                ongoing_match = serializers.GroupMatchSerializer(ongoing_matchs[0],context={"request": request}).data
                ongoing_match["match_type"] = {"type": "group", "id": ongoing_match["group"]}
                del ongoing_match["group"]

            if type(ongoing_matchs[0]) == KnockoutMatch:
                ongoing_match = serializers.KnockoutMatchSerializer(ongoing_matchs[0],context={"request": request}).data
                ongoing_match["match_type"] = {"type": "bracket", "id": ongoing_match["bracket"]}
                del ongoing_match["bracket"]

            if type(ongoing_matchs[0]) == SwissMatch:
                ongoing_match = serializers.SwissMatchSerializer(ongoing_matchs[0],context={"request": request}).data
                ongoing_match["match_type"] = {"type": "swiss", "id": ongoing_match["swiss"]}
                del ongoing_match["swiss"]

            del ongoing_match["score"]
            del ongoing_match["times"]
            del ongoing_match["status"]

            team_list = {}
            for team in ongoing_match["teams"]:
                team_list[str(team)] = Team.objects.get(pk=team).get_name()

            ongoing_match["teams"] = team_list
        else:
            ongoing_match = None

        # serialize registration as Player
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

        return Response({"player": players, "manager": managers, "substitute": substitutes,"ongoing_match": ongoing_match}, status=status.HTTP_200_OK)
