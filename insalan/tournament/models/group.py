from typing import List, Dict
from operator import itemgetter

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
    round_count = models.PositiveIntegerField(
        verbose_name=_("Nombre de rounds"),
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
        indexes = [
            models.Index(fields=["tournament"])
        ]
        ordering = ["tournament","name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.tournament.name}, {self.tournament.event})"

    def get_name(self) -> str:
        return self.name

    def get_tournament(self) -> "Tournament":
        return self.tournament

    def get_teams(self) -> List["Team"]:
        return team.Team.objects.filter(pk__in=self.get_teams_id())

    def get_teams_id(self) -> List[int]:
        return Seeding.objects.filter(group=self).values_list("team", flat=True)

    def get_teams_seeding_by_id(self) -> Dict[int,int]:
        return {seeding.team.id: seeding.seeding for seeding in Seeding.objects.filter(group=self)}

    def get_teams_seeding(self) -> Dict["Team",int]:
        return {seeding.team: seeding.seeding for seeding in Seeding.objects.filter(group=self)}
    
    def get_sorted_teams(self) -> List["Team"]:
        teams = sorted(self.get_teams_seeding().items(), key=itemgetter(1))
        return [team[0] for team in teams]

    def get_round_count(self) -> int:
        return len(self.get_teams_id()) - 1

    def get_leaderboard(self) -> Dict[int,int]:
        leaderboard = {}

        for team in self.get_teams_id():
            group_matchs = GroupMatch.objects.filter(teams=team,group=self)
            score = sum(match.Score.objects.filter(team=team,match__in=group_matchs).values_list("score",flat=True))
            leaderboard[team] = score

        return dict(sorted(leaderboard.items(), key=itemgetter(1), reverse=True))

    def get_matchs(self) -> List["GroupMatch"]:
        return GroupMatch.objects.filter(group=self)

    def get_tiebreaks(self) -> Dict[int,int]:
        return {tiebreak.team.id: tiebreak.score for tiebreak in GroupTiebreakScore.objects.filter(group=self)}


class Seeding(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    team = models.OneToOneField(
        "Team",
        on_delete=models.CASCADE,
    )
    seeding = models.PositiveIntegerField(
        default=0
    )


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

class GroupTiebreakScore(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
    )
    team = models.OneToOneField(
        "Team",
        on_delete=models.CASCADE,
    )
    score = models.IntegerField(
        default=0,
        verbose_name=_("Score de tiebreak")
    )

    class Meta:
        verbose_name = _("Score de tiebreak d'une équipe dans une poule")
