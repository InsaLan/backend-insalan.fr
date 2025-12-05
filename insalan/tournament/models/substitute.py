from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

from django.utils.translation import gettext_lazy as _

from insalan.tickets.models import Ticket
from insalan.user.models import User

from . import validators, tournament
from .payement_status import PaymentStatus

if TYPE_CHECKING:
    from .team import Team


class Substitute(models.Model):
    """
    A Substitute is someone that can replace a player in a team.
    """

    user = models.ForeignKey(
        User,
        verbose_name=_("Utilisateur⋅rice"),
        on_delete=models.CASCADE,
    )
    team = models.ForeignKey(
        "Team",
        verbose_name=_("Équipe"),
        on_delete=models.CASCADE,
    )
    payment_status = models.CharField(
        verbose_name=_("Statut du paiement"),
        max_length=10,
        blank=True,
        default=PaymentStatus.NOT_PAID,
        choices=PaymentStatus.choices,
        null=False,
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        verbose_name=_("Ticket"),
        null=True,
        blank=True,
        default=None,
    )
    name_in_game = models.CharField(
        max_length=42,
        validators=[MinLengthValidator(1)],
        null=False,
        blank=False,
        verbose_name=_("Pseudo en jeu"),
    )
    validator_data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        verbose_name=_("Données additionnelles"),
        help_text=_("Données additionnelles fournies par le validateur de pseudo en jeu."),
    )
    ecological_data_sent = models.BooleanField(
        verbose_name=_("Données écologique envoyées"),
        null=False,
        blank=False,
        default=False,
    )

    class Meta:
        """Meta Options"""

        verbose_name = _("Inscription d'un⋅e remplaçant⋅e")
        verbose_name_plural = _("Inscriptions de remplaçant⋅e⋅s")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "team"], name="not_twice_same_substitute"
            )
        ]
        indexes = [
            models.Index(fields=["team"]),
            models.Index(fields=["user"]),
            models.Index(fields=["payment_status"]),
        ]

    def __str__(self) -> str:
        """Format this substitute registration as a str"""
        return f"(Substitute) {self.user.username} for {self.team}"

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self) -> Team:
        """Return the Team object of the current team"""
        return self.team

    def get_name_in_game(self) -> str:
        """Return the name_in_game of the player"""
        return self.name_in_game

    def clean(self) -> None:
        """
        Assert that the user associated with the provided substitute does not already
        exist in any team of any tournament of the event
        """
        user = self.user
        tourney = self.team.get_tournament()  # pylint: disable=no-member
        if isinstance(tourney, tournament.EventTournament):
            event = tourney.get_event()
            if not validators.unique_event_registration_validator(user,event, substitute=self.id):
                raise ValidationError(
                    _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
                )
            if not validators.tournament_announced(tourney):
                raise ValidationError(
                    _("Tournoi non annoncé")
                )
        if validators.max_substitue_per_team_reached(self.team, exclude=self.id):
            raise ValidationError(
                _("Nombre maximum de remplaçants déjà atteint")
            )
        # Validate the name in game and save the data
        info = validators.valid_name(tourney.get_game(), self.name_in_game)
        if info is None:
            raise ValidationError(
                _("Le pseudo en jeu n'est pas valide")
            )
        self.validator_data.update(info)

    def update_name_in_game(self) -> None:
        """
        Update and validate the name_in_game of the player
        """
        data = self.validator_data
        validator = self.team.tournament.game.get_name_validator()
        if validator is not None:
            new_name_in_game = validator.update_name(self.name_in_game, data)

            if new_name_in_game != self.name_in_game:
                self.name_in_game = new_name_in_game
                self.save()
