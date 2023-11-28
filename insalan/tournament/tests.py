"""Tournament Module Tests"""

from decimal import Decimal
from io import BytesIO
from types import NoneType

from django.db.utils import IntegrityError
from django.contrib.auth.models import Permission
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.urls import reverse

from insalan.tournament.models import (
    PaymentStatus,
    Player,
    Manager,
    Substitute,
    Team,
    Tournament,
    Event,
    Game,
)
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
        evobj_one = Event.objects.create(
            name="InsaLan", year=2023, month=9, ongoing=True
        )
        Event.objects.create(name="InsaLan", year=2023, month=10)
        evobj_two = Event.objects.create(
            name="InsaLan", year=2023, month=11, ongoing=True
        )

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

    @staticmethod
    def create_event_logo(file_name: str = "event-test.png") -> SimpleUploadedFile:
        """Create a logo for event tests"""
        test_img = BytesIO(f"test-image called {file_name}".encode("utf-8"))
        test_img.name = file_name
        return SimpleUploadedFile(test_img.name, test_img.getvalue())

    def test_logo_extension_enforcement(self):
        """Verify that we only accept logos as PNG, JPG, JPEG and SVG"""
        ev_obj = Event.objects.create(
            name="Insalan Test", year=2023, month=2, description=""
        )

        # PNGs work
        test_png = __class__.create_event_logo("event-test.png")
        ev_obj.logo = test_png
        ev_obj.full_clean()

        # JPGs work
        test_jpg = __class__.create_event_logo("event-test.jpg")
        ev_obj.logo = test_jpg
        ev_obj.full_clean()

        # JPEGs work
        test_jpeg = __class__.create_event_logo("event-test.jpeg")
        ev_obj.logo = test_jpeg
        ev_obj.full_clean()

        # SVGs work
        test_svg = __class__.create_event_logo("event-test.svg")
        ev_obj.logo = test_svg
        ev_obj.full_clean()

        # Others won't
        for ext in ["mkv", "txt", "md", "php", "exe", "zip", "7z"]:
            test_icon = __class__.create_event_logo(f"event-test.{ext}")
            ev_obj.logo = test_icon
            self.assertRaises(ValidationError, ev_obj.full_clean)


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
        Tournament.objects.create(name="Tourney 1", game=game_one, event=event)
        Tournament.objects.create(name="Tourney 2", game=game_two, event=event)
        Tournament.objects.create(name="Tourney 3", game=game_three, event=event)
        Tournament.objects.create(name="Tourney 4", game=game_three, event=event_two)

    def test_tournament_null_event(self):
        """Test failure of creation of a Tournament with no event"""
        game = Game.objects.create(name="Test")
        self.assertRaises(
            IntegrityError, Tournament.objects.create, event=None, game=game
        )

    def test_tournament_null_game(self):
        """Test failure of creation of a Tournament with no game"""
        event = Event.objects.create(name="Test", year=2023, month=2, description="")
        self.assertRaises(
            IntegrityError, Tournament.objects.create, event=event, game=None
        )

    def test_manager_player_duplication(self):
        """Verify that a user cannot be a manager and a player on the same tournament"""
        event = Event.objects.create(name="Test", year=2023, month=2, description="")
        game_obj = Game.objects.create(name="Game 1", short_name="G1")
        tourney_one = Tournament.objects.create(
            name="Tourney 1", game=game_obj, event=event
        )
        tourney_two = Tournament.objects.create(
            name="Tourney 2", game=game_obj, event=event
        )

        # This should work (Player in tourney 1, Manager in Tourney 2)
        user_one = User.objects.create_user(
            username="user_test_one", email="user_test_one@example.com"
        )

        Player.objects.create(
            user=user_one,
            team=Team.objects.create(name="Team One", tournament=tourney_one, password=make_password("teamonepwd")),
        )
        Manager.objects.create(
            user=user_one,
            team=Team.objects.create(name="Team Two", tournament=tourney_two, password=make_password("teamtwopwd")),
        )

        # This should not work (Player and Manager in tourney 1 in different teams)
        user_two = User.objects.create_user(
            username="user_test_two", email="user_test_two@example.com"
        )
        team_three = Team.objects.create(name="Team Three", tournament=tourney_one, password=make_password("teamthreepwd"))
        team_four = Team.objects.create(name="Team Four", tournament=tourney_one, password=make_password("teamfourpwd"))

        Player.objects.create(user=user_two, team=team_three)
        man_obj = Manager.objects.create(user=user_two, team=team_four)
        self.assertRaises(ValidationError, man_obj.full_clean)

        user_three = User.objects.create_user(
            username="user_test_three", email="user_test_three@example.com"
        )

        Manager.objects.create(user=user_three, team=team_three)
        play_obj = Player.objects.create(user=user_three, team=team_four)
        self.assertRaises(ValidationError, play_obj.full_clean)

        # This should not work (Player and Manager in tourney 1 in the same team)
        team_five = Team.objects.create(name="Team Five", tournament=tourney_one, password=make_password("teamfivepwd"))

        user_four = User.objects.create_user(
            username="user_test_four", email="user_test_four@example.com"
        )
        Player.objects.create(user=user_four, team=team_five)
        self.assertRaises(
            ValidationError,
            Manager.objects.create(user=user_four, team=team_five).full_clean,
        )

        user_five = User.objects.create_user(
            username="user_test_five", email="user_test_five@example.com"
        )
        Manager.objects.create(user=user_five, team=team_five)
        self.assertRaises(
            ValidationError,
            Player.objects.create(user=user_five, team=team_five).full_clean,
        )

    def test_substitute_player_duplication(self):
        """Verify that a user cannot be a substitute and a player on the same tournament"""
        event = Event.objects.create(name="Test", year=2023, month=2, description="")
        game_obj = Game.objects.create(name="Game 1", short_name="G1")
        tourney_one = Tournament.objects.create(
            name="Tourney 1", game=game_obj, event=event
        )
        tourney_two = Tournament.objects.create(
            name="Tourney 2", game=game_obj, event=event
        )

        # This should work (Player in tourney 1, Substitute in Tourney 2)
        user_one = User.objects.create_user(
            username="user_test_one", email="user_test_one@example.com"
        )

        Player.objects.create(
            user=user_one,
            team=Team.objects.create(name="Team One", tournament=tourney_one, password=make_password("teamonepwd")),
        )
        Substitute.objects.create(
            user=user_one,
            team=Team.objects.create(name="Team Two", tournament=tourney_two, password=make_password("teamtwopwd")),
        )

        # This should not work (Player and Manager in tourney 1 in different teams)
        user_two = User.objects.create_user(
            username="user_test_two", email="user_test_two@example.com"
        )
        team_three = Team.objects.create(name="Team Three", tournament=tourney_one, password=make_password("teamthreepwd"))
        team_four = Team.objects.create(name="Team Four", tournament=tourney_one, password=make_password("teamfourpwd"))

        Player.objects.create(user=user_two, team=team_three)
        man_obj = Substitute.objects.create(user=user_two, team=team_four)
        self.assertRaises(ValidationError, man_obj.full_clean)

        user_three = User.objects.create_user(
            username="user_test_three", email="user_test_three@example.com"
        )

        Substitute.objects.create(user=user_three, team=team_three)
        play_obj = Player.objects.create(user=user_three, team=team_four)
        self.assertRaises(ValidationError, play_obj.full_clean)

        # This should not work (Player and Substitute in tourney 1 in the same team)
        team_five = Team.objects.create(name="Team Five", tournament=tourney_one, password=make_password("teamfivepwd"))

        user_four = User.objects.create_user(
            username="user_test_four", email="user_test_four@example.com"
        )
        Player.objects.create(user=user_four, team=team_five)
        self.assertRaises(
            ValidationError,
            Substitute.objects.create(user=user_four, team=team_five).full_clean,
        )

        user_five = User.objects.create_user(
            username="user_test_five", email="user_test_five@example.com"
        )
        Substitute.objects.create(user=user_five, team=team_five)
        self.assertRaises(
            ValidationError,
            Player.objects.create(user=user_five, team=team_five).full_clean,
        )

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
        team_one = Team.objects.create(name="Ohlala", tournament=tourney, password=make_password("ohlalapwd"))
        team_two = Team.objects.create(name="OhWow", tournament=tourney, password=make_password("ohwowpwd"))
        team_three = Team.objects.create(name="LeChiengue", tournament=tourney_two, password=make_password("lechienguepwd"))

        teams = tourney.get_teams()
        self.assertEqual(2, len(teams))
        self.assertTrue(team_one in teams)
        self.assertTrue(team_two in teams)
        self.assertFalse(team_three in teams)

    def test_default_cashprizes(self):
        """Test that the default for cashprizes is an empty list"""
        tourney = Tournament.objects.all()[0]
        self.assertEqual([], tourney.cashprizes)

    def test_get_set_cashprizes(self):
        """Verify that getting and setting cashprizes is possible"""
        tourney = Tournament.objects.all()[0]

        # One price
        tourney.cashprizes = [Decimal(28)]
        tourney.save()
        self.assertEqual(1, len(tourney.cashprizes))
        self.assertEqual(Decimal(28), tourney.cashprizes[0])

        # Many prices
        tourney.cashprizes = [Decimal(18), Decimal(22), Decimal(89)]
        tourney.save()
        self.assertEqual(3, len(tourney.cashprizes))
        self.assertEqual(Decimal(18), tourney.cashprizes[0])
        self.assertEqual(Decimal(22), tourney.cashprizes[1])
        self.assertEqual(Decimal(89), tourney.cashprizes[2])

        # Back to zero
        tourney.cashprizes = []
        tourney.save()
        self.assertEqual(0, len(tourney.cashprizes))

    def test_cashprizes_cannot_be_strictly_negative(self):
        """Test that a cashprize cannot be strictly negative"""
        tourney = Tournament.objects.all()[0]

        tourney.cashprizes = [Decimal(278), Decimal(-1), Decimal(0)]
        self.assertRaises(ValidationError, tourney.full_clean)

        tourney.cashprizes = [Decimal(278), Decimal(0), Decimal(0)]
        tourney.full_clean()

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

        self.assertRaises(
            Tournament.DoesNotExist, Tournament.objects.get, id=tourney.id
        )

    def test_event_deletion_cascade(self):
        """Verify that a tournament is deleted when its event is"""
        tourney = Tournament.objects.all()[0]
        ev_obj = tourney.game

        Tournament.objects.get(id=tourney.id)

        # Delete and verify
        ev_obj.delete()

        self.assertRaises(
            Tournament.DoesNotExist, Tournament.objects.get, id=tourney.id
        )

    @staticmethod
    def create_tourney_logo(file_name: str = "tourney-test.png") -> SimpleUploadedFile:
        """Create a logo for tournament tests"""
        test_img = BytesIO(f"test-image called {file_name}".encode("utf-8"))
        test_img.name = file_name
        return SimpleUploadedFile(test_img.name, test_img.getvalue())

    def test_logo_extension_enforcement(self):
        """Verify that we only accept logos as PNG, JPG, JPEG and SVG"""
        tourney = Tournament.objects.all()[0]

        # PNGs work
        test_png = __class__.create_tourney_logo("tourney-test.png")
        tourney.logo = test_png
        tourney.full_clean()

        # JPGs work
        test_jpg = __class__.create_tourney_logo("tourney-test.jpg")
        tourney.logo = test_jpg
        tourney.full_clean()

        # JPEGs work
        test_jpeg = __class__.create_tourney_logo("tourney-test.jpeg")
        tourney.logo = test_jpeg
        tourney.full_clean()

        # SVGs work
        test_svg = __class__.create_tourney_logo("tourney-test.svg")
        tourney.logo = test_svg
        tourney.full_clean()

        # Others won't
        for ext in ["mkv", "txt", "md", "php", "exe", "zip", "7z"]:
            test_icon = __class__.create_tourney_logo(f"tourney-test.{ext}")
            tourney.logo = test_icon
            self.assertRaises(ValidationError, tourney.full_clean)

    def test_rules_size_limit(self):
        """
        Check that the rules of a tournament can overflow the limit.

        This is a consequence of the way `max_length` is enforced in `TextField`
        fields, i.e. not. It is only enforced on the text area for the input,
        but not the database.

        See: https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.TextField
        """
        tourney = Tournament.objects.all()[0]

        tourney.rules = "C" * 50001
        tourney.full_clean()

    def test_product_creation(self):
        event_one = Event.objects.create(
            name="Insalan Test One", year=2023, month=2, description=""
        )

        game = Game.objects.create(name="Fortnite")

        trnm_one = Tournament.objects.create(
            event=event_one, game=game, player_price_online=23.3, manager_price_online=3, substitute_price_online=3
        )
        self.assertEqual(trnm_one.player_price_online, 23.3)

        self.assertEqual(trnm_one.manager_price_online, 3)

        self.assertEqual(trnm_one.substitute_price_online, 3)


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

        jeanmich: User = User.objects.create_user(
            username="jeanmich",
            email="jeanmicheldu46@zzz.com",
            password="password",
            first_name="Jean-Michel",
            last_name="Dupont",
        )

        event_one = Event.objects.create(
            name="Insalan Test One", year=2023, month=2, description=""
        )

        game = Game.objects.create(
            name="Fortnite",
            substitute_players_per_team=1,
        )

        trnm_one = Tournament.objects.create(
            event=event_one, 
            game=game,
            is_announced=True,
            maxTeam = 10
        )
        trnm_two = Tournament.objects.create(
            event=event_one, 
            game=game,
            is_announced=True,
            maxTeam = 10
        )

        team_lalooze: Team = Team.objects.create(
        name="LaLooze", tournament=trnm_one, password=make_password("laloozepwd"))

        team_lapouasse: Team = Team.objects.create(
        name="LaPouasse", tournament=trnm_two, password=make_password("lapouassepwd")
        )

        Player.objects.create(user=robert, team=team_lalooze)
        Player.objects.create(user=didier, team=team_lalooze)
        Player.objects.create(user=gege, team=team_lapouasse)
        Manager.objects.create(user=didier, team=team_lapouasse)

        Substitute.objects.create(user=jeanmich, team=team_lalooze)

    def test_team_get_full(self):
        """Get the fields of a Team"""
        team = Team.objects.get(name="LaLooze")
        self.assertIsNotNone(team)

        self.assertEqual("LaLooze", team.get_name())
        self.assertIsInstance(team.get_tournament(), Tournament)
        self.assertEqual(2, len(team.get_players()))
        self.assertEqual(0, len(team.get_managers()))
        self.assertEqual(1, len(team.get_substitutes()))

        team = Team.objects.get(name="LaPouasse")
        self.assertIsNotNone(team)

        self.assertEqual("LaPouasse", team.get_name())
        self.assertIsInstance(team.get_tournament(), Tournament)
        self.assertEqual(1, len(team.get_players()))
        self.assertEqual(1, len(team.get_managers()))
        self.assertEqual(0, len(team.get_substitutes()))

    def test_payment_status_default(self):
        """Verify what the default status of payment on a new player is"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        play_reg = Player.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, play_reg.payment_status)

    def test_payment_status_set(self):
        """Verify that we can set a status for a Player at any point"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        play_reg = Player.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, play_reg.payment_status)

        play_reg.payment_status = PaymentStatus.PAY_LATER

        self.assertEqual(PaymentStatus.PAY_LATER, play_reg.payment_status)

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
        self.assertRaises(
            IntegrityError, Team.objects.create, name="LaLooze", tournament=tourney, password=make_password("laloozepwd")
        )

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
        team_one: Team = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("password"))

        # Second edition
        event_two = Event.objects.create(
            name="InsaLan Test (Past)", year=2023, month=3, description=""
        )
        trnm_two = Tournament.objects.create(game=game, event=event_two)
        team_two: Team = Team.objects.create(
            name="La Team Test Passée", tournament=trnm_two, password=make_password("password2")
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
        Player.objects.create(team=team_one, user=user_one, name_in_game="playerOne")
        Player.objects.create(team=team_one, user=another_player, name_in_game="PlayerTwo")
        Player.objects.create(team=team_two, user=another_player, name_in_game="RandomKiller")

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
        team = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))

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
        team = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))

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
        team = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm, password=make_password("lateamtest2pwd"))

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
        team = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two, password=make_password("lateamtest2pwd"))

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
        Player.objects.create(user=user, team=team, name_in_game="pseudo")

        # Try and register them in the same team
        player = Player.objects.create(user=user, team=team_two, name_in_game="pseudo")
        self.assertRaises(ValidationError, player.full_clean)

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
        event = Event.objects.get(year=2023, month=8)
        trnm = Tournament.objects.get(event=event)
        # Create a team and player
        team_obj = Team.objects.create(name="La Team Test Player", tournament=trnm)
        play_obj = Player.objects.create(team=team_obj, user=user_obj, name_in_game="pseudo")

        Player.objects.get(id=play_obj.id)

        # Delete and verify
        team_obj.delete()

        self.assertRaises(Player.DoesNotExist, Player.objects.get, id=play_obj.id)

    def test_user_deletion(self):
        """Verify that a Player registration is deleted along with its user"""
        user_obj = User.objects.get(username="testplayer")
        event = Event.objects.get(year=2023, month=8)
        trnm = Tournament.objects.get(event=event)
        # Create a Player registration
        team_obj = Team.objects.create(name="La Team Test User", tournament=trnm)
        play_obj = Player.objects.create(team=team_obj, user=user_obj, name_in_game="pseudo")

        # Test
        Player.objects.get(id=play_obj.id)

        user_obj.delete()

        self.assertRaises(Player.DoesNotExist, Player.objects.get, id=play_obj.id)


# TODO: Add tests of the API


class TournamentFullDerefEndpoint(TestCase):
    """Test the endpoint that fully dereferences everything about a tournament"""

    def test_not_found(self):
        """Test what happens on a tournament not found"""
        candidates = Tournament.objects.all().values_list("id", flat=True)
        if len(candidates) == 0:
            candidates = [1]
        not_used = max(candidates) + 1

        request = self.client.get(
            f"/v1/tournament/tournament/{not_used}/full", format="sjon"
        )
        self.assertEqual(request.status_code, 404)

    def test_example(self):
        """Test a simple example"""
        uobj_one = User.objects.create(
            username="test_user_one", email="one@example.com"
        )
        uobj_two = User.objects.create(
            username="test_user_two", email="two@example.com"
        )
        uobj_three = User.objects.create(
            username="test_user_three", email="three@example.com"
        )
        uobj_four = User.objects.create(
            username="test_user_four", email="four@example.com"
        )

        game_obj = Game.objects.create(name="Test Game", short_name="TFG")

        evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        tourneyobj_one = Tournament.objects.create(
            event=evobj,
            name="Test Tournament",
            rules="have fun!",
            game=game_obj,
            is_announced=True,
        )
        team_one = Team.objects.create(name="Team One", tournament=tourneyobj_one)
        Player.objects.create(user=uobj_one, team=team_one, name_in_game="playerone")
        Player.objects.create(user=uobj_two, team=team_one, name_in_game="playertwo")
        Manager.objects.create(user=uobj_three, team=team_one)
        Substitute.objects.create(user=uobj_four, team=team_one, name_in_game="substitute")

        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)
        model = {
            "id": tourneyobj_one.id,
            "event": {
                "id": evobj.id,
                "name": "Test Event",
                "description": "This is a test",
                "year": 2021,
                "month": 12,
                "ongoing": False,
                "logo": None,
            },
            "game": {
                "id": game_obj.id, 
                "name": "Test Game", 
                "short_name": "TFG", 
                "players_per_team": 1, 
                "substitute_players_per_team": 0,
            },
            "name": "Test Tournament",
            "rules": "have fun!",
            "is_announced": True,
            "maxTeam": tourneyobj_one.maxTeam,
            # I don't know what's happenin with timezones here
            "registration_open": timezone.make_aware(
                timezone.make_naive(tourneyobj_one.registration_open)
            ).isoformat(),
            "registration_close": timezone.make_aware(
                timezone.make_naive(tourneyobj_one.registration_close)
            ).isoformat(),
            "player_price_online": "0.00",
            "player_price_onsite": "0.00",
            "manager_price_online": "0.00",
            "manager_price_onsite": "0.00",
            "substitute_price_online": "0.00",
            "substitute_price_onsite": "0.00",
            "cashprizes": [],
            "player_online_product": tourneyobj_one.player_online_product.id,
            "manager_online_product": tourneyobj_one.manager_online_product.id,
            "substitute_online_product": tourneyobj_one.substitute_online_product.id,
            "teams": [
                {
                    "id": team_one.id,
                    "name": "Team One",
                    "players": [
                        {"user": "test_user_one", "name_in_game": "playerone"},
                        {"user": "test_user_two", "name_in_game": "playertwo"},
                    ],
                    "managers": [
                        "test_user_three",
                    ],
                    "substitutes": [
                        {"user": "test_user_four", "name_in_game": "substitute"},
                    ],
                    "validated": team_one.validated,
                }
            ],
            "logo": None,
            "validated_teams": 0,
            "description": "",
            "casters": [],
        }

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)

    def test_not_announced(self):
        """Test if a tournament hasn't been yet announced"""
        uobj_one = User.objects.create(
            username="test_user_one", email="one@example.com"
        )
        uobj_two = User.objects.create(
            username="test_user_two", email="two@example.com"
        )
        uobj_three = User.objects.create(
            username="test_user_three", email="three@example.com"
        )

        game_obj = Game.objects.create(name="Test Game", short_name="TFG")

        evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        tourneyobj_one = Tournament.objects.create(
            event=evobj,
            name="Test Tournament",
            rules="have fun!",
            game=game_obj,
            is_announced=False,
        )
        team_one = Team.objects.create(name="Team One", tournament=tourneyobj_one, password=make_password("strongpwd"))
        Player.objects.create(user=uobj_one, team=team_one)
        Player.objects.create(user=uobj_two, team=team_one)
        Manager.objects.create(user=uobj_three, team=team_one)
        Substitute.objects.create(user=uobj_three, team=team_one)

        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            request.data,
            {
                "id": tourneyobj_one.id,
                "is_announced": False,
            },
        )


class EventDerefAndGroupingEndpoints(TestCase):
    """Test endpoints for dereferencing/fetching grouped events"""

    @staticmethod
    def create_multiple_events():
        """Create some of events"""
        Event.objects.create(name="Event 1", year=2018, month=8)
        Event.objects.create(name="Event 2", year=2019, month=3)
        Event.objects.create(name="Event 3", year=2019, month=7)
        Event.objects.create(name="Event 4", year=2021, month=11)

    def test_year_group_empty(self):
        """Test what happens when events are in the database but we query an empty year"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/2020", format="json")

        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.data), 0)

    def test_year_one_found(self):
        """Test what happens when one event is found"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/2018", format="json")

        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.data), 1)

    def test_year_two_found(self):
        """Test what happens when multiple events are found"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/2019", format="json")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.data), 2)

    def test_year_garbage(self):
        """Test that if you put anything but a year it's not recognized"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/00d1686a", format="json")
        self.assertEqual(request.status_code, 404)

    def test_deref_not_found(self):
        """Test what happens on a not found event"""
        not_assigned_list = Event.objects.all().values_list("id", flat=True)
        if len(not_assigned_list) == 0:
            not_assigned_list = [1]
        not_assigned = max(not_assigned_list) + 1
        request = self.client.get(
            f"/v1/tournament/event/{not_assigned}/tournaments", format="json"
        )

        self.assertEqual(request.status_code, 404)

    def test_deref_not_announced(self):
        """Test a simple example of a dereference"""
        evobj = Event.objects.create(name="Test", year=2023, month=3, ongoing=True)
        gobj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(
            name="Test Tournament",
            game=gobj,
            event=evobj,
            rules="have fun!",
            is_announced=False,
        )

        request = self.client.get(
            f"/v1/tournament/event/{evobj.id}/tournaments", format="json"
        )

        self.assertEqual(request.status_code, 200)

        model = {
            "id": evobj.id,
            "name": "Test",
            "description": "",
            "year": 2023,
            "month": 3,
            "ongoing": True,
            "tournaments": [
                {
                    "id": tourney.id,
                    "is_announced": False,
                }
            ],
            "logo": None,
        }
        self.assertEqual(request.data, model)

    def test_deref(self):
        """Test a simple example of a dereference"""
        evobj = Event.objects.create(name="Test", year=2023, month=3, ongoing=True)
        gobj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(
            name="Test Tournament",
            game=gobj,
            event=evobj,
            rules="have fun!",
            is_announced=True,
        )

        request = self.client.get(
            f"/v1/tournament/event/{evobj.id}/tournaments", format="json"
        )

        self.assertEqual(request.status_code, 200)

        model = {
            "id": evobj.id,
            "name": "Test",
            "description": "",
            "year": 2023,
            "month": 3,
            "ongoing": True,
            "tournaments": [
                {
                    "id": tourney.id,
                    "teams": [],
                    "validated_teams": 0,
                    "name": "Test Tournament",
                    "is_announced": True,
                    "maxTeam": tourney.maxTeam,
                    "rules": "have fun!",
                    "registration_open": timezone.make_aware(
                        timezone.make_naive(tourney.registration_open)
                    ).isoformat(),
                    "registration_close": timezone.make_aware(
                        timezone.make_naive(tourney.registration_close)
                    ).isoformat(),
                    "logo": None,
                    "player_price_online": "0.00",
                    "player_price_onsite": "0.00",
                    "manager_price_online": "0.00",
                    "manager_price_onsite": "0.00",
                    "substitute_price_online": "0.00",
                    "substitute_price_onsite": "0.00",
                    "cashprizes": [],
                    "game": gobj.id,
                    "manager_online_product": tourney.manager_online_product.id,
                    "substitute_online_product": tourney.substitute_online_product.id,
                    "player_online_product": tourney.player_online_product.id,
                    "description": "",
                    "casters": [],
                }
            ],
            "logo": None,
        }
        self.assertEqual(request.data, model)


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
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))

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
        trnm = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        manager = Manager(user=fella, team=team_one)
        manager.full_clean()
        manager.save()
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
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm, password=make_password("lateamtest2pwd"))

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        man2 = Manager.objects.create(user=fella, team=team_two)

        self.assertRaises(ValidationError, man2.full_clean)

    def test_one_manager_many_teams_same_event_diff_tournament_diff_team(self):
        """Test the collision of duplicate managers"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        trnm_two = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two, password=make_password("lateamtest2pwd"))

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        man = Manager(user=fella, team=team_one)
        man.full_clean()
        man.save()
        man2 = Manager.objects.create(user=fella, team=team_two)

        self.assertRaises(ValidationError, man2.full_clean)


    def test_one_manager_many_teams_diff_event_diff_tournament_diff_team(self):
        """Test the non collision of duplicate managers in different teams
        of different tournament of different event"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        event_two = Event.objects.create(
            name="InsaLan Test", year=2023, month=2, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        trnm_two = Tournament.objects.create(
            game=game, 
            event=event_two,
            is_announced=True,
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two)

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        man = Manager(user=fella, team=team_one)
        man.full_clean()
        man.save()
        man2 = Manager(user=fella, team=team_two)
        man2.full_clean()

    def test_manager_team_deletion(self):
        """Verify the behaviour of a Manager when their team gets deleted"""
        user_obj = User.objects.get(username="testplayer")
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        # Create a team and player
        team_obj = Team.objects.create(name="La Team Test", tournament=trnm)
        play_obj = Manager.objects.create(team=team_obj, user=user_obj)

        Manager.objects.get(id=play_obj.id)

        # Delete and verify
        team_obj.delete()

        self.assertRaises(Manager.DoesNotExist, Manager.objects.get, id=play_obj.id)

    def test_user_deletion(self):
        """Verify that a Manager registration is deleted along with its user"""
        user_obj = User.objects.get(username="testplayer")
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(
            game=game, event=event
        )  # Create a Manager registration
        team_obj = Team.objects.create(name="La Team Test", tournament=trnm)
        man_obj = Manager.objects.create(team=team_obj, user=user_obj)

        # Test
        Manager.objects.get(id=man_obj.id)

        user_obj.delete()

        self.assertRaises(Manager.DoesNotExist, Manager.objects.get, id=man_obj.id)

    def test_payment_status_default(self):
        """Verify what the default status of payment on a new manager is"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        man_reg = Manager.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, man_reg.payment_status)

    def test_payment_status_set(self):
        """Verify that we can set a status for a Manager at any point"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        man_reg = Manager.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, man_reg.payment_status)

        man_reg.payment_status = PaymentStatus.PAY_LATER

        self.assertEqual(PaymentStatus.PAY_LATER, man_reg.payment_status)


# Substitute Class Tests
class SubstituteTestCase(TestCase):
    """Substitute Unit Test Class"""

    def setUp(self):
        """Setup method for Substitute Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=3, description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = Tournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))

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
        Substitute.objects.create(team=team_one, user=random_player, name_in_game="pseudo")

    def test_get_user_of_substitute(self):
        """Check the conversion between user and substitute"""
        user = User.objects.get(username="randomplayer")

        substitutes = Substitute.objects.filter(user=user)
        self.assertEqual(1, len(substitutes))

        found_user = substitutes[0].as_user()
        self.assertEqual(found_user, user)

        self.assertEquals(found_user.get_username(), "randomplayer")
        self.assertEquals(found_user.get_short_name(), "Random")
        self.assertEquals(found_user.get_full_name(), "Random Player")
        self.assertEquals(found_user.get_user_permissions(), set())
        self.assertTrue(found_user.has_usable_password())
        self.assertTrue(found_user.check_password("IUseAVerySecurePassword"))
        self.assertTrue(found_user.is_active)
        self.assertFalse(found_user.is_staff)

    def test_get_substitute_team_not_none(self):
        """Check that a substitute gives a non null team"""
        user = User.objects.get(username="randomplayer")

        substitutes = Substitute.objects.filter(user=user)
        self.assertEqual(1, len(substitutes))
        substitute = substitutes[0]

        team = substitute.get_team()
        self.assertIsNotNone(team)

    def test_not_substitutes(self):
        """Check that a non-substitute cannot become substitutes"""
        user = User.objects.get(username="testplayer")

        substitutes = Substitute.objects.filter(user=user)
        self.assertEqual(0, len(substitutes))

    def test_get_player_team_correct(self):
        """Check that a substitutes gives the correct team"""
        user = User.objects.get(username="randomplayer")
        event = Event.objects.get(year=2023, month=3)
        trnm = Tournament.objects.get(event=event)

        substitutes = Substitute.objects.filter(user=user)
        self.assertEqual(1, len(substitutes))
        substitute = substitutes[0]

        team = substitute.get_team()
        self.assertIsNotNone(team)

        self.assertEquals(team.get_name(), "La Team Test")
        self.assertEquals(team.get_tournament(), trnm)

    def test_one_substitute_many_teams_same_event_same_tournament_same_team(self):
        """Test the collision of duplicate substitutes"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        substitute = Substitute(user=fella, team=team_one, name_in_game="pseudo")
        substitute.full_clean()
        substitute.save()
        self.assertRaises(
            IntegrityError, Substitute.objects.create, user=fella, team=team_one
        )

    def test_one_substitute_many_teams_same_event_same_tournament_diff_team(self):
        """Test the collision of duplicate substitutes"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = Tournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm, password=make_password("lateamtest2pwd"))

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        man2 = Substitute.objects.create(user=fella, team=team_two)

        self.assertRaises(ValidationError, man2.full_clean)

    def test_one_substitute_many_teams_same_event_diff_tournament_diff_team(self):
        """Test the collision of duplicate substitutes"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        trnm_two = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("lateamtestpwd"))
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two, password=make_password("lateamtest2pwd"))

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        man = Substitute(user=fella, team=team_one, name_in_game="pseudo")
        man.full_clean()
        man.save()
        man2 = Substitute.objects.create(user=fella, team=team_two, name_in_game="pseudo2")

        self.assertRaises(ValidationError, man2.full_clean)


    def test_one_substitute_many_teams_diff_event_diff_tournament_diff_team(self):
        """Test the non collision of duplicate substitutes in different teams
        of different tournament of different event"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        event_two = Event.objects.create(
            name="InsaLan Test", year=2023, month=2, description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = Tournament.objects.create(
            game=game, 
            event=event,
            is_announced=True,
        )
        trnm_two = Tournament.objects.create(
            game=game, 
            event=event_two,
            is_announced=True,
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm)
        team_two = Team.objects.create(name="La Team Test 2", tournament=trnm_two)

        fella = User.objects.create_user(
            username="fella",
            email="fella@example.net",
            password="IUseAVerySecurePassword",
            first_name="Hewwo",
            last_name="Nya",
        )

        man = Substitute(user=fella, team=team_one, name_in_game="pseudo")
        man.full_clean()
        man.save()
        man2 = Substitute(user=fella, team=team_two, name_in_game="pseudo2")
        man2.full_clean()

    def test_substitute_team_deletion(self):
        """Verify the behaviour of a substitute when their team gets deleted"""
        user_obj = User.objects.get(username="testplayer")
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(game=game, event=event)
        # Create a team and player
        team_obj = Team.objects.create(name="La Team Test", tournament=trnm)
        play_obj = Substitute.objects.create(team=team_obj, user=user_obj)

        Substitute.objects.get(id=play_obj.id)

        # Delete and verify
        team_obj.delete()

        self.assertRaises(Substitute.DoesNotExist, Substitute.objects.get, id=play_obj.id)

    def test_user_deletion(self):
        """Verify that a substitute registration is deleted along with its user"""
        user_obj = User.objects.get(username="testplayer")
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = Tournament.objects.create(
            game=game, event=event
        )  # Create a substitute registration
        team_obj = Team.objects.create(name="La Team Test", tournament=trnm)
        man_obj = Substitute.objects.create(team=team_obj, user=user_obj)

        # Test
        Substitute.objects.get(id=man_obj.id)

        user_obj.delete()

        self.assertRaises(Substitute.DoesNotExist, Substitute.objects.get, id=man_obj.id)

    def test_payment_status_default(self):
        """Verify what the default status of payment on a new substitute is"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        man_reg = Substitute.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, man_reg.payment_status)

    def test_payment_status_set(self):
        """Verify that we can set a status for a Substitute at any point"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        man_reg = Substitute.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, man_reg.payment_status)

        man_reg.payment_status = PaymentStatus.PAY_LATER

        self.assertEqual(PaymentStatus.PAY_LATER, man_reg.payment_status)


class TournamentTeamEndpoints(TestCase):
    """Tournament Registration Endpoint Test Class"""

    # TODO Test all endpoints

    def setUp(self):
        """Setup method for Tournament Registrations Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=3, description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = Tournament.objects.create(
            game=game, 
            event=event, 
            maxTeam=16,
            is_announced=True
        )
        team_one = Team.objects.create(name="La Team Test", tournament=trnm, password=make_password("password"))

        # user_one = User.objects.create_user(
        #     username="testplayer",
        #     email="player.user.test@insalan.fr",
        #     password="^ThisIsAnAdminPassword42$",
        #     first_name="Iam",
        #     last_name="Staff",
        # )

        invalid_email_user: User = User.objects.create_user(
            username="invalidemail",
            email="randomplayer@gmail.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
        )

        valid_email_user: User = User.objects.create_user(
            username="validemail",
            password="ThisIsPassword",
        )

        valid_email_user.set_email_active()

        # Player.objects.create(team=team_one, user=user_one)
        # Player.objects.create(team=team_one, user=another_player)
        # Manager.objects.create(team=team_one, user=random_player)

    def test_can_create_a_team_with_valid_email(self):
        """Try to create a team with a valid email"""
        user: User = User.objects.get(username="validemail")
        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        request = self.client.post(
            "/v1/tournament/team/",
            {
                "name": "Les emails valides",
                "tournament": trnm.id,
                "password": "password",
            },
            format="json",
        )

        self.assertEquals(request.status_code, 201)

    def test_cant_create_a_team_with_no_valid_email(self):
        """Try to create a team with email not validated"""
        user: User = User.objects.get(username="invalidemail")
        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        request = self.client.post(
            "/v1/tournament/team/",
            {
                "name": "Flemme de valider",
                "tournament": trnm.id,
                "password":"Password123!"
            },
            format="json",
        )

        self.assertEquals(request.status_code, 403)

    def test_can_join_a_team_with_a_valid_email(self):
        """Try to join an existing team with a valid email"""
        user: User = User.objects.get(username="validemail")
        self.client.force_login(user=user)
        team: Team = Team.objects.get(name="La Team Test")

        request = self.client.post(
            "/v1/tournament/player/",
            {
                "team": team.id,
                "password": "password",
                "name_in_game":"pseudo",
            },
            format="json",
        )
        self.assertEquals(request.status_code, 201)

        Player.objects.filter(user=user.id).delete()

        request = self.client.post(
            "/v1/tournament/manager/",
            {
                "team": team.id,
                "password":"password",
            },
            format="json",
        )
        self.assertEquals(request.status_code, 201)

        Manager.objects.filter(user=user.id).delete()

        request = self.client.post(
            "/v1/tournament/substitute/",
            {
                "team": team.id,
                "password": "password",
                "name_in_game":"pseudo",
            },
            format="json",
        )
        self.assertEquals(request.status_code, 201)


    def test_cant_join_a_team_with_no_valid_email(self):
        """Try to join an existing team with no valid email"""
        user: User = User.objects.get(username="invalidemail")
        self.client.force_login(user=user)
        team: Team = Team.objects.get(name="La Team Test")

        request = self.client.post(
            "/v1/tournament/player/",
            {
                "team": team.id,
                "password": "Password123!",
                "name_in_game":"pseudo",
            },
            format="json",
        )
        self.assertEquals(request.status_code, 403)

        request = self.client.post(
            "/v1/tournament/manager/",
            {
                "team": user.id,
                "password":"Password123!",
            },
            format="json",
        )
        self.assertEquals(request.status_code, 403)

        request = self.client.post(
            "/v1/tournament/substitute/",
            {
                "team": team.id,
                "password": "Password123!",
                "name_in_game":"pseudo",
            },
            format="json",
        )
        self.assertEquals(request.status_code, 403)


class TournamentMeTests(TestCase):
    def setUp(self):
        self.usrobj = User.objects.create_user(
            username="randomplayer",
            email="randomplayer@example.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
            is_active=True,
        )
        self.evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        self.game_obj = Game.objects.create(name="Test Game", short_name="TFG")
        self.tourneyobj_one = Tournament.objects.create(
            event=self.evobj,
            name="Test Tournament",
            rules="have fun!",
            game=self.game_obj,
            is_announced=True,
        )
        self.team_one = Team.objects.create(name="Team One", tournament=self.tourneyobj_one, password=make_password("password"))
        self.plobjt = Player.objects.create(
            user_id=self.usrobj.id,
            team=self.team_one, 
            name_in_game="pseudo"
        )

        self.team_two = Team.objects.create(name="Team Two", tournament=self.tourneyobj_one, password=make_password("password"))
        self.managojt = Manager.objects.create(
            user_id=self.usrobj.id,
            team=self.team_two
        )
        self.subobj = Substitute.objects.create(
            user_id=self.usrobj.id,
            team=self.team_two, 
            name_in_game="pseudo"
        )

    def test_get_tournament_me(self):
        self.client.login(username="randomplayer", password="IUseAVerySecurePassword")
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['player'][0]['name_in_game'], self.plobjt.name_in_game)
        self.assertEqual(response.data['player'][0]['team']['name'], self.team_one.name)
        self.assertEqual(response.data['player'][0]['team']['tournament']['name'], self.tourneyobj_one.name)
        self.assertEqual(response.data['player'][0]['team']['tournament']['event']['name'], self.evobj.name)

    def test_get_tournament_me_manager(self):
        self.client.login(username="randomplayer", password="IUseAVerySecurePassword")
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.data['manager'][0]['id'], self.managojt.id)
        self.assertEqual(response.data['manager'][0]['team']['name'], self.team_two.name)
        self.assertEqual(response.data['manager'][0]['team']['tournament']['name'], self.tourneyobj_one.name)
        self.assertEqual(response.data['manager'][0]['team']['tournament']['event']['name'], self.evobj.name)

    def test_get_tournament_me_substitute(self):
        self.client.login(username="randomplayer", password="IUseAVerySecurePassword")
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.data['substitute'][0]['name_in_game'], self.subobj.name_in_game)
        self.assertEqual(response.data['substitute'][0]['team']['name'], self.team_two.name)
        self.assertEqual(response.data['substitute'][0]['team']['tournament']['name'], self.tourneyobj_one.name)
        self.assertEqual(response.data['substitute'][0]['team']['tournament']['event']['name'], self.evobj.name)

    def test_get_tournament_me_unauthenticated(self):
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.status_code, 403)
