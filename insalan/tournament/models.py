"""
Module that contains the declaration of structures tied to tournaments
"""
from typing import List, Optional
from django.db import models
from django.utils.translation import gettext_lazy as _

from insalan.user.models import Player, Manager


class Event(models.Model):
    """
    An Event is any single event that is characterized by the following:
     - A single player can only register for a single tournament per event

    This means, for example, that if we want to let players play in the smash
    tournaments and InsaLan one year, we can have two events happening
    concurrently.
    """

    name = models.CharField(verbose_name="Event Name", max_length=40, null=False)
    description = models.CharField(verbose_name="Event Description", max_length=128)
    year = models.IntegerField(null=False)
    month = models.IntegerField(null=False)

    def get_tournaments(self) -> List["Tournament"]:
        """Return the list of tournaments for that Event"""
        return Tournament.objects.filter(event=self)


class Game(models.Model):
    """
    A Game is the representation of a Game that is being played at InsaLan
    """

    name = models.CharField(verbose_name="Game Name", max_length=40, null=False)


class Tournament(models.Model):
    """
    A Tournament happening during an event that Teams of players register for.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    def get_event(self) -> Event:
        """Get the event of a tournament"""
        return self.event

    def get_game(self) -> Game:
        """Get the game of a tournament"""
        return self.game

    def get_teams(self) -> List["Team"]:
        """Return the list of Teams in that Tournament"""
        return Team.objects.filter(tournament=self)


class Team(models.Model):
    """
    A Team consists in a group of one or more players, potentially helmed by a
    `Manager`.
    """

    tournament = models.ForeignKey(
        Tournament, null=True, blank=True, on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=42, null=False, verbose_name="Team Name")

    class Meta:
        """Meta Options"""
        constraints = [
                models.UniqueConstraint(fields=["tournament", "name"],
                                        name="no_name_conflict_in_tournament")
                ]

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

    def get_players(self):
        """
        Retrieve all the players in the database for that team
        """
        return Player.objects.filter(team=self)

    def get_managers(self):
        """
        Retrieve all the managers in the database for that team
        """
        return Manager.objects.filter(team=self)


# vim: set cc=80 tw=80:
