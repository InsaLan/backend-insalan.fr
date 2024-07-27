from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class SeatSlot(models.Model):
    """
    Represents a single seat
    """

    tournament = models.ForeignKey(
        "Tournament",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name=_("Tournoi"),
    )

    seats = models.ManyToManyField(
        "Seat",
        verbose_name=_("Place"),
    )

    class Meta:
        """Meta Options"""

        verbose_name = _("Slot")
        verbose_name_plural = _("Slots")

    def clean(self):
        """
        Ensure that the number of seats is consistent with the tournament
        """
        if self.seats.count() > self.tournament.game.players_per_team:
            raise ValidationError(
            _("Le nombre de places est trop grand pour ce tournoi")
            )

