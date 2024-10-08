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

