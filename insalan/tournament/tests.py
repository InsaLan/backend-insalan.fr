"""Tournament Module Tests"""
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase

from insalan.tournament.models import Team, Tournament, Event, Game
from insalan.user.models import User, Player, Manager


class GameTestCase(TestCase):
    """Tests for the Game class"""

    def test_game_null_name(self):
        """Test that no game can have a null name"""
        self.assertRaises(IntegrityError, Game.objects.create, name=None)

    def test_simple_game(self):
        """Create a simple game"""
        Game.objects.create(name="CS:GO")


class EventTestCase(TransactionTestCase):
    """Tests for the Event class"""

    def test_simple_event(self):
        """Test that we can create a simple event"""
        Event.objects.create(name="Insalan Test", year=2023, month=2, description="")

    def test_non_null_fields(self):
        """Test that all non-nullable fields should raise errors"""
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name=None,
            year=2023,
            month=2,
            description="",
        )
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name="",
            year=None,
            month=2,
            description="",
        )
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name="",
            year=2023,
            month=None,
            description="",
        )
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name="",
            year=2023,
            month=2,
            description=None,
        )

    def test_get_tournaments(self):
        """Get tournaments for an event"""
        event = Event.objects.create(name="Test", year=2023, month=3, description="")
        event_two = Event.objects.create(
            name="Test Two", year=2023, month=2, description=""
        )
        game_one = Game.objects.create(name="Test Game One")
        game_two = Game.objects.create(name="Test Game Two")
        game_three = Game.objects.create(name="Test Game Three")
        trnm_one = Tournament.objects.create(game=game_one, event=event)
        trnm_two = Tournament.objects.create(game=game_two, event=event)
        trnm_three = Tournament.objects.create(game=game_three, event=event)
        trnm_four = Tournament.objects.create(game=game_three, event=event_two)

        trnms_found = event.get_tournaments()
        self.assertEqual(3, len(trnms_found))
        self.assertTrue(trnm_one in trnms_found)
        self.assertTrue(trnm_two in trnms_found)
        self.assertTrue(trnm_three in trnms_found)
        self.assertFalse(trnm_four in trnms_found)


class TournamentTestCase(TestCase):
    """Tournament Tests"""
    def setUp(self):
        """Set up the Tournaments"""
        event = Event.objects.create(name="Test", year=2023, month=3, description="")
        event_two = Event.objects.create(
            name="Test Two", year=2023, month=2, description=""
        )
        game_one = Game.objects.create(name="Test Game One")
        game_two = Game.objects.create(name="Test Game Two")
        game_three = Game.objects.create(name="Test Game Three")
        Tournament.objects.create(game=game_one, event=event)
        Tournament.objects.create(game=game_two, event=event)
        Tournament.objects.create(game=game_three, event=event)
        Tournament.objects.create(game=game_three, event=event_two)

    def test_tournament_null_event(self):
        """Test failure of creation of a Tournament with no event"""
        game = Game.objects.create(name="Test")
        self.assertRaises(IntegrityError, Tournament.objects.create, event=None, game=game)

    def test_tournament_null_game(self):
        """Test failure of creation of a Tournament with no game"""
        event = Event.objects.create(name="Test", year=2023, month=2, description="")
        self.assertRaises(IntegrityError, Tournament.objects.create, event=event, game=None)

    def test_get_event(self):
        """Get the event for a tournament"""
        event = Event.objects.get(year=2023, month=3)
        game = Game.objects.get(name="Test Game One")
        tourney = Tournament.objects.get(game=game)

        self.assertEqual(event, tourney.get_event())

    def test_get_game(self):
        """Get the game for a tournament"""
        event = Event.objects.get(year=2023, month=2)
        game = Game.objects.get(name="Test Game Three")
        tourney = Tournament.objects.get(event=event)

        self.assertEqual(game, tourney.get_game())

    def test_get_teams(self):
        """Get the teams for a tournament"""
        tourney = Tournament.objects.all()[0]
        tourney_two = Tournament.objects.all()[1]
        team_one = Team.objects.create(name="Ohlala", tournament=tourney)
        team_two = Team.objects.create(name="OhWow", tournament=tourney)
        team_three = Team.objects.create(name="LeChiengue", tournament=tourney_two)

        teams = tourney.get_teams()
        self.assertEqual(2, len(teams))
        self.assertTrue(team_one in teams)
        self.assertTrue(team_two in teams)
        self.assertFalse(team_three in teams)

class TeamTestCase(TestCase):
    """
    Tests for the Team model
    """

    def setUp(self):
        """
        Set the tests up
        """
        robert: User = User.objects.create_user(
            username="robertisgaming",
            email="robert.durand@example.net",
            password="password1234",
            first_name="Robert",
            last_name="Durand",
        )

        didier: User = User.objects.create_user(
            username="xXxdidierdu45xXx",
            email="didiervroomvroom@example.net",
            password="lol",
            first_name="Didier",
            last_name="Bouchard",
        )

        gege: User = User.objects.create_user(
            username="amesombre",
            email="perdu@example.net",
            password='2389012dhaeiodapend zd"d;d;',
            first_name="Gérard",
            last_name="Levain",
        )

        event_one = Event.objects.create(
            name="Insalan Test One", year=2023, month=2, description=""
        )

        game = Game.objects.create(name="Fortnite")

        trnm_one = Tournament.objects.create(event=event_one, game=game)
        trnm_two = Tournament.objects.create(event=event_one, game=game)

        team_lalooze: Team = Team.objects.create(name="LaLooze", tournament=trnm_one)

        team_lapouasse: Team = Team.objects.create(
            name="LaPouasse", tournament=trnm_two
        )

        Player.objects.create(user=robert, team=team_lalooze)
        Player.objects.create(user=didier, team=team_lalooze)
        Player.objects.create(user=gege, team=team_lapouasse)
        Manager.objects.create(user=didier, team=team_lapouasse)

    def test_team_get_full(self):
        """Get the fields of a Team"""
        team = Team.objects.get(name="LaLooze")
        self.assertIsNotNone(team)

        self.assertEqual("LaLooze", team.get_name())
        self.assertIsInstance(team.get_tournament(), Tournament)
        self.assertEqual(2, len(team.get_players()))
        self.assertEqual(0, len(team.get_managers()))

        team = Team.objects.get(name="LaPouasse")
        self.assertIsNotNone(team)

        self.assertEqual("LaPouasse", team.get_name())
        self.assertIsInstance(team.get_tournament(), Tournament)
        self.assertEqual(1, len(team.get_players()))
        self.assertEqual(1, len(team.get_managers()))

    def test_get_full_null_tournament(self):
        """Get a team with a null tournament"""
        team = Team.objects.create(name="LaZone", tournament=None)

        team.full_clean()

        self.assertIsNone(team.get_tournament())

    def test_get_team_players(self):
        """Get the players of a Team"""
        team = Team.objects.get(name="LaLooze")
        self.assertIsNotNone(team)

        players = team.get_players()
        self.assertEqual(len(players), 2)
        player_robert = [
            player.as_user()
            for player in players
            if player.as_user().get_username() == "robertisgaming"
        ][0]
        player_didier = [
            player.as_user()
            for player in players
            if player.as_user().get_username() == "xXxdidierdu45xXx"
        ][0]

        self.assertEqual(player_robert.get_full_name(), "Robert Durand")
        self.assertEqual(player_didier.get_full_name(), "Didier Bouchard")

        # Same with the other team
        team = Team.objects.get(name="LaPouasse")
        self.assertIsNotNone(team)

        players = team.get_players()
        self.assertEqual(len(players), 1)

        player_gege = players[0].as_user()
        self.assertEqual(player_gege.get_username(), "amesombre")
        self.assertEqual(player_gege.get_full_name(), "Gérard Levain")

    def test_team_collision_name(self):
        """Test Name Collision for a Tournament"""
        team = Team.objects.get(name="LaLooze")
        tourney = team.get_tournament()

        # Attempt to register another one
        self.assertRaises(IntegrityError, Team.objects.create, name="LaLooze", tournament=tourney)