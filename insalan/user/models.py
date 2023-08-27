"""
Module for the definition of models tied to users
"""

from typing import Optional, List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    A user is simply our own abstraction defined above the standard Django User
    class.
    """

    def __init__(self, *args, **kwargs):
        AbstractUser.__init__(self, *args, **kwargs)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

    email = models.EmailField(
        verbose_name="email address", max_length=255, unique=True, blank=False
    )
    email_active = models.BooleanField(verbose_name="Email Activated", default=False)
    # Actually only used for super-user CLI tool
    # REQUIRED_FIELDS = [
    #         'email',
    #         'first_name',
    #         'last_name',
    #         ]


class Player(models.Model):
    """
    A Player at InsaLan is simply anyone who is registered to participate in a
    tournamenent, whichever it might be.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey("tournament.Team", on_delete=models.CASCADE)

    def __str__(self) -> str:
        """Format this player registration to a str"""
        return f'{self.user.username} for {self.team} ({self.team.tournament})'

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

    class Meta:
        """Meta Options"""

        constraints = [
            models.UniqueConstraint(
                fields=["user", "team"], name="not_twice_same_manager"
            )
        ]

    def __str__(self) -> str:
        """Format this manager registration as a str"""
        return f'(Manager) {self.user.username} for {self.team} ({self.team.tournament})'

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self):
        """Return the Team object of the current team"""
        return self.team


# vim: set tw=80 cc=80:
