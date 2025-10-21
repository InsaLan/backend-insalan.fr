from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.validators import (
    FileExtensionValidator,
    MinLengthValidator,
)
from django.forms import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from insalan.components.image_field import ImageField

from .tournament import EventTournament

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from django_stubs_ext import ValuesQuerySet


class Event(models.Model):
    """
    An Event is any single event that is characterized by the following:
     - A single player can only register for a single tournament per event

    This means, for example, that if we want to let players play in the smash
    tournaments and InsaLan one year, we can have two events happening
    concurrently.
    """

    eventtournament_set: RelatedManager[EventTournament]

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
    date_start = models.DateField(
        verbose_name=_("Date de début"),
        null=True,
        blank=True
    )
    date_end = models.DateField(
        verbose_name=_("Date de fin"),
        null=True,
        blank=True
    )
    ongoing = models.BooleanField(
        verbose_name=_("En cours"),
        help_text=_("Détermine si l'évènement est affiché sur la page principale"),
        default=True
    )
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
            models.Index(fields=["date_start"]),
        ]
    
    def clean(self):
        super().clean()
        self.clean_date_end()
        if self.ongoing:
            ongoing_events = Event.objects.filter(ongoing=True)
            if self.pk:
                ongoing_events = ongoing_events.exclude(pk=self.pk)
            if ongoing_events.exists():
                raise ValidationError(_("Un autre évènement est déjà en cours. Il ne peut y en avoir qu'un seul."))

    def clean_date_end(self):
        if self.date_end and self.date_start and self.date_end < self.date_start:
            raise ValidationError(_("La date de fin ne peut pas être avant la date de début."))

    def __str__(self) -> str:
        """Format this Event to a str"""
        if self.date_start:
            return f"{self.name} ({self.date_start.year}-{self.date_start.month:02d})"
        return self.name

    def get_tournaments_id(self) -> ValuesQuerySet[EventTournament, int]:
        """Return the list of tournaments identifiers for that Event"""
        return EventTournament.objects.filter(  # type: ignore[no-any-return]
            event=self,
        ).values_list("id", flat=True)

    def get_tournaments(self) -> QuerySet[EventTournament]:
        """Return the list of tournaments for that Event"""
        return EventTournament.objects.filter(event=self)

    @staticmethod
    def get_ongoing_ids() -> ValuesQuerySet[Event, int]:
        """Return the identifiers of ongoing events"""
        return Event.objects.filter(ongoing=True).values_list("id", flat=True)
