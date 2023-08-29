"""
Module that contains the declaration of structures tied to tournaments
"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

import os.path

from typing import List, Optional
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    MinLengthValidator,
)
from django.utils.translation import gettext_lazy as _

from insalan.settings import STATIC_URL
from insalan.user.models import User


class Event(models.Model):
    """
    An Event is any single event that is characterized by the following:
     - A single player can only register for a single tournament per event

    This means, for example, that if we want to let players play in the smash
    tournaments and InsaLan one year, we can have two events happening
    concurrently.
    """

    name = models.CharField(
        verbose_name="Event Name",
        max_length=40,
        validators=[MinLengthValidator(4)],
        null=False,
    )
    description = models.CharField(
        verbose_name="Event Description", max_length=128, default="", blank=True
    )
    year = models.IntegerField(null=False, validators=[MinValueValidator(2003)])
    month = models.IntegerField(
        null=False, validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    ongoing = models.BooleanField(default=False)
    logo: models.FileField = models.FileField(
        blank=True,
        null=True,
        upload_to=os.path.join(STATIC_URL, 'event-icons'),
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg',
                                                               'jpeg', 'svg'])]
    )

    def __str__(self) -> str:
        """Format this Event to a str"""
        return f"{self.name} ({self.year}-{self.month:02d})"

    def get_tournaments_id(self) -> List[int]:
        """Return the list of tournaments identifiers for that Event"""
        return Tournament.objects.filter(event=self).values_list("id", flat=True)

    def get_tournaments(self) -> List["Tournament"]:
        """Return the list of tournaments for that Event"""
        return Tournament.objects.filter(event=self)

    @staticmethod
    def get_ongoing_ids() -> List[int]:
        """Return the identifiers of ongoing events"""
        return __class__.objects.filter(ongoing=True).values_list("id", flat=True)


class Game(models.Model):
    """
    A Game is the representation of a Game that is being played at InsaLan
    """

    name = models.CharField(
        verbose_name="Game Name",
        validators=[MinLengthValidator(2)],
        max_length=40,
        null=False,
    )
    short_name = models.CharField(
        verbose_name="Short Name",
        validators=[MinLengthValidator(2)],
        max_length=10,
        null=False,
        blank=False,
    )

    def __str__(self) -> str:
        """Format this Game to a str"""
        return f"{self.name} ({self.short_name})"

    def get_name(self) -> str:
        """Return the name of the game"""
        return self.name

    def get_short_name(self) -> str:
        """Return the short name of the game"""
        return self.short_name


class Tournament(models.Model):
    """
    A Tournament happening during an event that Teams of players register for.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name=_("Tournament name"),
        validators=[MinLengthValidator(3)],
        max_length=40,
    )
    rules = models.TextField(verbose_name=_("Tournament Rules"),
                             max_length=50000, null=False, blank=True,
                             default="")
    logo: models.FileField = models.FileField(
        blank=True,
        null=True,
        upload_to=os.path.join(STATIC_URL, 'tournament-icons'),
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg',
                                                               'jpeg', 'svg'])]
    )

    def __str__(self) -> str:
        """Format this Tournament to a str"""
        return f"{self.name} (@ {self.event})"

    def get_name(self) -> str:
        """Get the name of the tournament"""
        return self.name

    def get_event(self) -> Event:
        """Get the event of a tournament"""
        return self.event

    def get_game(self) -> Game:
        """Get the game of a tournament"""
        return self.game

    def get_teams(self) -> List["Team"]:
        """Return the list of Teams in that Tournament"""
        return Team.objects.filter(tournament=self)

    def get_teams_id(self) -> List[int]:
        """Return the list of identifiers of this Tournament's Teams"""
        return self.get_teams().values_list("id", flat=True)

    def get_rules(self) -> str:
        """Return the raw tournament rules"""
        return self.rules


class Team(models.Model):
    """
    A Team consists in a group of one or more players, potentially helmed by a
    `Manager`.
    """

    tournament = models.ForeignKey(
        Tournament, null=True, blank=True, on_delete=models.SET_NULL
    )
    name = models.CharField(
        max_length=42,
        validators=[MinLengthValidator(3)],
        null=False,
        verbose_name="Team Name",
    )

    class Meta:
        """Meta Options"""

        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "name"], name="no_name_conflict_in_tournament"
            )
        ]

    def __str__(self) -> str:
        """Format this team to a str"""
        return f"{self.name} ({self.tournament.event})"

    def get_name(self):
        """
        Retrieve the name of this team.
        """
        return self.name

    def get_tournament(self) -> Optional[Tournament]:
        """
        Retrieve the tournament of this team. Potentially null.
        """
        return self.tournament

    def get_players(self) -> List["Player"]:
        """
        Retrieve all the players in the database for that team
        """
        return Player.objects.filter(team=self)

    def get_players_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all players
        """
        return self.get_players().values_list("user_id", flat=True)

    def get_managers(self) -> List["Manager"]:
        """
        Retrieve all the managers in the database for that team
        """
        return Manager.objects.filter(team=self)

    def get_managers_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all managers
        """
        return self.get_managers().values_list("user_id", flat=True)


class PaymentStatus(models.TextChoices):
    """Information about the current payment status of a Player/Manager"""

    NOT_PAID = "NOTPAID", _("Not Paid")
    PAID = "PAID", _("Paid")
    PAY_LATER = "LATER", _("Will pay on site")


class Player(models.Model):
    """
    A Player at InsaLan is simply anyone who is registered to participate in a
    tournamenent, whichever it might be.
    """
    class Meta:
        """Meta options"""
        verbose_name = "Player Registration"
        verbose_name_plural = "Player Registrations"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey("tournament.Team", on_delete=models.CASCADE)
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=PaymentStatus.NOT_PAID,
        null=False,
        verbose_name="Payment Status",
    )

    def __str__(self) -> str:
        """Format this player registration to a str"""
        return f"{self.user.username} for {self.team}"

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self):
        """Return the Team object of the current team"""
        return self.team

    def clean(self):
        """
        Assert that the user associated with the provided player does not already
        exist in any team of any tournament of the event
        """
        event = self.get_team().get_tournament().get_event()

        if (
            len(
                [
                    player.user
                    for players in [
                        team.get_players()
                        for teams in [
                            trnm.get_teams() for trnm in event.get_tournaments()
                        ]
                        for team in teams
                    ]
                    for player in players
                    if player.user == self.user
                ]
            )
            > 1
        ):
            raise ValidationError(_("Player already registered for this event"))


class Manager(models.Model):
    """
    A Manager is someone in charge of heading a team of players.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey("tournament.Team", on_delete=models.CASCADE)
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=PaymentStatus.NOT_PAID,
        null=False,
        verbose_name="Payment Status",
    )

    class Meta:
        """Meta Options"""
        verbose_name = "Manager Registration"
        verbose_name_plural = "Manager Registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "team"], name="not_twice_same_manager"
            )
        ]

    def __str__(self) -> str:
        """Format this manager registration as a str"""
        return (
            f"(Manager) {self.user.username} for {self.team}"
        )

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self):
        """Return the Team object of the current team"""
        return self.team


# vim: set cc=80 tw=80:
