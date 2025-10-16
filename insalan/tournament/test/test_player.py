"""Tournament Player Module Tests"""

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.test import TestCase

from insalan.tournament.models import (
    Player,
    Team,
    EventTournament,
    Event,
    Game,
)
from insalan.user.models import User


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
        trnm = EventTournament.objects.create(game=game, event=event)
        team_one: Team = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("password"),
        )

        # Second edition
        event_two = Event.objects.create(
            name="InsaLan Test (Past)", year=2023, month=3, description=""
        )
        trnm_two = EventTournament.objects.create(game=game, event=event_two)
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

        self.assertEqual(user.get_username(), "testplayer")
        self.assertEqual(user.get_short_name(), "Iam")
        self.assertEqual(user.get_full_name(), "Iam Staff")
        self.assertEqual(user.get_user_permissions(), set())
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
        trnm = EventTournament.objects.create(game=game, event=event)
        team = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )

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
        trnm = EventTournament.objects.create(game=game, event=event)
        team = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )

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
        trnm = EventTournament.objects.create(game=game, event=event)
        team = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )
        team_two = Team.objects.create(
            name="La Team Test 2",
            tournament=trnm,
            password=make_password("lateamtest2pwd"),
        )

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
        trnm = EventTournament.objects.create(game=game, event=event)
        trnm_two = EventTournament.objects.create(game=game, event=event)
        team = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )
        team_two = Team.objects.create(
            name="La Team Test 2",
            tournament=trnm_two,
            password=make_password("lateamtest2pwd"),
        )

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
        trnm = EventTournament.objects.create(game=game, event=event)
        trnm_two = EventTournament.objects.create(game=game, event=event_two)
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
        trnm = EventTournament.objects.get(event=event)

        player = Player.objects.get(user=user)
        self.assertIsNotNone(player)

        team = player.get_team()
        self.assertIsNotNone(team)

        self.assertEqual(team.get_name(), "La Team Test")
        self.assertEqual(team.get_tournament(), trnm)

    def test_player_team_deletion(self):
        """Verify the behaviour of a Player when their team gets deleted"""
        user_obj = User.objects.get(username="testplayer")
        event = Event.objects.get(year=2023, month=8)
        trnm = EventTournament.objects.get(event=event)
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
        trnm = EventTournament.objects.get(event=event)
        # Create a Player registration
        team_obj = Team.objects.create(name="La Team Test User", tournament=trnm)
        play_obj = Player.objects.create(team=team_obj, user=user_obj, name_in_game="pseudo")

        # Test
        Player.objects.get(id=play_obj.id)

        user_obj.delete()

        self.assertRaises(Player.DoesNotExist, Player.objects.get, id=play_obj.id)

    def test_patch_user(self):
        """
        Test the patch method of the Player API
        """
        user = User.objects.get(username="testplayer")

        player = Player.objects.get(user=user)

        self.client.force_login(user=user)

        # patch data
        data = {
            "name_in_game": "playerOneModified",
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/player/{player.id}/",
            data,
            content_type="application/json",
        )

        # check response
        self.assertEqual(request.status_code, 200)

        # check data
        self.assertEqual(request.data["name_in_game"], "playerOneModified")

    def test_patch_user_not_owner(self):
        """
        Test the patch method of the Player API when the user is not related to the player
        """
        user = User.objects.get(username="testplayer")
        user_two = User.objects.get(username="randomplayer")

        player = Player.objects.get(user=user)

        self.client.force_login(user=user_two)

        # patch data
        data = {
            "name_in_game": "playerOneModified",
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/player/{player.id}/",
            data,
            content_type="application/json",
        )

        # check response
        self.assertEqual(request.status_code, 403)

    def test_delete_user(self):
        """
        Test the delete method of the Player API
        """
        user = User.objects.get(username="testplayer")

        player = Player.objects.get(user=user)

        self.client.force_login(user=user)

        # delete request
        request = self.client.delete(
            f"/v1/tournament/player/{player.id}/",
            content_type="application/json",
        )

        # check response
        self.assertEqual(request.status_code, 204)

        # check data
        self.assertRaises(Player.DoesNotExist, Player.objects.get, id=player.id)

    def test_delete_user_not_owner(self):
        """
        Test the delete method of the Player API when the user is not related to the player
        """
        user = User.objects.get(username="testplayer")
        user_two = User.objects.get(username="randomplayer")

        player = Player.objects.get(user=user)

        self.client.force_login(user=user_two)

        # delete request
        request = self.client.delete(
            f"/v1/tournament/player/{player.id}/",
            content_type="application/json",
        )

        # check response
        self.assertEqual(request.status_code, 403)
