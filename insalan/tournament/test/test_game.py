"""Tournament Game Module Tests"""

from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase

from insalan.tournament.models import Game

class GameTestCase(TestCase):
    """Tests for the Game class"""

    def test_game_null_name(self) -> None:
        """Test that no game can have a null name"""
        self.assertRaises(IntegrityError, Game.objects.create, name=None)

    def test_simple_game(self) -> None:
        """Create a simple game"""
        Game.objects.create(name="CS:GO")

    def test_game_name_too_short(self) -> None:
        """Verify that a game's name cannot be too short"""
        gobj = Game(name="C", short_name="CSGO")
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.name = "CS"
        gobj.full_clean()

    def test_game_name_too_long(self) -> None:
        """Verify that a game's name cannot be too long"""
        gobj = Game(name="C" * 41, short_name="CSGO")
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.name = "C" * 40
        gobj.full_clean()

    def test_game_short_name_too_short(self) -> None:
        """Verify that a game's short name cannot be too short"""
        gobj = Game(name="CSGO", short_name="C")
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.short_name = "CS"
        gobj.full_clean()

    def test_game_short_name_too_long(self) -> None:
        """Verify that a game's name cannot be too long"""
        gobj = Game(name="CSGO", short_name="C" * 11)
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.short_name = "C" * 10
        gobj.full_clean()
