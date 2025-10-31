from django.db import models
from django.utils.translation import gettext_lazy as _


class Seat(models.Model):
    """
    Represents a single seat
    """

    event = models.ForeignKey(
        "Event",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name=_("Évènement"),
    )
    x = models.IntegerField(
        null=False,
        blank=False,
        verbose_name=_("Position horizontale"),
    )
    y = models.IntegerField(
        null=False,
        blank=False,
        verbose_name=_("Position verticale"),
    )

    class Meta:
        """Meta Options"""

        verbose_name = _("Place")
        verbose_name_plural = _("Places")
        constraints = [
            models.UniqueConstraint(
                fields=["event", "x", "y"], name="one_seat_per_position_per_event"
            )
        ]

    def __str__(self) -> str:
        return f"{self.event} - ({self.x}, {self.y})"
