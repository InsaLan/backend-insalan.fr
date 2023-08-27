"""Tournament Module Tests"""

from types import NoneType

from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase

from insalan.tournament.models import Player, Manager, Team, Tournament, Event, Game
from insalan.user.models import User


class GameTestCase(TestCase):
    """Tests for the Game class"""

    def test_game_null_name(self):
        """Test that no game can have a null name"""
        self.assertRaises(IntegrityError, Game.objects.create, name=None)

    def test_simple_game(self):
        """Create a simple game"""
        Game.objects.create(name="CS:GO")

    def test_game_name_too_short(self):
        """Verify that a game's name cannot be too short"""
        gobj = Game(name="C", short_name="CSGO")
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.name = "CS"
        gobj.full_clean()

    def test_game_name_too_long(self):
        """Verify that a game's name cannot be too long"""
        gobj = Game(name="C" * 41, short_name="CSGO")
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.name = "C" * 40
        gobj.full_clean()

    def test_game_short_name_too_short(self):
        """Verify that a game's short name cannot be too short"""
        gobj = Game(name="CSGO", short_name="C")
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.short_name = "CS"
        gobj.full_clean()

    def test_game_short_name_too_long(self):
        """Verify that a game's name cannot be too long"""
        gobj = Game(name="CSGO", short_name="C" * 11)
        self.assertRaises(ValidationError, gobj.full_clean)

        gobj.short_name = "C" * 10
        gobj.full_clean()


class EventTestCase(TransactionTestCase):
    """Tests for the Event class"""

    def test_simple_event(self):
        """Test that we can create a simple event"""
        Event.objects.create(name="Insalan Test", year=2023, month=2, description="")

    def test_name_minimum_length(self):
        """Test that an Event cannot have too short a name"""
        eobj = Event(name="Ins", year=2023, month=2)
        self.assertRaises(ValidationError, eobj.full_clean)

    def test_earlierst_event_year(self):
        """Check that we can't have too early an event"""
        eobj = Event(name="InsaLan", year=2002, month=2)
        self.assertRaises(ValidationError, eobj.full_clean)

    def test_low_event_month(self):
        """Check that we cannot use too low an event month"""
        eobj = Event(name="InsaLan", year=2023, month=0)
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = -1
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = -1000
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = 1
        eobj.full_clean()

    def test_high_event_month(self):
        """Check that we cannot use too high an event month"""
        eobj = Event(name="InsaLan", year=2023, month=13)
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = 839
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = 12
        eobj.full_clean()

    def test_ongoing_events(self):
        """Test that we can find events that are ongoing"""
        Event.objects.create(name="InsaLan", year=2023, month=8)
        evobj_one = Event.objects.create(name="InsaLan", year=2023, month=9, ongoing=True)
        Event.objects.create(name="InsaLan", year=2023, month=10)
        evobj_two = Event.objects.create(name="InsaLan", year=2023, month=11, ongoing=True)

        query_ongoing = Event.objects.filter(ongoing=True)
        self.assertEqual(2, len(query_ongoing))

        self.assertTrue(evobj_one in query_ongoing)
        self.assertTrue(evobj_two in query_ongoing)

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

    def test_name_too_short(self):
        """Verify that a tournament name cannot be too short"""
        tourneyobj = Tournament.objects.all()[0]
        tourneyobj.name = "C" * 2
        self.assertRaises(ValidationError, tourneyobj.full_clean)

        tourneyobj.name = "C" * 3
        tourneyobj.full_clean()

    def test_name_too_long(self):
        """Verify that a tournament name cannot be too long"""
        tourney = Tournament.objects.all()[0]
        tourney.name = "C" * 41
        self.assertRaises(ValidationError, tourney.full_clean)

        tourney.name = "C" * 40
        tourney.full_clean()

    def test_game_deletion_cascade(self):
        """Verify that a tournament is deleted when its game is"""
        tourney = Tournament.objects.all()[0]
        game_obj = tourney.game

        Tournament.objects.get(id=tourney.id)

        # Delete and verify
        game_obj.delete()

        self.assertRaises(Tournament.DoesNotExist, Tournament.objects.get, id=tourney.id)

    def test_event_deletion_cascade(self):
        """Verify that a tournament is deleted when its event is"""
        tourney = Tournament.objects.all()[0]
        ev_obj = tourney.game

        Tournament.objects.get(id=tourney.id)

        # Delete and verify
        ev_obj.delete()

        self.assertRaises(Tournament.DoesNotExist, Tournament.objects.get, id=tourney.id)


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

    def test_team_name_too_short(self):
        """Verify that a team name cannot be too short"""
        team = Team.objects.get(name="LaLooze")
        team.name = "CC"
        self.assertRaises(ValidationError, team.full_clean)

        team.name += "C"
        team.full_clean()

    def test_team_name_too_long(self):
        """Verify that a team name cannot be too long"""
        team = Team.objects.get(name="LaLooze")
        team.name = "C" * 43
        self.assertRaises(ValidationError, team.full_clean)

        team.name = "C" * 42
        team.full_clean()

    def test_tournament_deletion_set_null(self):
        """Verify that a Team is deleted when its Tournament is"""
        team = Team.objects.all()[0]
        tourney = team.tournament

        Team.objects.get(id=team.id)

        # Delete and verify
        tourney.delete()

        self.assertIsInstance(Team.objects.get(id=team.id).tournament, NoneType)


# Player Class Tests
class PlayerTestCase(TestCase):
    """Player Unit Test Class"""

    def setUp(self):
        """Setup method for Player Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team_one: Team = Team.objects.create(name="La Team Test", tournament=trnm)

        # Second edition
        event_two = Event.objects.create(
            name="InsaLan Test (Past)", year=2023, month=3, description=""
        )
        trnm_two = Tournament.objects.create(game=game, event=event_two)
        team_two: Team = Team.objects.create(
            name="La Team Test Passée", tournament=trnm_two
        )

        # Now the users
        user_one = User.objects.create_user(
            username="testplayer",
            email="player.user.test@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )

        User.objects.create_user(
            username="randomplayer",
            email="randomplayer@gmail.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
        )

        another_player = User.objects.create_user(
            username="anotherplayer",
            password="ThisIsPassword",
        )

        # Now, registrations
        Player.objects.create(team=team_one, user=user_one)
        Player.objects.create(team=team_one, user=another_player)
        Player.objects.create(team=team_two, user=another_player)

    def test_get_one_player_of_user(self):
        """Check the conversion between user and player"""
        user = User.objects.get(username="testplayer")

        players = Player.objects.filter(user=user)
        # Test player should be registered to only one team in all history
        self.assertEqual(1, len(players))
        player = players[0]

        self.assertEqual(player.as_user(), user)

        self.assertEquals(user.get_username(), "testplayer")
        self.assertEquals(user.get_short_name(), "Iam")
        self.assertEquals(user.get_full_name(), "Iam Staff")
        self.assertEquals(user.get_user_permissions(), set())
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password("^ThisIsAnAdminPassword42$"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_get_many_players_of_user(self):
        """Test that we get all players when registered multiple times"""
        user = User.objects.get(username="anotherplayer")

        players = Player.objects.filter(user=user)
        self.assertEqual(2, len(players))

    def test_get_no_players_of_user(self):
        """Test that we get no players on users never registered"""
        user = User.objects.get(username="randomplayer")

        players = Player.objects.filter(user=user)
        self.assertEqual(0, len(players))

    def test_duplicate_player(self):
        """Test whether the system reacts to player duplicates"""
        event = Event.objects.create(
            name="InsaLan Collision Test", year=2023, month=9, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team = Team.objects.create(name="La Team Test", tournament=trnm)

        user = User.objects.get(username="randomplayer")

        Player.objects.create(user=user, team=team)
        self.assertRaises(
            ValidationError, Player.objects.create(user=user, team=team).full_clean
        )

    def test_not_multiple_players_same_event_same_tournament_same_team(self):
        """Check that saving fails when multiple players are inserted at once"""
        event = Event.objects.create(
            name="InsaLan Collision Test", year=2023, month=9, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team = Team.objects.create(name="La Team Test", tournament=trnm)

        user = User.objects.get(username="randomplayer")

        # Register them once
        Player.objects.create(user=user, team=team)

        # Try and register them in the same team
        player = Player.objects.create(user=user, team=team)
        self.assertRaises(ValidationError, player.full_clean)

    def test_not_multiple_players_same_event_same_tournament_diff_team(self):
        """Check that saving fails when multiple players are inserted at once"""
        event = Event.objects.create(
            name="InsaLan Collision Test", year=2023, month=9, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm)

        user = User.objects.get(username="randomplayer")

        # Register them once
        Player.objects.create(user=user, team=team)

        # Try and register them in the same team
        player = Player.objects.create(user=user, team=team_two)
        self.assertRaises(ValidationError, player.full_clean)

    def test_not_multiple_players_same_event_diff_tournament_diff_team(self):
        """Check that saving fails when multiple players are inserted at once"""
        event = Event.objects.create(
            name="InsaLan Collision Test", year=2023, month=9, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        trnm_two = Tournament.objects.create(game=game, event=event)
        team = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two)

        user = User.objects.get(username="randomplayer")

        # Register them once
        Player.objects.create(user=user, team=team)

        # Try and register them in the same team
        player = Player.objects.create(user=user, team=team_two)
        self.assertRaises(ValidationError, player.full_clean)

    def test_not_multiple_players_diff_event_diff_tournament_diff_team(self):
        """Check that saving fails when multiple players are inserted at once"""
        event = Event.objects.create(
            name="InsaLan Collision Test", year=2023, month=9, description=""
        )
        event_two = Event.objects.create(
            name="InsaLan Collision Test Two", year=2023, month=9, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        trnm_two = Tournament.objects.create(game=game, event=event_two)
        team = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two)

        user = User.objects.get(username="randomplayer")

        # Register them once
        Player.objects.create(user=user, team=team)

        # Try and register them in the same team
        player = Player.objects.create(user=user, team=team_two)
        player.full_clean()

    def test_get_player_team_not_none(self):
        """Check that a player gives a non null team"""
        user = User.objects.get(username="testplayer")

        player = Player.objects.get(user=user)
        self.assertIsNotNone(player)

        team = player.get_team()
        self.assertIsNotNone(team)

    def test_get_player_team_correct(self):
        """Check that a player gives the correct team"""
        user = User.objects.get(username="testplayer")
        # There should be only one
        event = Event.objects.get(year=2023, month=8)
        trnm = Tournament.objects.get(event=event)

        player = Player.objects.get(user=user)
        self.assertIsNotNone(player)

        team = player.get_team()
        self.assertIsNotNone(team)

        self.assertEquals(team.get_name(), "La Team Test")
        self.assertEquals(team.get_tournament(), trnm)

    def test_player_team_deletion(self):
        """Verify the behaviour of a Player when their team gets deleted"""
        user_obj = User.objects.get(username="testplayer")
        # Create a team and player
        team_obj = Team.objects.create(name="La Team Test", tournament=None)
        play_obj = Player.objects.create(team=team_obj, user=user_obj)

        Player.objects.get(id=play_obj.id)

        # Delete and verify
        team_obj.delete()

        self.assertRaises(Player.DoesNotExist, Player.objects.get, id=play_obj.id)

    def test_user_deletion(self):
        """Verify that a Player registration is deleted along with its user"""
        user_obj = User.objects.get(username="testplayer")
        # Create a Player registration
        team_obj = Team.objects.create(name="La Team Test", tournament=None)
        play_obj = Player.objects.create(team=team_obj, user=user_obj)

        # Test
        Player.objects.get(id=play_obj.id)

        user_obj.delete()

        self.assertRaises(Player.DoesNotExist, Player.objects.get, id=play_obj.id)


# TODO: Add tests of the API


# Manager Class Tests
class ManagerTestCase(TestCase):
    """Manager Unit Test Class"""

    def setUp(self):
        """Setup method for Manager Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=3, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)

        user_one = User.objects.create_user(
            username="testplayer",
            email="player.user.test@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )

        random_player: User = User.objects.create_user(
            username="randomplayer",
            email="randomplayer@gmail.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
        )

        another_player = User.objects.create_user(
            username="anotherplayer",
            password="ThisIsPassword",
        )

        Player.objects.create(team=team_one, user=user_one)
        Player.objects.create(team=team_one, user=another_player)
        Manager.objects.create(team=team_one, user=random_player)

    def test_get_user_of_manager(self):
        """Check the conversion between user and manager"""
        user = User.objects.get(username="randomplayer")

        managers = Manager.objects.filter(user=user)
        self.assertEqual(1, len(managers))

        found_user = managers[0].as_user()
        self.assertEqual(found_user, user)

        self.assertEquals(found_user.get_username(), "randomplayer")
        self.assertEquals(found_user.get_short_name(), "Random")
        self.assertEquals(found_user.get_full_name(), "Random Player")
        self.assertEquals(found_user.get_user_permissions(), set())
        self.assertTrue(found_user.has_usable_password())
        self.assertTrue(found_user.check_password("IUseAVerySecurePassword"))
        self.assertTrue(found_user.is_active)
        self.assertFalse(found_user.is_staff)

    def test_get_manager_team_not_none(self):
        """Check that a manager gives a non null team"""
        user = User.objects.get(username="randomplayer")

        managers = Manager.objects.filter(user=user)
        self.assertEqual(1, len(managers))
        manager = managers[0]

        team = manager.get_team()
        self.assertIsNotNone(team)

    def test_not_manager(self):
        """Check that a non-manager cannot become managers"""
        user = User.objects.get(username="testplayer")

        managers = Manager.objects.filter(user=user)
        self.assertEqual(0, len(managers))

    def test_get_player_team_correct(self):
        """Check that a manager gives the correct team"""
        user = User.objects.get(username="randomplayer")
        event = Event.objects.get(year=2023, month=3)
        trnm = Tournament.objects.get(event=event)

        managers = Manager.objects.filter(user=user)
        self.assertEqual(1, len(managers))
        manager = managers[0]

        team = manager.get_team()
        self.assertIsNotNone(team)

        self.assertEquals(team.get_name(), "La Team Test")
        self.assertEquals(team.get_tournament(), trnm)

    def test_one_manager_many_teams_same_event_same_tournament_same_team(self):
        """Test the collision of duplicate managers"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        Manager.objects.create(user=fella, team=team_one).full_clean()
        self.assertRaises(
            IntegrityError, Manager.objects.create, user=fella, team=team_one
        )

    def test_one_manager_many_teams_same_event_same_tournament_diff_team(self):
        """Test the collision of duplicate managers"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm)

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        Manager.objects.create(user=fella, team=team_one).full_clean()
        Manager.objects.create(user=fella, team=team_two).full_clean()

    def test_one_manager_many_teams_same_event_diff_tournament_diff_team(self):
        """Test the collision of duplicate managers"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        trnm_two = Tournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two)

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        Manager.objects.create(user=fella, team=team_one).full_clean()
        Manager.objects.create(user=fella, team=team_two).full_clean()

    def test_one_manager_many_teams_diff_event_diff_tournament_diff_team(self):
        """Test the collision of duplicate managers"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        event_two = Event.objects.create(
            name="InsaLan Test", year=2023, month=2, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        trnm_two = Tournament.objects.create(game=game, event=event_two)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two)

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        Manager.objects.create(user=fella, team=team_one).full_clean()
        Manager.objects.create(user=fella, team=team_two).full_clean()

    def test_manager_team_deletion(self):
        """Verify the behaviour of a Manager when their team gets deleted"""
        user_obj = User.objects.get(username="testplayer")
        # Create a team and player
        team_obj = Team.objects.create(name="La Team Test", tournament=None)
        play_obj = Manager.objects.create(team=team_obj, user=user_obj)

        Manager.objects.get(id=play_obj.id)

        # Delete and verify
        team_obj.delete()

        self.assertRaises(Manager.DoesNotExist, Manager.objects.get, id=play_obj.id)

    def test_user_deletion(self):
        """Verify that a Manager registration is deleted along with its user"""
        user_obj = User.objects.get(username="testplayer")
        # Create a Manager registration
        team_obj = Team.objects.create(name="La Team Test", tournament=None)
        man_obj = Manager.objects.create(team=team_obj, user=user_obj)

        # Test
        Manager.objects.get(id=man_obj.id)

        user_obj.delete()

        self.assertRaises(Manager.DoesNotExist, Manager.objects.get, id=man_obj.id)
