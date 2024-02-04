from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import List, Tuple
from . import match

class SwissRound(models.Model):
	tournament = models.ForeignKey(
		"Tournament",
		verbose_name=_("Tournoi"),
		on_delete=models.CASCADE
	)
	min_score = models.IntegerField(
		verbose_name=_("Score minimal pour la qualification")
	)

	class Meta:
		verbose_name = _("Ronde Suisse")
	
	def __str__(self) -> str:
		return "Ronde Suisse" + f"({self.tournament}, {self.tournament.event})"

	def get_teams(self) -> List["Team"]:
		return [seeding.team for seeding in SwissSeeding.objects.filter(swiss=self)]

	def get_teams_seeding(self) -> List[Tuple["Team",int]]:
		return [(seeding.team,seeding.seeding) for seeding in SwissSeeding.objects.filter(swiss=self)]

	def get_sorted_teams(self) -> List[Tuple["Team",int]]:
		teams = self.get_teams_seeding()
		if any([team[1] == None for team in teams]):
			return [team[0] for team in teams]

		teams.sort(key=lambda e: e[1])
		return [team[0] for team in teams]

class SwissSeeding(models.Model):
	swiss = models.ForeignKey(
		SwissRound,
		on_delete=models.CASCADE
	)
	team = models.OneToOneField(
		"Team",
		on_delete=models.CASCADE
	)
	seeding = models.IntegerField(
		null=True,
		blank=True
	)

class SwissMatch(match.Match):
	swiss = models.ForeignKey(
		SwissRound,
		on_delete=models.CASCADE
	)

	class Meta:
		verbose_name = _("Match de ronde suisse")
		verbose_name_plural = _("Matchs de ronde suisse")