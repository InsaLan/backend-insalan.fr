"""
NameValidator class
"""
from django.utils.translation import gettext_lazy as _
from django.db import models
from insalan.settings import RIOT_API_KEY
import requests

class EmptyNameValidator:
    """
    NameValidator class
    """
    short = "None"
    name = _("Pas de Validation de nom")

    @staticmethod
    def is_valid(name: str):
        """
        This method is used to validate the name of a player
        Each validators should implement this method
        """
        return True

class LeagueOfLegendsNameValidator:
    """
    LeagueOfLegendsNameValidator class
    """
    short = "LoL"
    name = _("Validation League of Legends")

    Account_endpoint = "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{}/{}?api_key={}"
    Summoner_endpoint = "https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{}?api_key={}"

    @staticmethod
    def is_valid(name: str):
        """
        This method is used to validate the name of a LoL player
        """
        # Validate the format of the name
        if not "#" in name:
            return False
        if name.count("#") > 1:
            return False
        gamename, tagline = name.split("#")

        # Get the puuid associated with the account
        response = requests.get(
            LeagueOfLegendsNameValidator.Account_endpoint.format(gamename, tagline, RIOT_API_KEY),
            timeout=5
        )
        if response.status_code != 200:
            return False
        puuid = response.json()["puuid"]

        # Get the league of legends account associated with the puuid
        response = requests.get(
            LeagueOfLegendsNameValidator.Summoner_endpoint.format(puuid, RIOT_API_KEY),
            timeout=5
        )
        if response.status_code != 200:
            return False

        # We don't need to check the response, if the request was successful,
        # the name is valid and a league of legends account exists with this name

        return True

validators = [
    EmptyNameValidator,
    LeagueOfLegendsNameValidator
]

def get_choices():
    """
    Get the choices for the validators
    """
    return [(validator.short, validator.name) for validator in validators]

def get_validator(name):
    """
    Get the validator from a name
    """
    for validator in validators:
        if validator.short == name:
            return validator.is_valid
    return None
