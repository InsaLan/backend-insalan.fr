from django.db import models
from django.utils.translation import gettext_lazy as _

class Stage(models.Model):
    tournament = models.ForeignKey(
        "BaseTournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name=_("Nom de la phase"),
        max_length=256,
        blank=True
    )
    index = models.PositiveIntegerField(
        verbose_name=_("Index de la phase"),
        default=1,
    )

    class Meta:
        verbose_name = _("Phase d'un tournoi")
        verbose_name_plural = _("Phases d'un tournoi")
        ordering = ["index"]
        indexes = [
            models.Index(fields=["tournament"])
        ]

    def __str__(self) -> str:
        return self.name + " (" + str(self.tournament) + ")"
