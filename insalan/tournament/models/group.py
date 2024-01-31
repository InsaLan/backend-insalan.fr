from pyexpat import model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from typing import List, Tuple

from . import team
from . import match

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
        verbose_name=_("Nombre de rounds"),
        default=1
    )
    # teams = models.ManyToManyField(
    #     "Team",
    #     through="Seeding"
    # )

    class Meta:
        verbose_name = _("Poule")
        verbose_name_plural = _("Poules")
        constraints = [
            models.UniqueConstraint(
                fields=["name","tournament"],
                name="unique_group_name_in_same_tournament"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tournament.name}, {self.tournament.event})"

    def get_name(self) -> str:
        return self.name

    def get_tournament(self) -> "Tournament":
        return self.tournament

    def get_teams(self) -> List["Team"]:
        return [seeding.team for seeding in Seeding.objects.filter(group=self)]
        # return team.Team.objects.filter(group=self)
    
    def get_teams_seeding(self) -> List[Tuple["Team",int]]:
        return [(seeding.team,seeding.seeding) for seeding in Seeding.objects.filter(group=self)]
    
    def get_sorted_teams(self) -> List["Team"]:
        teams = self.get_teams_seeding()
        teams.sort(key=lambda e: e[1])
        return [team[0] for team in teams]

    def get_teams_id(self) -> List[int]:
        return self.get_teams().values_list("id", flat=True)

    def get_nb_rounds(self) -> int:
        return self.nb_round
    
    def get_leaderboard(self) -> List[Tuple["Team",int]]:
        leaderboard = []

        for team in self.get_teams():
            score = sum(GroupMatchScore.objects.filter(team=team,match__group=self).values_list("score",flat=True))
            leaderboard.append(tuple([team,score]))

        return leaderboard


class Seeding(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    team = models.OneToOneField(
        "Team",
        on_delete=models.CASCADE,
    )
    seeding = models.IntegerField()


class GroupMatch(match.Match):
    group = models.ForeignKey(
        Group,
        verbose_name=_("Poule"),
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Match de poule")
        verbose_name_plural = _("Matchs de poule")

class GroupMatchScore(models.Model):
    score = models.IntegerField()
    match = models.ForeignKey(
        GroupMatch,
        on_delete=models.CASCADE
    )
    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE
    )