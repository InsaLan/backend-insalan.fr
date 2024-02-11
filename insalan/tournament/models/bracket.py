from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
import math

from . import match

class BracketType(models.TextChoices):
    """Information about the type of a bracket, single or double elimination"""

    SINGLE = "SINGLE", _("Simple élimination")
    DOUBLE = "DOUBLE", _("Double élimination")

class BracketSet(models.TextChoices):
    """Information on the bracket set, winner or looser"""

    WINNER = "WINNER", _("Gagnant")
    LOOSER = "LOOSER", _("Perdant")

class Bracket(models.Model):
    name = models.CharField(
        max_length=40,
        verbose_name=_("Nom de l'arbre")
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    bracket_type = models.CharField(
        default=BracketType.SINGLE,
        choices=BracketType.choices,
        max_length=10
    )
    team_count = models.IntegerField(
        default=2,
        verbose_name=_("Nombre d'équipes"),
        validators=[MinValueValidator(2)]
    )

    class Meta:
        verbose_name = _("Arbre de tournoi")
        verbose_name_plural = _("Arbres de tournoi")

    def __str__(self):
        return self.name

    def get_depth(self) -> int:
        return math.ceil(math.log2(self.team_count/self.tournament.get_game().get_team_per_match())) + 1

    def get_max_match_count(self) -> int:
        return math.ceil(self.team_count/self.tournament.get_game().get_team_per_match())

class KnockoutMatch(match.Match):
    bracket = models.ForeignKey(
        "Bracket",
        verbose_name=_("Arbre de tournoi"),
        on_delete=models.CASCADE
    )
    bracket_set = models.CharField(
        max_length=10,
        default=BracketSet.WINNER,
        choices=BracketSet.choices,
        verbose_name=_("Type de tableau, gagnant ou perdant")
    )

    class Meta:
        verbose_name = _("Match d'arbre")
        verbose_name_plural = _("Matchs d'arbre")