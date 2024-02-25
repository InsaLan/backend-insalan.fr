from typing import List, Dict, Tuple

from django.db import models
from django.utils.translation import gettext_lazy as _

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
    round_count = models.IntegerField(
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
        teams = Seeding.objects.filter(group=self).values_list("team", flat=True)
        return team.Team.objects.filter(pk__in=teams)

    def get_teams_id(self) -> List[int]:
        return self.get_teams().values_list("id", flat=True)
    
    def get_teams_seeding(self) -> List[Tuple["Team",int]]:
        return [(seeding.team,seeding.seeding) for seeding in Seeding.objects.filter(group=self)]
    
    def get_sorted_teams(self) -> List["Team"]:
        teams = self.get_teams_seeding()
        teams.sort(key=lambda e: e[1])
        return [team[0] for team in teams]

    def get_round_count(self) -> int:
        return self.round_count
    
    def get_leaderboard(self) -> Dict["Team",int]:
        leaderboard = {}

        for team in self.get_teams():
            group_matchs = GroupMatch.objects.filter(teams=team,group=self)
            score = sum(match.Score.objects.filter(team=team,match__in=group_matchs).values_list("score",flat=True))
            leaderboard[team] = score

        return leaderboard

    def get_scores(self) -> Dict[int,int]:
        leaderboard = self.get_leaderboard()
        
        return {team.id : score for team, score in leaderboard.items()}

    def get_matchs(self) -> List["GroupMatch"]:
        return GroupMatch.objects.filter(group=self)


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

    def get_tournament(self):
        return self.group.tournament

# class GroupMatchScore(models.Model):
#     score = models.IntegerField()
#     match = models.ForeignKey(
#         GroupMatch,
#         on_delete=models.CASCADE
#     )
#     team = models.ForeignKey(
#         "Team",
#         on_delete=models.CASCADE
#     )