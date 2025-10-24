"""Tournament Manager Module Tests"""

from django.db.utils import IntegrityError
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.test import TestCase

from insalan.tournament.models import (
    PaymentStatus,
    Player,
    Manager,
    Team,
    EventTournament,
    Event,
    Game,
)
from insalan.user.models import User

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
        trnm = EventTournament.objects.create(game=game, event=event)
        team_one = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )

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

        self.assertEqual(found_user.get_username(), "randomplayer")
        self.assertEqual(found_user.get_short_name(), "Random")
        self.assertEqual(found_user.get_full_name(), "Random Player")
        self.assertEqual(found_user.get_user_permissions(), set())
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
        trnm = EventTournament.objects.get(event=event)

        managers = Manager.objects.filter(user=user)
        self.assertEqual(1, len(managers))
        manager = managers[0]

        team = manager.get_team()
        self.assertIsNotNone(team)

        self.assertEqual(team.get_name(), "La Team Test")
        self.assertEqual(team.get_tournament(), trnm)

    def test_one_manager_many_teams_same_event_same_tournament_same_team(self):
        """Test the collision of duplicate managers"""
        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", year=2023, month=8, description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(
            game=game,
            event=event,
            is_announced=True,
        )
        team_one = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )

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
        trnm = EventTournament.objects.create(game=game, event=event)
        # TODO: enable back this warning when the test is fixed.
        team_one = Team.objects.create( # pylint: disable=unused-variable
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )
        team_two = Team.objects.create(
            name="La Team Test 2",
            tournament=trnm,
            password=make_password("lateamtest2pwd"),
        )

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
        trnm = EventTournament.objects.create(
            game=game,
            event=event,
            is_announced=True,
        )
        trnm_two = EventTournament.objects.create(
            game=game,
            event=event,
            is_announced=True,
        )
        team_one = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("lateamtestpwd"),
        )
        team_two = Team.objects.create(
            name="La Team Test 2",
            tournament=trnm_two,
            password=make_password("lateamtest2pwd"),
        )

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
        trnm = EventTournament.objects.create(
            game=game,
            event=event,
            is_announced=True,
        )
        trnm_two = EventTournament.objects.create(
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
        trnm = EventTournament.objects.create(game=game, event=event)
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
        trnm = EventTournament.objects.create(
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

    def test_delete_manager(self):
        """
        Test the delete method of the Manager API
        """
        user = User.objects.get(username="randomplayer")

        manager = Manager.objects.get(user=user)

        self.client.force_login(user=user)

        # delete request
        request = self.client.delete(
            f"/v1/tournament/manager/{manager.id}/",
            content_type="application/json",
        )

        # check response
        self.assertEqual(request.status_code, 204)

        # check data
        self.assertRaises(Manager.DoesNotExist, Manager.objects.get, id=manager.id)

    def test_delete_manager_not_owner(self):
        """
        Test the delete method of the Manager API when the user is not related to the manager
        """
        user = User.objects.get(username="randomplayer")
        user_two = User.objects.get(username="testplayer")

        manager = Manager.objects.get(user=user)

        self.client.force_login(user=user_two)

        # delete request
        request = self.client.delete(
            f"/v1/tournament/manager/{manager.id}/",
            content_type="application/json",
        )

        # check response
        self.assertEqual(request.status_code, 403)
