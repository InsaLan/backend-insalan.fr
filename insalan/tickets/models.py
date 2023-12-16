"""
Module for defining the Ticket model.
"""
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from insalan.user.models import User


class Ticket(models.Model):
    """
    Model representing a ticket.
    """

    class Status(models.TextChoices):
        """
        Enum for the ticket status.
        """
        CANCELLED = "CA", _("Annulé")
        SCANNED = "SC", _("Scanné")
        VALID = "VA", _("Valide")

    class Meta:
        """Meta options"""

        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")

    token: models.UUIDField = models.UUIDField(
        verbose_name=_("UUID"), unique=True, default=uuid.uuid4, editable=False
    )
    user: models.ForeignKey = models.ForeignKey(
        User, verbose_name=_("Utilisateur⋅ice"), on_delete=models.CASCADE
    )
    status: models.CharField = models.CharField(
        verbose_name=_("Statut"),
        max_length=2,
        choices=Status.choices,
        default=Status.VALID,
    )
    tournament = models.ForeignKey(
        "tournament.Tournament", verbose_name=_("Tournoi"),
        on_delete=models.CASCADE, blank=False, null=False
    )
