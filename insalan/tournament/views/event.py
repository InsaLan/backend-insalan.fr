from django.http import Http404
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.tournament import serializers

from ..models import Event, Tournament
from .permissions import ReadOnly

class EventList(generics.ListCreateAPIView):
    """List all of the existing events"""

    pagination_class = None
    queryset = Event.objects.all().order_by("id")
    serializer_class = serializers.EventSerializer
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
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """Create an event"""
        return super().post(request, *args, **kwargs)

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

    @swagger_auto_schema(
        request_body=serializers.EventSerializer,
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
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Évènement introuvable")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier cet évènement")
                    )
                }
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """Update an event"""
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            204: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Évènement supprimé")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Évènement introuvable")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à supprimer cet évènement")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """Delete an event"""
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
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Évènement introuvable")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier cet évènement")
                    )
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """Partially update an event"""
        return super().patch(request, *args, **kwargs)


class EventDetailsSomeDeref(generics.RetrieveAPIView):
    """Details about an Event that dereferences tournaments, but nothing else"""
    serializer_class = serializers.TournamentSerializer

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("ID du tournoi")
                        ),
                        "name": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Nom du tournoi")
                        ),
                        "is_announced": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description=_("Tournoi annoncé")
                        ),
                        "event": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("ID de l'évènement")
                        )
                    }
                )
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Évènement introuvable")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à voir cet évènement")
                    )
                }
            )
        }
    )
    def get(self, request, primary_key: int):
        """
        Get the tournaments of an event
        """
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
