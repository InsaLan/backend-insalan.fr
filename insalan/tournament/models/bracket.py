from django.db import models
from django.utils.translation import gettext_lazy as _

class BracketType(models.TextChoices):
    """Information about the type of a bracket, single or double elimination"""

    SINGLE = "SINGLE", _("Simple élimination")
    DOUBLE = "DOUBLE", _("Double élimination")

class Bracket(models.Model):
    name = models.CharField(
        verbose_name=_("Nom de l'arbre")
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi")
    )
    bracket_type = models.CharField(
        default=BracketType.SINGLE,
        choices=BracketType.choices
    )

    class Meta:
        verbose_name = _("Arbre de tournoi")
        verbose_name_plural = _("Arbres de tournoi")