from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from typing import List

from . import team

class Group(models.Model):
    name = models.CharField(
        max_length=40,
        verbose_name=_("Nom de la poule")
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    nb_round = models.IntegerField(
        verbose_name=_("Nombre de rondes"),
        default=1
    )

    class Meta:
        verbose_name = _("Poule")
        verbose_name_plural = _("Poules")
        constraints = [
            models.UniqueConstraint(
                fields=["name","tournament"],
                name="unique_group_name_in_same_tournament"
            )
        ]

    def get_name(self) -> str:
        return self.name

    def get_tournament(self) -> "Tournament":
        return self.tournament

    def get_teams(self) -> List["Team"]:
        return team.Team.objects.filter(group=self)

    def get_teams_id(self) -> List[int]:
        return self.get_teams().values_list("id", flat=True)

    def get_nb_round(self) -> int:
        return self.nb_round


class Leaderboard(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE
    )
    score = models.IntegerField(
        default=0
    )