from __future__ import annotations

from math import ceil
from operator import itemgetter
from typing import TYPE_CHECKING

from django.db import models
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from . import match
from . import team
from . import tournament

if TYPE_CHECKING:
    from django_stubs_ext import ValuesQuerySet

    from .team import Team
    from .tournament import BaseTournament


class Group(models.Model):
    name = models.CharField(
        max_length=40,
        verbose_name=_("Nom de la poule")
    )
    tournament = models.ForeignKey(
        "BaseTournament",
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
        if (isinstance(self.tournament, tournament.EventTournament) and
            self.tournament.event is not None):  # pylint: disable=no-member
            # pylint: disable-next=no-member
            return f"{self.name} ({self.tournament.name}, {self.tournament.event})"
        return f"{self.name} ({self.tournament.name})"

    def get_name(self) -> str:
        return self.name

    def get_tournament(self) -> BaseTournament:
        return self.tournament

    def get_teams(self) -> QuerySet[Team]:
        return team.Team.objects.filter(pk__in=self.get_teams_id())

    def get_teams_id(self) -> ValuesQuerySet[Seeding, int]:
        return Seeding.objects.filter(group=self).values_list("team", flat=True)

    def get_teams_seeding_by_id(self) -> dict[int, int]:
        return {seeding.team.id: seeding.seeding for seeding in Seeding.objects.filter(group=self)}

    def get_teams_seeding(self) -> dict[Team, int]:
        return {seeding.team: seeding.seeding for seeding in Seeding.objects.filter(group=self)}

    def get_sorted_teams(self) -> list[int]:
        teams = self.get_teams_seeding()

        non_seeded_teams = []
        seeded_teams = []

        for team_obj, seed in teams.items():
            if seed == 0:
                non_seeded_teams.append((team_obj.id, seed))
            else:
                seeded_teams.append((team_obj.id, seed))

        seeded_teams.sort(key=lambda e: e[1])
        return [team for (team, _) in seeded_teams + non_seeded_teams]

    def get_round_count(self) -> int:
        team_per_match = self.tournament.game.team_per_match  # pylint: disable=no-member
        return ceil(len(self.get_teams_id()) / team_per_match) * team_per_match - 1

    def get_leaderboard(self) -> dict[int, int]:
        leaderboard = {}

        for team_id in self.get_teams_id():
            group_matchs = GroupMatch.objects.filter(teams=team_id, group=self)
            score = sum(match.Score.objects.filter(
                team=team_id,
                match__in=group_matchs,
            ).values_list("score",flat=True))
            leaderboard[team_id] = score

        return dict(sorted(leaderboard.items(), key=itemgetter(1), reverse=True))

    def get_matchs(self) -> QuerySet[GroupMatch]:
        return GroupMatch.objects.filter(group=self)

    def get_tiebreaks(self) -> dict[int,int]:
        return {tiebreak.team.id: tiebreak.score
                for tiebreak in GroupTiebreakScore.objects.filter(group=self)}


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

    def get_tournament(self) -> BaseTournament:
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
