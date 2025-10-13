from typing import List
from django.db import models
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    MinLengthValidator,
)
from django.utils.translation import gettext_lazy as _

from insalan.components.image_field import ImageField

from . import tournament


class Event(models.Model):
    """
    An Event is any single event that is characterized by the following:
     - A single player can only register for a single tournament per event

    This means, for example, that if we want to let players play in the smash
    tournaments and InsaLan one year, we can have two events happening
    concurrently.
    """

    name = models.CharField(
        verbose_name=_("Nom de l'évènement"),
        max_length=40,
        validators=[MinLengthValidator(4)],
        null=False,
    )
    description = models.CharField(
        verbose_name=_("Description de l'évènement"),
        max_length=128,
        default="",
        blank=True,
    )
    year = models.IntegerField(
        verbose_name=_("Année"), null=False, validators=[MinValueValidator(2003)]
    )
    month = models.IntegerField(
        verbose_name=_("Mois"),
        null=False,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    ongoing = models.BooleanField(verbose_name=_("En cours"), default=False)
    logo: models.FileField = ImageField(
        verbose_name=_("Logo"),
        blank=True,
        null=True,
        upload_to="event-icons",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp", "avif"])
        ],
    )
    poster: models.FileField = ImageField(
        verbose_name=_("Affiche"),
        blank=True,
        null=True,
        upload_to="event-posters",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp", "avif"])
        ],
    )
    planning_file = models.FileField(
        verbose_name=_("Fichier ICS du planning"),
        blank=True,
        null=True,
        upload_to="event-planning",
        validators=[FileExtensionValidator(allowed_extensions=["ics"])],
    )

    class Meta:
        """Meta options"""

        verbose_name = _("Évènement")
        verbose_name_plural = _("Évènements")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["year", "month"]),
        ]

    def __str__(self) -> str:
        """Format this Event to a str"""
        return f"{self.name} ({self.year}-{self.month:02d})"

    def get_tournaments_id(self) -> List[int]:
        """Return the list of tournaments identifiers for that Event"""
        return tournament.EventTournament.objects.filter(event=self).values_list("id", flat=True)

    def get_tournaments(self) -> List["EventTournament"]:
        """Return the list of tournaments for that Event"""
        return tournament.EventTournament.objects.filter(event=self)

    @staticmethod
    def get_ongoing_ids() -> List[int]:
        """Return the identifiers of ongoing events"""
        return __class__.objects.filter(ongoing=True).values_list("id", flat=True)
