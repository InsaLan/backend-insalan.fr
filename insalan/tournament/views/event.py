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

from ..models import Player, Manager, Substitute, Event, Tournament, Game, Team, PaymentStatus
from .permissions import ReadOnly, Patch

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