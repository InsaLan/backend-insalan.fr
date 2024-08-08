from django.core.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import insalan.tournament.serializers as serializers

from ..models import Seat, Event
from .permissions import ReadOnly


class SeatCreationList(generics.ListCreateAPIView):
    """Create a list of seats"""

    pagination_class = None
    serializer_class = serializers.SeatSerializer
    queryset = Seat.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("many", True)
        return super().get_serializer(*args, **kwargs)

    @swagger_auto_schema(
        request_body=serializers.SeatSerializer(many=True),
        responses={
            201: serializer_class(many=True),
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
                        type=openapi.TYPE_STRING, description=_("Évènement introuvable")
                    )
                },
            ),
            409: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                options={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING, description=_("Place déjà existante")
                    )
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        seats = request.data

        for i, seat in enumerate(seats):
            if "event" not in seat or "x" not in seat or "y" not in seat:
                raise BadRequest(_("Un Place manque un champ obligatoire"))

        # ensure all seats have the same event
        event_ids = set([seat["event"] for seat in seats])
        if len(event_ids) > 1:
            raise BadRequest(_("Tous les Places doivent appartenir au même évènement"))

        # check if the event exists
        if not Event.objects.filter(id=event_ids.pop()).exists():
            return Response(
                _("Évènement introuvable"), status=status.HTTP_404_NOT_FOUND
            )

        # check if any two seats are identical
        for i, seat1 in enumerate(seats):
            for seat2 in seats[i + 1 :]:
                if seat1["x"] == seat2["x"] and seat1["y"] == seat2["y"]:
                    raise BadRequest(_("Deux places sont identiques"))

        # Check if any seats already exist
        existing_seats = Seat.objects.filter(
            event__id__in=[seat["event"] for seat in seats],
            x__in=[seat["x"] for seat in seats],
            y__in=[seat["y"] for seat in seats],
        )

        if existing_seats.exists():
            return Response(_("Place déjà existante"), status=status.HTTP_409_CONFLICT)

        return super().post(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)
        ),
        responses={
            204: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_STRING, description=_("Places supprimée")
                    )
                },
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                options={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING, description=_("Place introuvable")
                    )
                },
            ),
        },
    )
    def delete(self, request, *args, **kwargs):
        seat_ids = request.data

        # Ensure all seats to be deleted are valid
        existing_seats = Seat.objects.filter(id__in=seat_ids)
        if len(seat_ids) != len(existing_seats):
            return Response(
                {"err": _("Place introuvable")}, status=status.HTTP_404_NOT_FOUND
            )

        for seat in existing_seats:
            seat.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
