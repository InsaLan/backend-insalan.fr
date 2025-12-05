"""This module contains the views for the ecological statistics app."""

from typing import Any

from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from insalan.tournament.models import EventTournament, Manager, Player, Substitute
from insalan.user.models import User

from .models import TravelData
from .serializers import TravelDataSerializer


class CreateTravelData(CreateAPIView[TravelData]):  # pylint: disable=unsubscriptable-object
    """Create a new TravelData."""

    serializer_class = TravelDataSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        tournament_id = request.data.get("tournament")
        if tournament_id is None:
            return Response({
                "tournament": _("Champ manquant"),
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            tournament = EventTournament.objects.get(pk=tournament_id)
        except EventTournament.DoesNotExist:
            return Response({
                "detail": _("Tournois invalide"),
            }, status=status.HTTP_400_BAD_REQUEST)

        assert isinstance(request.user, User), 'User must be authenticated to access this route'
        registration = self.get_user_registration(tournament, request.user)
        if registration is None:
            return Response({
                "detail": _("L'utilisateur n'est pas inscrit au tournois"),
            }, status=status.HTTP_400_BAD_REQUEST)

        if registration.ecological_data_sent:
            return Response({
                "detail": _("Données écologique déjà envoyées"),
            }, status=status.HTTP_400_BAD_REQUEST)

        registration.ecological_data_sent = True
        registration.save(update_fields=['ecological_data_sent'])

        return super().post(request, *args ,**kwargs)

    def get_user_registration(self, tournament: EventTournament, user: User
                              ) -> Manager | Player | Substitute | None:
        """Return the registration of a user in the tournament or return None."""
        try:
            manager = Manager.objects.get(user=user, team__tournament=tournament)
        except Manager.DoesNotExist:
            pass
        else:
            return manager

        try:
            player = Player.objects.get(user=user, team__tournament=tournament)
        except Player.DoesNotExist:
            pass
        else:
            return player

        try:
            substitute = Substitute.objects.get(user=user, team__tournament=tournament)
        except Substitute.DoesNotExist:
            pass
        else:
            return substitute

        return None
