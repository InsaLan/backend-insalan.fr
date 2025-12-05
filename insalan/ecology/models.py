"""
This module contains the models for the ecological statistics app.

It includes the following models:
- TravelData: Represents the travel informations of a person coming to an event.
"""

from django.db.models import CASCADE, CharField, ForeignKey, Model, TextChoices
from django.utils.translation import gettext_lazy as _

from insalan.tournament.models import Event


class TransportationMethod(TextChoices):
    """Enum with all transportation method used by """

    BIKE = "BIKE", _("Vélo")
    BUS = "BUS", _("Bus")
    BOAT = "BOAT", _("Bateau")
    CAR = "CAR", _("Voiture")
    CARPOOLING = "CARPOOLING", _("Covoiturage")
    NONE = "NONE", _("Aucun")
    PLANE = "PLANE", _("Avion")
    PUBLIC_TRANSPORT = "PUBLIC_TRANSPORT", _("Transport public urbain")
    TRAIN = "TRAIN", _("Train")


class TravelData(Model):
    """
    Model representing anonymous information about how a person traveled to the
    event.
    """

    city = CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name=_("Ville de départ"),
        help_text=_("Ville de départ depuis laquelle le voyage est effectué."),
    )
    transportation_method = CharField(
        choices=TransportationMethod.choices,
        max_length=max(len(choice) for choice, _ in TransportationMethod.choices),
        null=False,
        blank=False,
        verbose_name=_("Mode de transport"),
        help_text=_("Mode de transport utilisé pour se rendre à l'évènement."),
    )
    event = ForeignKey(
        Event,
        null=False,
        blank=False,
        on_delete=CASCADE,
        verbose_name=_("Évènement"),
        help_text=_("Évènement pour lequel le déplacement est effectué."),
    )

    class Meta:
        """Meta class for the TravelData model."""

        verbose_name = _("Information de déplacement")
        verbose_name_plural = _("Informations de déplacement")

    def __str__(self) -> str:
        """Return the string representation of a TravelData."""
        return f"{self.city} - {self.get_transportation_method_display()} - {self.event}"
