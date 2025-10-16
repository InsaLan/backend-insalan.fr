from typing import Union

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _

from insalan.tickets.models import Ticket
from insalan.user.models import User

from .payement_status import PaymentStatus
from . import validators, group, bracket, swiss, match, tournament

class Player(models.Model):
    """
    A Player at InsaLan is simply anyone who is registered to participate in a
    tournamenent, whichever it might be.
    """

    class Meta:
        """Meta options"""

        verbose_name = _("Inscription d'un⋅e joueur⋅euse")
        verbose_name_plural = _("Inscription de joueur⋅euses")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["team"]),
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Utilisateur⋅ice"),
    )
    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        verbose_name=_("Équipe")
    )
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=PaymentStatus.NOT_PAID,
        choices=PaymentStatus.choices,
        null=False,
        verbose_name=_("Statut du paiement"),
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

    def __str__(self) -> str:
        """Format this player registration to a str"""
        return f"{self.user.username} for {self.team}"

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self) -> "Team":
        """Return the Team object of the current team"""
        return self.team

    def get_name_in_game(self) -> str:
        """Return the name_in_game of the player"""
        return self.name_in_game

    def get_ongoing_match(self) -> Union["GroupMatch", "KnockoutMatch", "SwissMatch"]:
        return list(group.GroupMatch.objects.filter(
            teams=self.team,
            status=match.MatchStatus.ONGOING,
        )) + list(bracket.KnockoutMatch.objects.filter(
            teams=self.team,
            status=match.MatchStatus.ONGOING,
        )) + list(swiss.SwissMatch.objects.filter(
            teams=self.team,
            status=match.MatchStatus.ONGOING
        ))

    def clean(self):
        """
        Assert that the user associated with the provided player does not already
        exist in any team of any tournament of the event
        """
        user = self.user
        tourney = self.team.get_tournament()  # pylint: disable=no-member
        if isinstance(tourney, tournament.EventTournament):
            event = tourney.get_event()
            if not validators.unique_event_registration_validator(user, event, player=self.id):
                raise ValidationError(
                    _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
                )
            if not validators.tournament_announced(tourney):
                raise ValidationError(
                    _("Tournoi non annoncé")
                )
        if validators.max_players_per_team_reached(self.team, exclude=self.id):
            raise ValidationError(
                _("Équipe déjà remplie")
            )

        # Validate the name in game
        if not validators.valid_name(tourney.get_game(), self.name_in_game):
            raise ValidationError(
                _("Le pseudo en jeu n'est pas valide")
            )

    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        self.team.refresh_validation()  # pylint: disable=no-member

    def delete(self,*args,**kwargs):
        if self.team.captain == self:
            self.team.captain = None
        super().delete(*args,**kwargs)
        self.team.refresh_validation()  # pylint: disable=no-member
