"""This module contains the views for the ecological statistics app."""

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import TravelData
from .serializers import TravelDataSerializer


class CreateTravelData(CreateAPIView[TravelData]):  # pylint: disable=unsubscriptable-object
    """Create a new TravalData."""

    serializer_class = TravelDataSerializer
    permission_classes = [IsAuthenticated]
