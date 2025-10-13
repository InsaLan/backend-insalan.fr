from typing import List, Tuple

from django.db import models
from django.utils.translation import gettext_lazy as _
from . import match

class SwissRound(models.Model):
    tournament = models.ForeignKey(
        "BaseTournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    min_score = models.IntegerField(
        verbose_name=_("Score minimal pour la qualification")
    )

    class Meta:
        verbose_name = _("Ronde Suisse")
        indexes = [
            models.Index(fields=["tournament"])
        ]

    def __str__(self) -> str:
        return "Ronde Suisse" + f"({self.tournament})"

    def get_teams(self) -> List["Team"]:
        return SwissSeeding.objects.filter(swiss=self).values_list("team", flat=True)

    def get_teams_id(self) -> List[int]:
        return self.get_teams().values_list("id", flat=True)

    def get_teams_seeding(self) -> List[Tuple["Team",int]]:
        return [(seeding.team, seeding.seeding)
                for seeding in SwissSeeding.objects.filter(swiss=self)]

    def get_sorted_teams(self) -> List[int]:
        teams = self.get_teams_seeding()

        non_seeded_teams = []
        seeded_teams = []

        for (team, seed) in teams:
            if seed == 0:
                non_seeded_teams.append((team.id,seed))
            else:
                seeded_teams.append((team.id,seed))

        seeded_teams.sort(key=lambda e: e[1])
        return [team for (team, _) in seeded_teams + non_seeded_teams]

    def get_matchs(self) -> List["SwissMatch"]:
        return SwissMatch.objects.filter(swiss=self)

class SwissSeeding(models.Model):
    swiss = models.ForeignKey(
        SwissRound,
        on_delete=models.CASCADE
    )
    team = models.OneToOneField(
        "Team",
        on_delete=models.CASCADE
    )
    seeding = models.PositiveIntegerField(
        default=0
    )

class SwissMatch(match.Match):
    swiss = models.ForeignKey(
        SwissRound,
        on_delete=models.CASCADE
    )

    score_group = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        verbose_name = _("Match de ronde suisse")
        verbose_name_plural = _("Matchs de ronde suisse")

    def get_tournament(self):
        return self.swiss.tournament
