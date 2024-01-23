from django.db import models
from django.utils.translation import gettext_lazy as _

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
        "Liste des équipes",
        verbose_name=_("Liste des équipes")
    )
    round_number = models.IntegerField(
        verbose_name=_("Numéro du round")
    )
    index_in_round = models.IntegerField(
        verbose_name=_("Indexe du match dans un round")
    )
    status = models.CharField(
        default=MatchStatus.SCHEDULED,
        choices=MatchStatus.choices
    )
    bo_type = models.CharField(
        default=BestofType.BO1,
        choices=BestofType.choices,
        verbose_name=_("Type de série")
    )
    times = models.ArrayField(
        verbose_name=_("Liste des durées des parties du match")
    )

    class Meta:
        abstract = True


class GroupMatch(Match):
    group = models.ForeignKey(
        "Group",
        verbose_name=_("Poule")
    )
    

class KnockoutMatch(Match):
    bracket = models.ForeignKey(
        "Bracket",
        verbose_name=_("Arbre de tournoi"),
        null=False,
        blank=False
    )
    bracket_set = models.CharField(
        default=BracketSet.UPPER,
        choices=BracketSet.choices
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

class Score(models.Model):
    score = models.IntegerField(
        verbose_name=_("Score")
    )
    team = models.ForeignKey(
        "Team",
        verbose_name=_("Équipe")
    )
    group_match = models.ForeignKey(
        "Group"
    )
    bracket_match = models.ForeignKey(
        "Bracket"
    )