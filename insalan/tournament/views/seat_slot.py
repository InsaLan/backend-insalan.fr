from django.core.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import insalan.tournament.serializers as serializers

from ..models import Seat, SeatSlot, Tournament
from .permissions import ReadOnly


class SeatSlotList(generics.ListCreateAPIView):
    """List all SeatSlots"""

    pagination_class = None
    serializer_class = serializers.SeatSlotSerializer
    queryset = SeatSlot.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
        responses={
            201: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                options={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING, description=_("Requête invalide")
                    )
                },
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                options={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING, description=_("Tournoi introuvable")
                    )
                },
            ),
            409: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                options={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING, description=_("Conflit de place")
                    )
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        seat_slot = request.data

        if "tournament" not in seat_slot or "seats" not in seat_slot:
            raise BadRequest(_("Il manque un champ obligatoire"))

        # check that the tournament exists
        tournament = Tournament.objects.filter(id=seat_slot["tournament"])
        if not tournament.exists():
            return Response(_("Tournoi introuvable"), status=status.HTTP_404_NOT_FOUND)
        tournament = tournament.get()

        # ensure all seats exist
        seat_ids = seat_slot["seats"]
        seats = Seat.objects.filter(id__in=seat_ids)
        if len(seats) != len(seat_ids):
            raise BadRequest(_("Certaines places n'existent pas"))

        # Ensure that the number of seats is consistent with the tournament
        if seats.count() != tournament.game.players_per_team:
            raise BadRequest(_("Le nombre de places est incorrect pour ce tournoi"))

        # ensure all seats have the same event
        events = set([seat.event for seat in seats])
        if len(events) > 1:
            raise BadRequest(_("Tous les Places doivent appartenir au même évènement"))

        # Check if any seats are already taken
        other_slots = SeatSlot.objects.all()
        other_seats = {seat for slot in other_slots for seat in slot.seats.all()}
        if other_seats.intersection(seats):
            return Response(
                _("Les places ne peuvent pas être partagés entre plusieurs slots"),
                status=status.HTTP_409_CONFLICT,
            )

        return super().post(request, *args, **kwargs)


class SeatSlotDetails(generics.RetrieveUpdateDestroyAPIView):
    """Create SeatSlots"""

    serializer_class = serializers.SeatSlotSerializer
    queryset = SeatSlot.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]
