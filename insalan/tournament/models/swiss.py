from django.db import models
from django.utils.translation import gettext_lazy as _

class SwissRound(models.Model):
	tournament = models.ForeignKey(
		"Tournament",
		verbose_name=_("Tournoi"),
		on_delete=models.CASCADE
	)
	nb_rounds = models.IntegerField(
		verbose_name=_("Nombre de manches"),
		default=1
	)

	class Meta:
		verbose_name = _("Ronde Suisse")
	
	def __str__(self) -> str:
		return "Ronde Suisse" + f"({self.tournament}, {self.tournament.event})"