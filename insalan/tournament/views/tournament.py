import math
from django.core.exceptions import PermissionDenied, BadRequest
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

from ..models import (Player, Manager, Substitute, Event, Tournament, Game,
                      Team, PaymentStatus, Group, Bracket, SwissRound,
                      GroupMatch, KnockoutMatch, SwissMatch, Seeding, Score,
                      BracketType, BracketSet, MatchStatus, BestofType,
                      SwissSeeding, Seating)
from .permissions import ReadOnly, Patch

from rest_framework.exceptions import NotFound

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
        try:
            tourney = Tournament.objects.select_related("event").get(id=primary_key)
        except Tournament.DoesNotExist as exc:
            raise NotFound(_("Tournament not found")) from exc

        is_staff = request.user.is_staff

        tourney_serialized = serializers.TournamentSerializer(
            tourney, context={"request": request}
        ).data
            # deref group matchs and scores

        if tourney_serialized["is_announced"]:
            # Dereference the event
            tourney_serialized["event"] = serializers.EventSerializer(
                Event.objects.get(id=tourney_serialized["event"]), context={"request": request}
            ).data

            del tourney_serialized["event"]["tournaments"]

            # Dereference the game
            tourney_serialized["game"] = serializers.GameSerializer(
                Game.objects.get(id=tourney_serialized["game"]), context={"request": request}
            ).data

            # Dereferencselect_relatede the teams
            tourney_serialized["teams"] = serializers.FullDerefTeamSerializer(
                Team.objects.filter(tournament=tourney), context={"request": request}, many=True
            ).data


            # Prepare can_see_payment_status
            user_player = None
            user_substitue = None
            if request.user.is_authenticated:
                try:
                    user_player = Player.objects.get(user=request.user, team__tournament=tourney)
                except Player.DoesNotExist:
                    try:
                        user_substitue = Substitute.objects.get(user=request.user, team__tournament=tourney)
                    except Substitute.DoesNotExist:
                        pass

            for team in tourney_serialized["teams"]:
                # dereference players, managers and substitutes
                team["players"] = serializers.FullDerefPlayerSerializer(
                    Player.objects.filter(team=team["id"]),
                    context={"request": request},
                    many=True,
                ).data
                team["managers"] = serializers.FullDerefManagerSerializer(
                    Manager.objects.filter(team=team["id"]),
                    context={"request": request},
                    many=True,
                ).data
                team["substitutes"] = serializers.FullDerefSubstituteSerializer(
                    Substitute.objects.filter(team=team["id"]),
                    context={"request": request},
                    many=True,
                ).data

                can_see_payment_status: bool = (
                    is_staff or
                    user_player is not None and user_player.id in [x["id"] for x in team["players"]] or
                    request.user.username in [x for x in team["managers"]] or
                    user_substitue is not None and user_substitue.id in [x["id"] for x in team["substitutes"]]
                )

                # remove payment status if not allowed
                for player in team["players"]:
                    if team["captain"] is not None:
                        if player["id"] == team["captain"]:
                            team["captain"] = player["name_in_game"]
                        if not can_see_payment_status:
                            player["payment_status"] = None
                            del player["id"]

                for substitute in team["substitutes"]:
                    if not can_see_payment_status:
                        substitute["payment_status"] = None
                        del substitute["id"]

            # deref group matchs and scores
            tourney_serialized["groups"] = serializers.FullDerefGroupSerializer(
                Group.objects.filter(tournament=tourney), context={"request": request}, many=True
            ).data

            for group in tourney_serialized["groups"]:
                group["teams"] = Seeding.objects.filter(group=group["id"]).values_list("team", flat=True)
                
                matches = GroupMatch.objects.filter(group=group["id"])
                group["matchs"] = serializers.FullDerefGroupMatchSerializer(
                   matches, context={"request": request}, many=True
                ).data

                scores = Score.objects.filter(match__in=matches).values("team_id", "match", "score")

                for match in group["matchs"]:
                    match["score"] = {score["team_id"]: score["score"] for score in scores if score["match"] == match["id"]}

                group["scores"] = {team: sum(match["score"][team] for match in group["matchs"] if team in match["score"]) for team in group["teams"]}

                # order teams by score
                group["teams"] = sorted(group["teams"], key=lambda x: group["scores"][x], reverse=True)

            # deref bracket matchs and scores
            tourney_serialized["brackets"] = serializers.FullDerefBracketSerializer(
                Bracket.objects.filter(tournament=tourney), context={"request": request}, many=True
            ).data

            for bracket in tourney_serialized["brackets"]:

                matches = KnockoutMatch.objects.filter(bracket=bracket["id"])

                bracket["matchs"] = serializers.FullDerefKnockoutMatchSerializer(
                    matches, context={"request": request}, many=True
                ).data

                scores = Score.objects.filter(match__in=matches).values("team_id", "match", "score")
                for match in bracket["matchs"]:
                    match["score"] = {score["team_id"]: score["score"] for score in scores if score["match"] == match["id"]}

                bracket["depth"] = math.ceil(math.log2(bracket["team_count"]/tourney_serialized["game"]["team_per_match"])) + 1

                bracket["teams"] = set(matches.values_list("teams", flat=True).filter(teams__isnull=False))

                bracket["winner"] = None

                if bracket["bracket_type"] == BracketType.SINGLE:
                    final = KnockoutMatch.objects.filter(round_number=1,index_in_round=1,bracket=bracket["id"],bracket_set=BracketSet.WINNER,status=MatchStatus.COMPLETED)
                elif bracket["bracket_type"] == BracketType.DOUBLE:
                    final = KnockoutMatch.objects.filter(round_number=0,index_in_round=1,bracket=bracket["id"],bracket_set=BracketSet.WINNER,status=MatchStatus.COMPLETED)

                if len(final) == 1:
                    bracket["winner"] = final[0].get_winners_loosers()[0][0]

                del bracket["team_count"]

            # deref swiss matchs and scores
            tourney_serialized["swissRounds"] = serializers.FullDerefSwissRoundSerializer(
                SwissRound.objects.filter(tournament=tourney), context={"request": request}, many=True
            ).data

            for swiss in tourney_serialized["swissRounds"]:
                matches = SwissMatch.objects.filter(swiss=swiss["id"])

                swiss["matchs"] = serializers.FullDerefSwissMatchSerializer(
                    matches, context={"request": request}, many=True
                ).data

                scores = Score.objects.filter(match__in=matches).values("team_id", "match", "score")
                for match in swiss["matchs"]:
                    match["score"] = {score["team_id"]: score["score"] for score in scores if score["match"] == match["id"]}

                swiss["teams"] = SwissSeeding.objects.filter(swiss=swiss["id"]).values_list("team", flat=True)

            tourney_serialized["seatings"] = serializers.SeatingSerializer(
                Seating.objects.filter(tournament=tourney), context={"request": request}, many=True
            ).data

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
