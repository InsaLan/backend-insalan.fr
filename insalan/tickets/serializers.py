"""Serializers for our objects"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from .models import Ticket

class TicketSerializer(serializers.Serializer):
    """Serializer for a ticket"""

    class Meta:
        """Meta options of the serializer"""

        model = Ticket
        fields = "__all__"
        read_only_fields = ("token", "user", "status", "tournament")
