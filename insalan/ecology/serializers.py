"""This module contains serializers for the ecological statistics app."""

from rest_framework.serializers import ModelSerializer

from .models import TravelData


class TravelDataSerializer(ModelSerializer[TravelData]):
    """Serializer for the TravelData model."""

    class Meta:
        """Meta class for the TravelDataSerializer."""

        model = TravelData
        fields = ("id", "city", "transportation_method", "event")
