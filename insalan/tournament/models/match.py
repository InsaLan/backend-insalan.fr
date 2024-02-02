from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from typing import List

class MatchStatus(models.TextChoices):
    """Information about the status of a match"""

    SCHEDULED = "SCHEDULED", _("Prévu")
    ONGOING = "ONGOING", _("En cours")
    COMPLETED = "COMPLETED", _("Terminé")

class BestofType(models.TextChoices):
    """Best of type for a match"""

    BO1 = "BO1", _("Série de 1")
    BO3 = "BO3", _("Série de 3")
    BO5 = "BO5", _("Série de 5")
    BO7 = "BO7", _("Série de 7")

class Match(models.Model):
    teams = models.ManyToManyField(
        "Team",
        verbose_name=_("Liste des équipes"),
        through="Score"
    )
    round_number = models.IntegerField(
        verbose_name=_("Numéro du round")
    )
    index_in_round = models.IntegerField(
        verbose_name=_("Indexe du match dans un round")
    )
    status = models.CharField(
        max_length=10,
        default=MatchStatus.SCHEDULED,
        choices=MatchStatus.choices,
        verbose_name = _("Status du match")
    )
    bo_type = models.CharField(
        max_length=5,
        default=BestofType.BO1,
        choices=BestofType.choices,
        verbose_name=_("Type de série")
    )
    times = ArrayField(
        models.IntegerField(
            default=0
        ),
        verbose_name=_("Liste des durées des parties du match"),
        default=list,
        blank=True
    )

    # class Meta:
    #     abstract = True

    def get_teams(self) -> List["Team"]:
        return self.teams.all()

class Score(models.Model):
    team = models.ForeignKey(
        "Team",
        verbose_name=_("Équipe"),
        on_delete=models.CASCADE
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        verbose_name=_("Match")
    )
    score = models.IntegerField(
        verbose_name=_("Score"),
        default=0
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team","match"],
                name="no_duplicate_team_in_a_match"
            )
        ]
    # group_match = models.ForeignKey(
    #     "Group",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     verbose_name=_("Match de poule lié à ce score")
    # )
    # bracket_match = models.ForeignKey(
    #     "Bracket",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     verbose_name=_("Match dans un arbre lié à ce score")
    # )