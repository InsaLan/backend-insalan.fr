"""
NameValidator class
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Type, TYPE_CHECKING, cast

from django.utils.translation import gettext_lazy as _

import requests

from insalan.settings import FACEIT_API_KEY, RIOT_API_KEY

if TYPE_CHECKING:
    from django_stubs_ext import StrPromise


REQUESTS_TIMEOUT_SECONDS: int = 5


class NameValidator(ABC):
    short: ClassVar[str]
    name: ClassVar[StrPromise]

    @staticmethod
    @abstractmethod
    def validate_name(_name: str) -> dict[str, Any] | None:
        """
        This method is used to validate the name of a player
        Each validators should implement this method
        """

    @staticmethod
    @abstractmethod
    def update_name(_name: str, _data: dict[str, Any]) -> str:
        """
        This method is used to update the name of a player
        Each validators should implement this method
        """


class EmptyNameValidator(NameValidator):
    """NameValidator class"""
    short = "None"
    name = _("Pas de Validation de nom")

    @staticmethod
    def validate_name(_name: str) -> dict[str, Any] | None:
        # No validation required: return an empty dict to indicate success
        return {}

    @staticmethod
    def update_name(_name: str, _data: dict[str, Any]) -> str:
        return _name


class FaceItNameValidator(NameValidator):
    """FaceItNameValidator class"""

    short = "FaceIt"
    name = _("Validation FaceIt")

    face_it_api: str = "https://open.faceit.com/data/v4"

    @staticmethod
    def validate_name(name: str) -> dict[str, Any] | None:
        """This method is used to validate the FaceIt name of a CS2 player."""
        response = requests.get(
            f"{FaceItNameValidator.face_it_api}/players",
            params={"nickname": name, },
            headers={"Authorization": f"Bearer {FACEIT_API_KEY}"},
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )

        if response.status_code != 200:
            return None

        player_id = response.json()["player_id"]
        data = {"player_id": player_id}

        return data

    @staticmethod
    def update_name(name: str, data: dict[str, Any]) -> str:
        """
        This method is used to update the FaceIt name of a CS2 player based on
        its player id.
        """
        player_id: str = data["player_id"]
        response = requests.get(
            f"{FaceItNameValidator.face_it_api}/players/{player_id}",
            headers={"Authorization": f"Bearer {FACEIT_API_KEY}"},
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return name

        nickname: str | None = response.json().get("nickname")

        if nickname is None:
            return name

        return nickname


class LeagueOfLegendsNameValidator(NameValidator):
    """LeagueOfLegendsNameValidator class"""
    short = "LoL"
    name = _("Validation League of Legends")

    @staticmethod
    def validate_name(name: str) -> dict[str, Any] | None:
        """This method is used to validate the name of a LoL player."""
        # pylint: disable-next=line-too-long
        accountendpoint: str = "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{}/{}?api_key={}"
        # pylint: disable-next=line-too-long
        summonerendpoint: str = "https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{}?api_key={}"

        data = {}

        # Validate the format of the name
        if name.count("#") != 1:
            return None
        gamename, tagline = name.split("#")

        # Get the puuid associated with the account
        response = requests.get(
            accountendpoint.format(gamename, tagline, RIOT_API_KEY),
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return None
        puuid = response.json()["puuid"]
        data["puuid"] = puuid

        # Get the league of legends account associated with the puuid
        response = requests.get(
            summonerendpoint.format(puuid, RIOT_API_KEY),
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return None

        # We don't need to check the response, if the request was successful,
        # the name is valid and a league of legends account exists with this name

        return data

    @staticmethod
    def update_name(name: str, data: dict[str, Any]) -> str:
        """
        This method is used to update the name of a LoL player based on the puuid
        """
        # pylint: disable-next=line-too-long
        summonerendpoint: str = "https://europe.api.riotgames.com/riot/account/v1/accounts/by-puuid/{}?api_key={}"

        if "puuid" not in data:
            return name

        puuid = data["puuid"]
        response = requests.get(
            summonerendpoint.format(puuid, RIOT_API_KEY),
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )
        # If the request fails, don't update the name
        if response.status_code != 200:
            return name

        # Type the JSON response to avoid returning Any and validate fields
        json_data = cast(dict[str, Any], response.json())

        game_name = json_data.get("gameName")
        tag_line = json_data.get("tagLine")
        if not isinstance(game_name, str) or not isinstance(tag_line, str):
            return name

        return game_name + "#" + tag_line


validators: list[Type[NameValidator]] = [
    EmptyNameValidator,
    FaceItNameValidator,
    LeagueOfLegendsNameValidator,
]


def get_choices() -> list[tuple[str, StrPromise]]:
    """
    Get the choices for the validators
    """
    return [(validator.short, validator.name) for validator in validators]


def get_validator(name: str) -> Type[NameValidator] | None:
    """
    Get the validator from a name
    """
    for validator in validators:
        if validator.short == name:
            return validator
    return None
