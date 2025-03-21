"""PrivateTournament Module Tests"""

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from insalan.tournament.models import (
    PrivateTournament,
    Game,
)

class PrivateTournamentTestCase(TestCase):
    """
        This class tests the PrivateTournament class and its methods.
        It verifies that the class can be created, that it has the correct
        attributes, and that it can be saved to the database.
        
        For fields that are related to BaseTournament, see the
        BaseTournamentTestCase class.
    """

    def setUp(self):
        """Set up the Tournaments"""
        game_one = Game.objects.create(name="Test Game One")
        game_two = Game.objects.create(name="Test Game Two")
        game_three = Game.objects.create(name="Test Game Three")
        PrivateTournament.objects.create(name="Tourney 1", game=game_one, start=timezone.now())
        PrivateTournament.objects.create(name="Tourney 2", game=game_two, start=timezone.now())
        PrivateTournament.objects.create(name="Tourney 3", game=game_three, start=timezone.now())
        PrivateTournament.objects.create(name="Tourney 4", game=game_three, start=timezone.now())

    def test_create_private_tournament(self):
        """Test creation of PrivateTournament"""
        game = Game.objects.create(name="New Game")
        tournament = PrivateTournament.objects.create(
            name="New Private Tournament",
            game=game,
            password="secret",
            running=True,
            start=timezone.now(),
            rewards="First place gets a trophy"
        )
        self.assertEqual(tournament.name, "New Private Tournament")
        self.assertEqual(tournament.password, "secret")
        self.assertTrue(tournament.running)
        self.assertEqual(tournament.rewards, "First place gets a trophy")

    def test_password_min_length(self):
        """Test that password must be at least 3 characters"""
        game = Game.objects.create(name="New Game")
        tournament = PrivateTournament(
            name="New Private Tournament",
            game=game,
            password="ab",
            running=True,
            start=timezone.now(),
            rewards="First place gets a trophy"
        )
        self.assertRaises(ValidationError, tournament.full_clean)

    def test_start_default(self):
        """Test that start date defaults to now"""
        game = Game.objects.create(name="New Game")
        tournament = PrivateTournament.objects.create(
            name="New Private Tournament",
            game=game,
            password="secret",
            running=True,
            rewards="First place gets a trophy"
        )
        self.assertIsNotNone(tournament.start)

    def test_rewards_blank(self):
        """Test that rewards can be blank"""
        game = Game.objects.create(name="New Game")
        tournament = PrivateTournament.objects.create(
            name="New Private Tournament",
            game=game,
            password="secret",
            running=True,
            start=timezone.now(),
            rewards=""
        )
        self.assertEqual(tournament.rewards, "")

    def test_running_default(self):
        """Test that running defaults to True"""
        game = Game.objects.create(name="New Game")
        tournament = PrivateTournament.objects.create(
            name="New Private Tournament",
            game=game,
            password="secret",
            start=timezone.now(),
            rewards="First place gets a trophy"
        )
        self.assertTrue(tournament.running)
