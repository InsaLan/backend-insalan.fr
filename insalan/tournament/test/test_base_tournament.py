"""BaseTournament Module Tests"""

from datetime import date
from io import BytesIO

from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase

from insalan.tournament.models import (
    Player,
    Manager,
    Substitute,
    Team,
    BaseTournament,
    EventTournament,
    Event,
    Game,
    PrivateTournament,
)
from insalan.user.models import User


class BaseTournamentTestCase(TestCase):
    """Tournament Tests"""

    def setUp(self) -> None:
        """Set up the Tournaments"""
        game_one = Game.objects.create(name="Test Game One")
        game_two = Game.objects.create(name="Test Game Two")
        game_three = Game.objects.create(name="Test Game Three")
        BaseTournament.objects.create(name="Tourney 1", game=game_one)
        BaseTournament.objects.create(name="Tourney 2", game=game_two)
        BaseTournament.objects.create(name="Tourney 3", game=game_three)
        BaseTournament.objects.create(name="Tourney 4", game=game_three)

    def test_tournament_null_game(self) -> None:
        """Test failure of creation of a Tournament with no game"""
        self.assertRaises(
            IntegrityError, BaseTournament.objects.create, game=None
        )

    def test_manager_player_duplication(self) -> None:
        """Verify that a user cannot be a manager and a player on the same tournament"""
        game_obj = Game.objects.create(name="Game 1", short_name="G1")
        event_obj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            date_start=date(2021,12,1),
            date_end=date(2021,12,2),
            ongoing=False,
        )
        tourney_one = EventTournament.objects.create(
            name="Tourney 1", game=game_obj, event=event_obj
        )
        tourney_two = EventTournament.objects.create(
            name="Tourney 2", game=game_obj, event=event_obj
        )

        # This should work (Player in tourney 1, Manager in Tourney 2)
        user_one = User.objects.create_user(
            username="user_test_one", email="user_test_one@example.com"
        )

        Player.objects.create(
            user=user_one,
            team=Team.objects.create(
                name="Team One",
                tournament=tourney_one,
                password=make_password("teamonepwd")
            ),
        )
        Manager.objects.create(
            user=user_one,
            team=Team.objects.create(
                name="Team Two",
                tournament=tourney_two,
                password=make_password("teamtwopwd"),
            ),
        )

        # This should not work (Player and Manager in tourney 1 in different teams)
        user_two = User.objects.create_user(
            username="user_test_two", email="user_test_two@example.com"
        )
        team_three = Team.objects.create(
            name="Team Three",
            tournament=tourney_one,
            password=make_password("teamthreepwd"),
        )
        team_four = Team.objects.create(
            name="Team Four",
            tournament=tourney_one,
            password=make_password("teamfourpwd"),
        )

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
        team_five = Team.objects.create(
            name="Team Five",
            tournament=tourney_one,
            password=make_password("teamfivepwd"),
        )

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

    def test_substitute_player_duplication(self) -> None:
        """Verify that a user cannot be a substitute and a player on the same tournament"""
        game_obj = Game.objects.create(name="Game 1", short_name="G1")
        tourney_one = BaseTournament.objects.create(
            name="Tourney 1", game=game_obj
        )
        tourney_two = BaseTournament.objects.create(
            name="Tourney 2", game=game_obj
        )

        # This should work (Player in tourney 1, Substitute in Tourney 2)
        user_one = User.objects.create_user(
            username="user_test_one", email="user_test_one@example.com"
        )

        Player.objects.create(
            user=user_one,
            team=Team.objects.create(
                name="Team One",
                tournament=tourney_one,
                password=make_password("teamonepwd"),
            ),
        )
        Substitute.objects.create(
            user=user_one,
            team=Team.objects.create(
                name="Team Two",
                tournament=tourney_two,
                password=make_password("teamtwopwd"),
            ),
        )

        # This should not work (Player and Manager in tourney 1 in different teams)
        user_two = User.objects.create_user(
            username="user_test_two", email="user_test_two@example.com"
        )
        team_three = Team.objects.create(
            name="Team Three",
            tournament=tourney_one,
            password=make_password("teamthreepwd"),
        )
        team_four = Team.objects.create(
            name="Team Four",
            tournament=tourney_one,
            password=make_password("teamfourpwd"),
        )

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
        team_five = Team.objects.create(
            name="Team Five",
            tournament=tourney_one,
            password=make_password("teamfivepwd"),
        )

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

    def test_get_game(self) -> None:
        """Get the game for a tournament"""
        game = Game.objects.get(name="Test Game Three")
        tourney = BaseTournament.objects.get(name="Tourney 3")

        self.assertEqual(game, tourney.get_game())

    def test_get_teams(self) -> None:
        """Get the teams for a tournament"""
        tourney = BaseTournament.objects.all()[0]
        tourney_two = BaseTournament.objects.all()[1]
        team_one = Team.objects.create(
            name="Ohlala",
            tournament=tourney,
            password=make_password("ohlalapwd"),
        )
        team_two = Team.objects.create(
            name="OhWow",
            tournament=tourney,
            password=make_password("ohwowpwd"),
        )
        team_three = Team.objects.create(
            name="LeChiengue",
            tournament=tourney_two,
            password=make_password("lechienguepwd"),
        )

        teams = tourney.get_teams()
        self.assertEqual(2, len(teams))
        self.assertTrue(team_one in teams)
        self.assertTrue(team_two in teams)
        self.assertFalse(team_three in teams)

    def test_name_too_short(self) -> None:
        """Verify that a tournament name cannot be too short"""
        tourneyobj = BaseTournament.objects.all()[0]
        tourneyobj.name = "C" * 2
        self.assertRaises(ValidationError, tourneyobj.full_clean)

        tourneyobj.name = "C" * 3
        tourneyobj.full_clean()

    def test_name_too_long(self) -> None:
        """Verify that a tournament name cannot be too long"""
        tourney = BaseTournament.objects.all()[0]
        tourney.name = "C" * 513
        self.assertRaises(ValidationError, tourney.full_clean)

        tourney.name = "C" * 512
        tourney.full_clean()

    def test_game_deletion_cascade(self) -> None:
        """Verify that a tournament is deleted when its game is"""
        tourney = BaseTournament.objects.all()[0]
        game_obj = tourney.game

        BaseTournament.objects.get(id=tourney.id)

        # Delete and verify
        game_obj.delete()

        self.assertRaises(
            BaseTournament.DoesNotExist, BaseTournament.objects.get, id=tourney.id
        )

    @staticmethod
    def create_tourney_logo(file_name: str = "tourney-test.png") -> SimpleUploadedFile:
        """Create a logo for tournament tests"""
        test_img = BytesIO(f"test-image called {file_name}".encode("utf-8"))
        test_img.name = file_name
        return SimpleUploadedFile(test_img.name, test_img.getvalue())

    def test_logo_extension_enforcement(self) -> None:
        """Verify that we only accept logos as PNG, JPG, JPEG and SVG"""
        tourney = BaseTournament.objects.all()[0]

        # PNGs work
        test_png = BaseTournamentTestCase.create_tourney_logo("tourney-test.png")
        tourney.logo = test_png
        tourney.full_clean()

        # JPGs work
        test_jpg = BaseTournamentTestCase.create_tourney_logo("tourney-test.jpg")
        tourney.logo = test_jpg
        tourney.full_clean()

        # JPEGs work
        test_jpeg = BaseTournamentTestCase.create_tourney_logo("tourney-test.jpeg")
        tourney.logo = test_jpeg
        tourney.full_clean()

        # SVGs work
        test_svg = BaseTournamentTestCase.create_tourney_logo("tourney-test.svg")
        tourney.logo = test_svg
        tourney.full_clean()

        # Others won't
        for ext in ["mkv", "txt", "md", "php", "exe", "zip", "7z"]:
            test_icon = BaseTournamentTestCase.create_tourney_logo(f"tourney-test.{ext}")
            tourney.logo = test_icon
            self.assertRaises(ValidationError, tourney.full_clean)

    def test_rules_size_limit(self) -> None:
        """
        Check that the rules of a tournament can overflow the limit.

        This is a consequence of the way `max_length` is enforced in `TextField`
        fields, i.e. not. It is only enforced on the text area for the input,
        but not the database.

        See: https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.TextField
        """
        tourney = BaseTournament.objects.all()[0]

        tourney.rules = "C" * 50001
        tourney.full_clean()

class TournamentMeTests(APITestCase):
    """
    Test the tournament/me endpoint
    """
    def setUp(self) -> None:
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
            date_start=date(2021,12,1),
            date_end=date(2021,12,2),
            ongoing=False,
        )
        self.game_obj = Game.objects.create(name="Test Game", short_name="TFG")
        self.tourneyobj_one = EventTournament.objects.create(
            event=self.evobj,
            name="Test Tournament",
            rules="have fun!",
            game=self.game_obj,
            is_announced=True,
        )
        self.team_one = Team.objects.create(
            name="Team One",
            tournament=self.tourneyobj_one,
            password=make_password("password"),
        )
        self.plobjt = Player.objects.create(
            user_id=self.usrobj.id,
            team=self.team_one,
            name_in_game="pseudo"
        )

        self.team_two = Team.objects.create(
            name="Team Two",
            tournament=self.tourneyobj_one,
            password=make_password("password"),
        )
        self.managojt = Manager.objects.create(
            user_id=self.usrobj.id,
            team=self.team_two
        )
        self.subobj = Substitute.objects.create(
            user_id=self.usrobj.id,
            team=self.team_two,
            name_in_game="pseudo"
        )

        self.tourneyobj_two = PrivateTournament.objects.create(
            name="Test Tournament 2",
            game=self.game_obj,
        )
        self.team_three = Team.objects.create(
            name="Team Three",
            tournament=self.tourneyobj_two,
            password=make_password("password"),
        )
        self.plobjt2 = Player.objects.create(
            user_id=self.usrobj.id,
            team=self.team_three,
            name_in_game="pseudo"
        )

    def test_get_tournament_me(self) -> None:
        """
        Test the tournament/me endpoint
        """
        self.client.login(username="randomplayer", password="IUseAVerySecurePassword")
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['player'][0]['name_in_game'], self.plobjt.name_in_game)
        self.assertEqual(response.data['player'][0]['team']['name'], self.team_one.name)
        self.assertEqual(response.data['player'][0]['team']['tournament']['name'],
                         self.tourneyobj_one.name)
        self.assertEqual(response.data['player'][0]['team']['tournament']['event']['name'],
                         self.evobj.name)

        self.assertEqual(response.data['player'][1]['name_in_game'], self.plobjt2.name_in_game)
        self.assertEqual(response.data['player'][1]['team']['name'], self.team_three.name)
        self.assertEqual(response.data['player'][1]['team']['tournament']['name'],
                         self.tourneyobj_two.name)
        self.assertTrue('event' not in response.data['player'][1]['team']['tournament'])

    def test_get_tournament_me_manager(self) -> None:
        """
        Test the tournament/me endpoint
        """
        self.client.login(username="randomplayer", password="IUseAVerySecurePassword")
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.data['manager'][0]['id'], self.managojt.id)
        self.assertEqual(response.data['manager'][0]['team']['name'], self.team_two.name)
        self.assertEqual(response.data['manager'][0]['team']['tournament']['name'],
                         self.tourneyobj_one.name)
        self.assertEqual(response.data['manager'][0]['team']['tournament']['event']['name'],
                         self.evobj.name)

    def test_get_tournament_me_substitute(self) -> None:
        """
        Test the tournament/me endpoint
        """
        self.client.login(username="randomplayer", password="IUseAVerySecurePassword")
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.data['substitute'][0]['name_in_game'], self.subobj.name_in_game)
        self.assertEqual(response.data['substitute'][0]['team']['name'], self.team_two.name)
        self.assertEqual(response.data['substitute'][0]['team']['tournament']['name'],
                         self.tourneyobj_one.name)
        self.assertEqual(response.data['substitute'][0]['team']['tournament']['event']['name'],
                         self.evobj.name)

    def test_get_tournament_me_unauthenticated(self) -> None:
        """
        Test the tournament/me endpoint
        """
        response = self.client.get(reverse("tournament/me"))

        self.assertEqual(response.status_code, 403)
