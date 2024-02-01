from django.db import models
from django.utils.translation import gettext_lazy as _

from . import match

class BracketType(models.TextChoices):
    """Information about the type of a bracket, single or double elimination"""

    SINGLE = "SINGLE", _("Simple élimination")
    DOUBLE = "DOUBLE", _("Double élimination")

class BracketSet(models.TextChoices):
    """Information on the bracket set, winner or looser"""

    WINNER = "WINNER"
    LOOSER = "LOOSER"

class Bracket(models.Model):
    name = models.CharField(
        max_length=40,
        verbose_name=_("Nom de l'arbre")
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    bracket_type = models.CharField(
        default=BracketType.SINGLE,
        choices=BracketType.choices,
        max_length=10
    )
    depth = models.IntegerField(
        default=1
    )

    class Meta:
        verbose_name = _("Arbre de tournoi")
        verbose_name_plural = _("Arbres de tournoi")

    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args,**kwargs)
    #     self.cache_depth = self.depth

    # def save(self, *args, **kwargs):
    #     """
    #     Override default save method to automatically create matchs when the Bracket is created or modified.
    #     """
    #     need_save = False

    #     # if no match exist, then create them
    #     if len(KnockoutMatch.objects.filter(bracket=self)) == 0:
    #         for round_n in range(1,depth+1):
    #             for match_id in range(1,2**(round_n-1)+1):
    #                 KnockoutMatch.objects.create(round_number=round_n,index_in_round=match_id,bracket=self)
    #         if self.bracket_type == BracketType.DOUBLE:
    #             for round_n in range(1,2*depth-1):
    #                 for match_id in range(1,2**((round_n-1)//2)+1):
    #                     KnockoutMatch.objects.create(round_number=round_n,index_in_round=match_id,bracket=self,bracket_set=BracketSet.LOOSER)
    #             KnockoutMatch.objects.create(round_number=0,index_in_round=1,bracket=self)
    #         need_save = True
    #     # if the depth has changed and no game is started, create or delete matchs
    #     elif self.cache_depth < self.depth and all([match.MatchStatus.SCHEDULED == m.status for m in KnockoutMatch.objects.filter(bracket=self)]):

    #         pass
    #     elif self.cache_depth > self.depth and all([match.MatchStatus.SCHEDULED == m.status for m in KnockoutMatch.objects.filter(bracket=self)]):
    #         # 
    #         need_save = True

    #     if need_save:
    #         super().save()

class KnockoutMatch(match.Match):
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

    class Meta:
        verbose_name = _("Match dans un arbre")
        verbose_name_plural = _("Matchs dans un arbre")