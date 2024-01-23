from django.db import models
from django.utils.translation import gettext_lazy as _

class Group(models.Model):
    name = models.CharField(
        verbose_name=_("Nom de la poule")
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Poule")
        verbose_name_plural = _("Poules")

    