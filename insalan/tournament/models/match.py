from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from typing import List, Dict
import math
from insalan.user.models import User

class MatchStatus(models.TextChoices):
    """Information about the status of a match"""

    SCHEDULED = "SCHEDULED", _("Prévu")
    ONGOING = "ONGOING", _("En cours")
    COMPLETED = "COMPLETED", _("Terminé")

class BestofType(models.IntegerChoices):
    """Best of type for a match"""

    BO1 = 1, _("Série de 1")
    BO3 = 3, _("Série de 3")
    BO5 = 5, _("Série de 5")
    BO7 = 7, _("Série de 7")
    RANKING = 0, _("Classement")

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
    bo_type = models.IntegerField(
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
    
    def get_team_count(self) -> int:
        return len(self.get_teams())

    def get_teams(self) -> List["Team"]:
        return self.teams.all()

    def get_teams_id(self) -> List[int]:
        return self.teams.all().values_list("id", flat=True)

    def get_max_score(self) -> int:
        """Return the cumulated maximum score"""
        if self.bo_type == BestofType.RANKING:
            return (self.get_team_count()*(self.get_team_count()+1))//2

        return self.bo_type

    def get_winning_score(self) -> int:
        """Minimum score for a team to be considered a winner"""
        if self.bo_type == BestofType.RANKING:
            return math.ceil(self.get_team_count()/2)
        
        return math.ceil(self.get_max_score()/2)

    def is_user_in_match(self, user: User) -> bool:
        """Test if a user is a player in a team of the match"""
        for team in self.get_teams():
            for player in team.get_players():
                if player.as_user() == user:
                    return True
        
        return False
        # return any([user == player_user for player_user in [player.as_user() for player in [team.get_players() for team in self.get_teams()]]])

    def get_scores(self) -> Dict[int,int]:
        scores = {}

        for team in self.teams.all():
            score = Score.objects.get(team=team,match=self).score
            scores[team.id] = score

        return scores

    def get_Scores(self) -> List["Score"]:
        return Score.objects.filter(team__in=self.get_teams(),match=self)

    def get_winners_loosers(self) -> List[List["Team"]]:
        winners = []
        loosers = []
        scores = self.get_scores()

        for team in self.get_teams():
            if scores[team.id] >= self.get_winning_score():
                winners.append(team)
            else:
                loosers.append(team)

        return winners,loosers

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