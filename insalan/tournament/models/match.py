from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField

class MatchStatus(models.TextChoices):
    """Information about the status of a match"""

    SCHEDULED = "SCHEDULED", _("Prévu")
    ONGOING = "ONGOING", _("En cours")
    COMPLETED = "COMPLETED", _("Terminé")

class BracketSet(models.TextChoices):
    """Information on the bracket set, winner or looser"""

    WINNER = "WINNER"
    LOOSER = "LOOSER"

class BestofType(models.TextChoices):
    """Best of type for a match"""

    BO1 = "BO1", _("Série de 1")
    BO3 = "BO3", _("Série de 3")
    BO5 = "BO5", _("Série de 5")
    BO7 = "BO7", _("Série de 7")

class Match(models.Model):
    teams = models.ManyToManyField(
        "Team",
        verbose_name=_("Liste des équipes")
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
        choices=MatchStatus.choices
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
        default=list
    )

    class Meta:
        abstract = True


class GroupMatch(Match):
    group = models.ForeignKey(
        "Group",
        verbose_name=_("Poule"),
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Match de poule")
        verbose_name_plural = _("Matchs de poule")
    

class KnockoutMatch(Match):
    bracket = models.ForeignKey(
        "Bracket",
        verbose_name=_("Arbre de tournoi"),
        on_delete=models.CASCADE
    )
    bracket_set = models.CharField(
        max_length=10,
        default=BracketSet.WINNER,
        choices=BracketSet.choices,
        verbose_name=_("Type de tableau, gagnant ou perdant")
    )
    # winner_next = models.ForeignKey(
    #     KnockoutMatch,
    #     verbose_name=_("Match suivant pour le/les gagnants"),
    #     null=True
    # )
    # looser_next = models.ForeignKey(
    #     KnockoutMatch,
    #     verbose_name=_("Match suivant pour le/les perdants"),
    #     null=True
    # )

    class Meta:
        verbose_name = _("Match dans un arbre")
        verbose_name_plural = _("Matchs dans un arbre")

class Score(models.Model):
    score = models.IntegerField(
        verbose_name=_("Score")
    )
    team = models.ForeignKey(
        "Team",
        verbose_name=_("Équipe"),
        on_delete=models.CASCADE
    )
    group_match = models.ForeignKey(
        "Group",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Match de poule lié à ce score")
    )
    bracket_match = models.ForeignKey(
        "Bracket",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Match dans un arbre lié à ce score")
    )