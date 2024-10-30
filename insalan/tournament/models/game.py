from django.db import models
from django.core.validators import (
    MinValueValidator,
    MinLengthValidator,
)
from django.utils.translation import gettext_lazy as _

from .name_validator import get_choices, get_validator

class Game(models.Model):
    """
    A Game is the representation of a Game that is being played at InsaLan
    """

    class Meta:
        """Meta options"""

        verbose_name = _("Jeu")
        verbose_name_plural = _("Jeux")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["short_name"]),
        ]

    name = models.CharField(
        verbose_name=_("Nom du jeu"),
        validators=[MinLengthValidator(2)],
        max_length=40,
        null=False,
    )
    short_name = models.CharField(
        verbose_name=_("Nom raccourci du jeu"),
        validators=[MinLengthValidator(2)],
        max_length=10,
        null=False,
        blank=False,
    )
    players_per_team = models.IntegerField(
        verbose_name=_("Nombre de joueurs par équipe"),
        null=False,
        validators=[MinValueValidator(1)],
        default=1
    )
    substitute_players_per_team = models.IntegerField(
        verbose_name=_("Nombre de remplaçants par équipe"),
        null=False,
        validators=[MinValueValidator(0)],
        default=0
    )
    team_per_match = models.IntegerField(
        verbose_name=_("Nombre maximum d'équipes par match"),
        validators=[MinValueValidator(2)],
        default=2
    )
    validators = models.CharField(
        verbose_name=_("Validateurs de pseudo"),
        max_length=42,
        null=False,
        blank=False,
        default=get_choices()[0][0],
        choices=get_choices(),
    )

    def __str__(self) -> str:
        """Format this Game to a str"""
        return f"{self.name} ({self.short_name})"

    def get_name(self) -> str:
        """Return the name of the game"""
        return self.name

    def get_short_name(self) -> str:
        """Return the short name of the game"""
        return self.short_name

    def get_players_per_team(self) -> int:
        """Return the number of players per team"""
        return self.players_per_team

    def get_substitute_players_per_team(self) -> int:
        """Return the number of substitute players per team"""
        return self.substitute_players_per_team

    def get_team_per_match(self) -> int:
        """Return the maximum number of teams in a match"""
        return self.team_per_match

    def get_name_validator(self):
        """Return the validators of the game"""
        return get_validator(self.validators)
