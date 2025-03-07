from typing import List, Optional, Union
from math import ceil
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

from django.utils.translation import gettext_lazy as _

from . import player
from . import manager
from . import substitute
from . import group, bracket, swiss

from . import validators
from . import payement_status as ps

class Team(models.Model):
    """
    A Team consists in a group of one or more players, potentially helmed by a
    `Manager`.
    """

    tournament = models.ForeignKey(
        "Tournament",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name=_("Tournoi"),
        related_name="teams"
    )
    name = models.CharField(
        max_length=42,
        validators=[MinLengthValidator(3)],
        null=False,
        blank=False,
        verbose_name=_("Nom d'équipe"),
    )
    validated = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("Équipe validée")
    )
    password = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(8)],
        null=False,
        blank=False,
        verbose_name=_("Mot de passe de l'équipe"),
    )
    captain = models.ForeignKey(
        "Player",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Capitaine"),
        related_name="team_captain",
    )
    seat_slot = models.OneToOneField(
        "SeatSlot",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Slot"),
    )
    seed = models.PositiveIntegerField(
        verbose_name=_("Seed"),
        null=False,
        blank=False,
        default=0,
    )


    class Meta:
        """Meta Options"""

        verbose_name = _("Équipe")
        verbose_name_plural = _("Équipes")
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "name"], name="no_name_conflict_in_tournament"
            )
        ]
        indexes = [
            models.Index(fields=["tournament"]),
        ]

    def __str__(self) -> str:
        """Format this team to a str"""
        if self.tournament is not None:
            return f"{self.name} ({self.tournament.event})"
        return f"{self.name} (???)"

    def get_name(self):
        """
        Retrieve the name of this team.
        """
        return self.name

    def get_tournament(self) -> Optional["Tournament"]:
        """
        Retrieve the tournament of this team. Potentially null.
        """
        return self.tournament

    def get_players(self) -> List["Player"]:
        """
        Retrieve all the players in the database for that team
        """
        return player.Player.objects.filter(team=self)

    def get_players_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all players
        """
        return self.get_players().values_list("id", flat=True)

    def get_managers(self) -> List["Manager"]:
        """
        Retrieve all the managers in the database for that team
        """
        return manager.Manager.objects.filter(team=self)

    def get_managers_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all managers
        """
        return self.get_managers().values_list("id", flat=True)

    def get_managers_user_name(self) -> List[str]:
        """
        Retrieve the user names of all managers
        """
        return [manager.as_user().username for manager in self.get_managers()]

    def get_substitutes(self) -> List["Substitute"]:
        """
        Retrieve all the substitutes in the database for that team
        """
        return substitute.Substitute.objects.filter(team=self)

    def get_substitutes_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all substitutes
        """
        return self.get_substitutes().values_list("id", flat=True)

    def get_captain_name(self) -> str:
        """
        Retrieve the captain of the team
        """
        if self.captain is not None:
            return self.captain.name_in_game
        return None

    def get_password(self) -> str:
        """Return team password"""
        return self.password

    def get_group_matchs(self) -> List["GroupMatch"]:
        return group.GroupMatch.objects.filter(teams=self)

    def get_knockout_matchs(self) -> List["KnockoutMatch"]:
        return bracket.KnockoutMatch.objects.filter(teams=self)

    def get_swiss_matchs(self) -> List["SwissMatch"]:
        return swiss.SwissMatch.objects.filter(teams=self)

    def get_matchs(self) -> List[Union[List["GroupMatch"],List["KnockoutMatch"],List["SwissMatch"]]]:
        return self.get_group_matchs(), self.get_knockout_matchs(), self.get_swiss_matchs()

    def get_seat_slot_id(self) -> Optional[int]:
        """
        Retrieve the seat slot identifier of the team
        """
        if self.seat_slot is not None:
            return self.seat_slot.id
        return None

    def refresh_validation(self):
        """Refreshes the validation state of a tournament"""
        # Condition 1: ceil((n+1)/2) players have paid/will pay
        if self.validated:
            return
        if self.tournament.get_validated_teams() < self.tournament.get_max_team():
            players = self.get_players()

            game = self.get_tournament().get_game()

            threshold = ceil((game.get_players_per_team()+1)/2)

            paid_seats = len(players.filter(payment_status=ps.PaymentStatus.PAID))

            self.validated = paid_seats >= threshold
            self.save()

    def clean(self):
        """
        Assert that the tournament associated with the provided team is announced
        """
        if not validators.tournament_announced(self.tournament):
            raise ValidationError(
                _("Tournoi non annoncé")
            )
        if validators.tournament_registration_full(self.tournament, exclude=self.id):
            raise ValidationError(
                _("Tournoi complet")
            )

    def save(self, *args, **kwargs):
        try:
            if self.captain is None:
                players = self.get_players()
                if len(players) > 0:
                    self.captain = players[0]
        except player.Player.DoesNotExist:
            players = self.get_players()
            if len(players) > 0:
                self.captain = players[0]
            else:
                self.captain = None
        super().save(*args, **kwargs)
