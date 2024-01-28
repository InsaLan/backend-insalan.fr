from typing import List, Optional
from math import ceil
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

from django.utils.translation import gettext_lazy as _

from insalan.tickets.models import Ticket
from insalan.user.models import User

from . import player
from . import manager
from . import substitute

from . import validators

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
    # group = models.ForeignKey(
    #     "Group",
    #     verbose_name=_("Poule"),
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )
    # seeding = models.IntegerField()
    # bracket = models.ForeignKey(
    #     "Bracket",
    #     verbose_name=_("Arbre de tournoi"),
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )

    class Meta:
        """Meta Options"""

        verbose_name = _("Équipe")
        verbose_name_plural = _("Équipes")
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "name"], name="no_name_conflict_in_tournament"
            )
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

    def get_password(self) -> str:
        """Return team password"""
        return self.password

    def refresh_validation(self):
        """Refreshes the validation state of a tournament"""
        # Condition 1: ceil((n+1)/2) players have paid/will pay
        if self.validated:
            return
        if self.tournament.get_validated_teams() < self.tournament.get_max_team():
            players = self.get_players()

            game = self.get_tournament().get_game()

            threshold = ceil((game.get_players_per_team()+1)/2)

            paid_seats = len(players.filter(payment_status=PaymentStatus.PAID))

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
        if self.captain is None:
            players = self.get_players()
            if len(players) > 0:
                self.captain = players[0]
        super().save(*args, **kwargs)