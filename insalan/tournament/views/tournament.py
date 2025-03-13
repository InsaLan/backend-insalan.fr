from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.tickets.models import Ticket
from insalan.user.models import User
from insalan.tournament import serializers

from ..models import (
    Player,
    Manager,
    Substitute,
    Event,
    BaseTournament,
    EventTournament,
    PrivateTournament,
    Team,
    GroupMatch,
    KnockoutMatch,
    SwissMatch,
)
from .permissions import ReadOnly

class PrivateTournamentList(generics.ListAPIView):
    """List all known private tournaments"""

    pagination_class = None
    queryset = PrivateTournament.objects.filter(running=True).order_by("id")
    serializer_class = serializers.PrivateTournamentSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]


class TournamentList(generics.ListCreateAPIView):
    """List all known tournaments"""

    pagination_class = None
    queryset = EventTournament.objects.all().order_by("id")
    serializer_class = serializers.EventTournamentSerializer
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

    queryset = EventTournament.objects.all().order_by("id")
    serializer_class = serializers.EventTournamentSerializer
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
    serializer_class = serializers.FullDerefEventTournamentSerializer
    queryset = EventTournament.objects.all().prefetch_related("event__seat_set","game","teams","group_set__groupmatch_set","bracket_set__knockoutmatch_set","swissround_set__swissmatch_set","seatslot_set__seats")

    def get(self, request, pk: int):
        tourney = self.get_object()
        tourney_serialized = self.get_serializer(tourney).data

        if not tourney_serialized["is_announced"]:
            return Response(tourney_serialized, status=status.HTTP_200_OK)

        is_staff = request.user.is_staff

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
            can_see_payment_status: bool = (
                is_staff or
                user_player is not None and user_player.id in [x["id"] for x in team["players"]] or
                request.user.username in [x for x in team["managers"]] or
                user_substitue is not None and user_substitue.id in [x["id"] for x in team["substitutes"]]
            )

            # remove payment status if not allowed
            for player in team["players"]:
                if not can_see_payment_status:
                    player["payment_status"] = None
                    del player["id"]

            for substitute in team["substitutes"]:
                if not can_see_payment_status:
                    substitute["payment_status"] = None
                    del substitute["id"]

            if not is_staff:
                del team["seed"]

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
            if isinstance(ongoing_matchs[0], GroupMatch):
                ongoing_match = serializers.GroupMatchSerializer(ongoing_matchs[0],context={"request": request}).data
                ongoing_match["match_type"] = {"type": "group", "id": ongoing_match["group"]}
                del ongoing_match["group"]

            if isinstance(ongoing_matchs[0], KnockoutMatch):
                ongoing_match = serializers.KnockoutMatchSerializer(ongoing_matchs[0],context={"request": request}).data
                ongoing_match["match_type"] = {"type": "bracket", "id": ongoing_match["bracket"]}
                del ongoing_match["bracket"]

            if isinstance(ongoing_matchs[0], SwissMatch):
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
            player["team"]["tournament"] = serializers.BaseTournamentSerializer(
                BaseTournament.objects.get(id=player["team"]["tournament"]),
                context={"request": request},
            ).data
            if "event" in player["team"]["tournament"]:
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
            manager["team"]["tournament"] = serializers.BaseTournamentSerializer(
                EventTournament.objects.get(id=manager["team"]["tournament"]),
                context={"request": request},
            ).data
            if "event" in player["team"]["tournament"]:
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
            if "event" in player["team"]["tournament"]:
                # dereference tournament
                substitute["team"]["tournament"] = serializers.BaseTournamentSerializer(
                    EventTournament.objects.get(id=substitute["team"]["tournament"]),
                    context={"request": request},
                ).data
            # dereference event
            substitute["team"]["tournament"]["event"] = serializers.EventSerializer(
                Event.objects.get(id=substitute["team"]["tournament"]["event"]),
                context={"request": request},
            ).data
            substitute["ticket"] = Ticket.objects.get(id=substitute["ticket"]).token if substitute["ticket"] is not None else None

        return Response({"player": players, "manager": managers, "substitute": substitutes,"ongoing_match": ongoing_match}, status=status.HTTP_200_OK)
