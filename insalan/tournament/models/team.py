from __future__ import annotations

from typing import Any, TYPE_CHECKING

from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _

from . import bracket
from . import group
from . import player
from . import manager
from . import substitute
from . import swiss
from . import tournament
from . import validators


if TYPE_CHECKING:
    from django_stubs_ext import ValuesQuerySet

    from .group import GroupMatch
    from .bracket import KnockoutMatch
    from .manager import Manager
    from .substitute import Substitute
    from .player import Player
    from .swiss import SwissMatch
    from .tournament import BaseTournament


class Team(models.Model):
    """
    A Team consists in a group of one or more players, potentially helmed by a
    `Manager`.
    """

    tournament = models.ForeignKey(
        "BaseTournament",
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
        if isinstance(self.tournament, tournament.EventTournament):
            return f"{self.name} ({self.tournament.event})"
        return f"{self.name} ({self.tournament.name})"

    def get_name(self) -> str:
        """
        Retrieve the name of this team.
        """
        return self.name

    def get_tournament(self) -> BaseTournament:
        """
        Retrieve the tournament of this team.
        """
        return self.tournament

    def get_players(self) -> QuerySet[Player]:
        """
        Retrieve all the players in the database for that team.
        """
        return player.Player.objects.filter(team=self)

    def get_players_id(self) -> ValuesQuerySet[Player, int]:
        """
        Retrieve the user identifiers of all players
        """
        return self.get_players().values_list("id", flat=True)

    def get_managers(self) -> QuerySet[Manager]:
        """
        Retrieve all the managers in the database for that team
        """
        return manager.Manager.objects.filter(team=self)

    def get_managers_id(self) -> ValuesQuerySet[Manager, int]:
        """
        Retrieve the user identifiers of all managers
        """
        return self.get_managers().values_list("id", flat=True)

    def get_managers_user_name(self) -> list[str]:
        """
        Retrieve the user names of all managers
        """
        return [manager.as_user().username for manager in self.get_managers()]

    def get_substitutes(self) -> QuerySet[Substitute]:
        """
        Retrieve all the substitutes in the database for that team
        """
        return substitute.Substitute.objects.filter(team=self)

    def get_substitutes_id(self) -> ValuesQuerySet[Substitute, int]:
        """
        Retrieve the user identifiers of all substitutes
        """
        return self.get_substitutes().values_list("id", flat=True)

    def get_captain_name(self) -> str | None:
        """
        Retrieve the captain of the team
        """
        if self.captain is not None:
            return self.captain.name_in_game
        return None

    def get_password(self) -> str:
        """Return team password"""
        return self.password

    def get_group_matchs(self) -> QuerySet[GroupMatch]:
        return group.GroupMatch.objects.filter(teams=self)

    def get_knockout_matchs(self) -> QuerySet[KnockoutMatch]:
        return bracket.KnockoutMatch.objects.filter(teams=self)

    def get_swiss_matchs(self) -> QuerySet[SwissMatch]:
        return swiss.SwissMatch.objects.filter(teams=self)

    def get_matchs(self
                   ) -> tuple[QuerySet[GroupMatch], QuerySet[KnockoutMatch], QuerySet[SwissMatch]]:
        return self.get_group_matchs(), self.get_knockout_matchs(), self.get_swiss_matchs()

    def get_seat_slot_id(self) -> int | None:
        """
        Retrieve the seat slot identifier of the team
        """
        if self.seat_slot is not None:
            return self.seat_slot.id  # pylint: disable=no-member
        return None

    def refresh_validation(self) -> None:
        """Rafraîchit l'état de validation d'une équipe et du tournoi"""
        if self.validated:
            return

        # Try to expand the tournament thresholds
        # If successful, the team might now be valid
        expanded = self.tournament.try_expand_threshold()

        # Check if the team can now be validated
        if not expanded:
            validated_count = self.tournament.get_validated_teams()
            current_max = self.tournament.get_max_team()

            if validated_count < current_max:
                if self.tournament.team_meets_validation_criteria(self):
                    self.validated = True
                    self.save(update_fields=['validated'])

                    # Try to expand the tournament thresholds again
                    # Should not be necessary, but double check
                    self.tournament.try_expand_threshold()

        self.save()

    def clean(self) -> None:
        """
        Assert that the tournament associated with the provided team is announced
        """
        if isinstance(self.tournament, tournament.EventTournament):
            if not validators.tournament_announced(self.tournament):
                raise ValidationError(
                    _("Tournoi non annoncé")
                )
        if validators.tournament_registration_full(self.tournament, exclude=self.id):
            raise ValidationError(
                _("Tournoi complet")
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
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
