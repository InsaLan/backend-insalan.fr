"""User Tests Module"""
from typing import Dict
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

# from django.contrib.auth.models import Permission
# from django.contrib.contenttypes.models import ContentType

from insalan.tournament.models import Team, Tournament, Event, Game
from insalan.user.models import User, Player, Manager


class UserTestCase(TestCase):
    def setUp(self):
        u: User = User.objects.create_user(
            username="staffplayer",
            email="staff@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )
        u.is_staff = True

        # TODO Actual permission and test it somewhere else
        # content_type = ContentType.objects.get_for_model(User)
        # p: Permission = Permission.objects.create(
        #         codename='can_do_stuff',
        #         name='Can do stuff',
        #         content_type=content_type)
        #
        # u.user_permissions.add(p)
        # u.save()

        User.objects.create_user(
            username="randomplayer",
            email="randomplayer@gmail.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
        )
        User.objects.create_user(
            username="anotherplayer",
            password="ThisIsPassword",
        )

    def test_get_existing_full_user(self):
        u: User = User.objects.get(username="randomplayer")
        self.assertEquals(u.get_username(), "randomplayer")
        self.assertEquals(u.get_short_name(), "Random")
        self.assertEquals(u.get_full_name(), "Random Player")
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password("IUseAVerySecurePassword"))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_existing_minimal_user(self):
        u: User = User.objects.get(username="anotherplayer")
        self.assertEquals(u.get_username(), "anotherplayer")
        self.assertEquals(u.get_short_name(), "")
        self.assertEquals(u.get_full_name(), "")
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password("ThisIsPassword"))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_non_existing_user(self):
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="idontexist")


class UserEndToEndTestCase(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()

    def test_register_invalid_data(self):
        def send_invalid_data(data):
            request = self.client.post('/v1/user/register/',
                                       data,
                                       format='json')
            self.assertEquals(request.status_code, 400)

        send_invalid_data({})
        send_invalid_data({"username": "newuser"})
        send_invalid_data({"username": "newuser", "password": "1234"})
        send_invalid_data({"username": "newuser", "email": "email@example.com"})

    def test_register_valid_account(self):
        def send_valid_data(data, check_fields=[]):
            request = self.client.post('/v1/user/register/',
                                       data,
                                       format='json')

            self.assertEquals(request.status_code, 201)

            created_data: Dict = request.data

            for k, val in check_fields:
                self.assertEquals(created_data[k], val)

        send_valid_data(
            {"username": "newplayer", "password": "1111", "email": "email@example.com"},
            [
                ("username", "newplayer"),
                ("first_name", ""),
                ("last_name", ""),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email_active", False),
                ("email", "email@example.com"),
            ],
        )

        send_valid_data(
            {
                "username": "PeachLover3003",
                "password": "It's a me!",
                "email": "mario@mushroom.kingdom",
                "first_name": "Mario",
                "last_name": "Bros",
            },
            [
                ("username", "PeachLover3003"),
                ("first_name", "Mario"),
                ("last_name", "Bros"),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email_active", False),
                ("email", "mario@mushroom.kingdom"),
            ],
        )


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


# No end-to-end tests: Players do not have an API


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
