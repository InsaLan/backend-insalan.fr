"""Tournament Team Module Tests"""

from datetime import date
from django.db.utils import IntegrityError
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.test import TestCase

from insalan.tournament.models import (
    PaymentStatus,
    Player,
    Manager,
    Substitute,
    Team,
    EventTournament,
    Event,
    Game,
    SeatSlot,
    Seat
)
from insalan.user.models import User

class TeamTestCase(TestCase):
    """
    Tests for the Team model
    """

    def setUp(self) -> None:
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
            name="Insalan Test One",
            date_start=date(2023,2,1),
            date_end=date(2023,2,2),
            description=""
        )

        game = Game.objects.create(
            name="Fortnite",
            substitute_players_per_team=1,
        )

        trnm_one = EventTournament.objects.create(
            event=event_one,
            game=game,
            is_announced=True,
            maxTeam = 10
        )
        trnm_two = EventTournament.objects.create(
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

    def test_team_get_full(self) -> None:
        """Get the fields of a Team"""
        team = Team.objects.get(name="LaLooze")
        self.assertIsNotNone(team)

        self.assertEqual("LaLooze", team.get_name())
        self.assertIsInstance(team.get_tournament(), EventTournament)
        self.assertEqual(2, len(team.get_players()))
        self.assertEqual(0, len(team.get_managers()))
        self.assertEqual(1, len(team.get_substitutes()))

        team = Team.objects.get(name="LaPouasse")
        self.assertIsNotNone(team)

        self.assertEqual("LaPouasse", team.get_name())
        self.assertIsInstance(team.get_tournament(), EventTournament)
        self.assertEqual(1, len(team.get_players()))
        self.assertEqual(1, len(team.get_managers()))
        self.assertEqual(0, len(team.get_substitutes()))

    def test_payment_status_default(self) -> None:
        """Verify what the default status of payment on a new player is"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        play_reg = Player.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, play_reg.payment_status)

    def test_payment_status_set(self) -> None:
        """Verify that we can set a status for a Player at any point"""
        robert = User.objects.all()[0]
        team = Team.objects.all()[0]

        play_reg = Player.objects.create(user=robert, team=team)

        self.assertEqual(PaymentStatus.NOT_PAID, play_reg.payment_status)

        play_reg.payment_status = PaymentStatus.PAY_LATER

        self.assertEqual(PaymentStatus.PAY_LATER, play_reg.payment_status)

    def test_get_team_players(self) -> None:
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

    def test_team_collision_name(self) -> None:
        """Test Name Collision for a Tournament"""
        team = Team.objects.get(name="LaLooze")
        tourney = team.get_tournament()

        # Attempt to register another one
        self.assertRaises(
            IntegrityError,
            Team.objects.create,
            name="LaLooze",
            tournament=tourney,
            password=make_password("laloozepwd"),
        )

    def test_team_name_too_short(self) -> None:
        """Verify that a team name cannot be too short"""
        team = Team.objects.get(name="LaLooze")
        team.name = "CC"
        self.assertRaises(ValidationError, team.full_clean)

        team.name += "C"
        team.full_clean()

    def test_team_name_too_long(self) -> None:
        """Verify that a team name cannot be too long"""
        team = Team.objects.get(name="LaLooze")
        team.name = "C" * 43
        self.assertRaises(ValidationError, team.full_clean)

        team.name = "C" * 42
        team.full_clean()


class TournamentTeamEndpoints(TestCase):
    """Tournament Registration Endpoint Test Class"""

    # TODO Test all endpoints

    def setUp(self) -> None:
        """Setup method for Tournament Registrations Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,3,1), date_end=date(2023,3,2), description=""
        )
        game = Game.objects.create(name="Test Game", substitute_players_per_team=1)
        trnm = EventTournament.objects.create(
            game=game,
            event=event,
            maxTeam=16,
            is_announced=True
        )
        Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("password"),
        )

        # user_one = User.objects.create_user(
        #     username="testplayer",
        #     email="player.user.test@insalan.fr",
        #     password="^ThisIsAnAdminPassword42$",
        #     first_name="Iam",
        #     last_name="Staff",
        # )

        User.objects.create_user(
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

    def test_can_create_a_team_with_player(self) -> None:
        """Try to create a team with a player"""
        user: User = User.objects.get(username="validemail")
        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        request = self.client.post(
            "/v1/tournament/team/",
            {
                "name": "La Team Test 2",
                "tournament": trnm.id,
                "password": "Password123!",
                "players": [
                    user.id,
                ],
                "players_names_in_game": [
                    "pseudo",
                ]
            },
            format="json",
        )

        self.assertEqual(request.status_code, 201)

        team = Team.objects.get(name="La Team Test 2")
        self.assertEqual(team.get_tournament(), trnm)

        player = Player.objects.get(user=user)
        self.assertEqual(player.as_user(), user)
        self.assertEqual(player.get_team(), team)
        self.assertEqual(player.get_name_in_game(), "pseudo")

    def test_can_create_a_team_with_manager(self) -> None:
        """Try to create a team with a manager"""
        user: User = User.objects.get(username="validemail")
        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        request = self.client.post(
            "/v1/tournament/team/",
            {
                "name": "La Team Test 2",
                "tournament": trnm.id,
                "password": "Password123!",
                "managers": [
                    user.id,
                ],
            },
            format="json",
        )

        self.assertEqual(request.status_code, 201)

        team = Team.objects.get(name="La Team Test 2")
        self.assertEqual(team.get_tournament(), trnm)

        manager = Manager.objects.get(user=user)
        self.assertEqual(manager.as_user(), user)
        self.assertEqual(manager.get_team(), team)

    def test_can_create_a_team_with_substitute(self) -> None:
        """Try to create a team with a substitute"""
        user: User = User.objects.get(username="validemail")
        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        request = self.client.post(
            "/v1/tournament/team/",
            {
                "name": "La Team Test 2",
                "tournament": trnm.id,
                "password": "Password123!",
                "substitutes": [
                    user.id,
                ],
                "substitutes_names_in_game": [
                    "pseudo",
                ]
            },
            format="json",
        )

        self.assertEqual(request.status_code, 201)

        team = Team.objects.get(name="La Team Test 2")
        self.assertEqual(team.get_tournament(), trnm)

        substitute = Substitute.objects.get(user=user)
        self.assertEqual(substitute.as_user(), user)
        self.assertEqual(substitute.get_team(), team)
        self.assertEqual(substitute.get_name_in_game(), "pseudo")

    def test_can_create_a_team_with_valid_email(self) -> None:
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

        self.assertEqual(request.status_code, 201)

    def test_cant_create_a_team_with_no_valid_email(self) -> None:
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

        self.assertEqual(request.status_code, 403)

    def test_can_patch_team_captain(self) -> None:
        """Test that we can patch a team"""
        user: User = User.objects.get(username="validemail")

        user2: User = User.objects.create_user(
            username="validemail2",
            email="valideemail@gmail.com",
            password="ThisIsPassword",
        )

        self.client.force_login(user=user)


        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        # Create a team
        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm,
            password=make_password("password"),
        )

        old_password = team.password

        # Create players
        player = Player.objects.create(team=team, user=user, name_in_game="pseudo")
        Player.objects.create(team=team, user=user2, name_in_game="pseudo2")

        # patch data
        data = {
            "name": "Nom d'équipe 2",
            "password": "password2",
            "players": [
            ]
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(request.status_code, 200)

        # check that the team has been updated
        team = Team.objects.get(id=team.id)
        self.assertEqual(team.name, "Nom d'équipe 2")
        self.assertNotEqual(team.password, old_password)

        # check that the players have been updated
        players = team.get_players()
        self.assertEqual(len(players), 1)
        self.assertEqual(players[0].id, player.id)

    def test_cant_patch_team_not_captain(self) -> None:
        """Test that we can't patch a team if we're not the captain"""
        user: User = User.objects.get(username="validemail")

        user2: User = User.objects.create_user(
            username="validemail2",
            email="valideemail@gmail.com",
            password="ThisIsPassword",
        )

        self.client.force_login(user=user2)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        # Create a team
        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm,
            password=make_password("password"),
        )

        # Create players
        Player.objects.create(team=team, user=user, name_in_game="pseudo")
        Player.objects.create(team=team, user=user2, name_in_game="pseudo2")

        # patch data
        data = {
            "name": "Nom d'équipe 2",
            "password": "password2",
            "players": [
            ]
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(request.status_code, 403)

    def test_can_patch_team_manager(self) -> None:
        """Test that we can patch a team"""
        User.objects.get(username="validemail")

        user2: User = User.objects.create_user(
            username="validemail2",
            email="valideemail@gmail.com",
            password="ThisIsPassword",
        )

        self.client.force_login(user=user2)

        event = Event.objects.get(name="InsaLan Test")
        trnm = event.get_tournaments()[0]

        # Create a team
        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm,
            password=make_password("password"),
        )

        Manager.objects.create(team=team, user=user2)

        # patch data
        data = {
            "name": "Nom d'équipe 2",
            "password": "password2",
            "players": [
            ]
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(request.status_code, 200)

        # check that the team has been updated
        team = Team.objects.get(id=team.id)
        self.assertEqual(team.name, "Nom d'équipe 2")
        self.assertNotEqual(team.password, "password")

    def test_cant_patch_team_substitute(self) -> None:
        """Test that we can't patch a team"""
        User.objects.get(username="validemail")

        user2: User = User.objects.create_user(
            username="validemail2",
            email="valideemail@gmail.com",
            password="ThisIsPassword",
        )

        self.client.force_login(user=user2)

        event = Event.objects.get(name="InsaLan Test")

        trnm = event.get_tournaments()[0]

        # Create a team
        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm,
            password=make_password("password"),
        )

        Substitute.objects.create(team=team, user=user2, name_in_game="pseudo")

        # patch data
        data = {
            "name": "Nom d'équipe 2",
            "password": "password2",
            "players": [
            ]
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(request.status_code, 403)

    def test_can_patch_seat_slot(self) -> None:
        user: User = User.objects.get(username="validemail")

        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")

        game2 = Game.objects.create(name="Test Game 2", short_name="TFG2", players_per_team=3)
        trnm2 = EventTournament.objects.create(
            game=game2,
            event=event,
            maxTeam=16,
            is_announced=True
        )

        seat_slot = SeatSlot.objects.create(tournament=trnm2)
        seat_slot.seats.set([
            Seat.objects.create(event=event, x=1, y=1),
            Seat.objects.create(event=event, x=1, y=2),
            Seat.objects.create(event=event, x=1, y=3),
        ])

        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm2,
            password=make_password("password"),
            validated=True,
        )
        # Add a player in the team
        pl1 = Player.objects.create(team=team, user=user, name_in_game="pseudo")
        team.captain = pl1
        team.save()

        Player.objects.create(team=team, user=user, name_in_game="pseudo")

        # patch data
        data = {
            "seat_slot": seat_slot.id,
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(request.status_code, 200)

        # check that the team has been updated
        team = Team.objects.get(id=team.id)
        self.assertEqual(team.seat_slot, seat_slot)

    def test_non_validated_cant_patch_seat_slot(self) -> None:
        user: User = User.objects.get(username="validemail")

        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")

        game2 = Game.objects.create(name="Test Game 2", short_name="TFG2", players_per_team=3)
        trnm2 = EventTournament.objects.create(
            game=game2,
            event=event,
            maxTeam=16,
            is_announced=True
        )

        seat_slot = SeatSlot.objects.create(tournament=trnm2)
        seat_slot.seats.set([
            Seat.objects.create(event=event, x=1, y=1),
            Seat.objects.create(event=event, x=1, y=2),
            Seat.objects.create(event=event, x=1, y=3),
        ])

        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm2,
            password=make_password("password"),
        )

        Player.objects.create(team=team, user=user, name_in_game="pseudo")

        # patch data
        data = {
            "seat_slot": seat_slot.id,
        }

        # patch request
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(request.status_code, 400)

    def test_cant_patch_seat_slot(self) -> None:
        user: User = User.objects.get(username="validemail")

        self.client.force_login(user=user)

        event = Event.objects.get(name="InsaLan Test")

        game2 = Game.objects.create(name="Test Game 2", short_name="TFG2", players_per_team=3)
        trnm2 = EventTournament.objects.create(
            game=game2,
            event=event,
            maxTeam=16,
            is_announced=True
        )

        seat_slot2 = SeatSlot.objects.create(tournament=trnm2)
        seat_slot2.seats.set([
            Seat.objects.create(event=event, x=1, y=1),
            Seat.objects.create(event=event, x=1, y=2),
            Seat.objects.create(event=event, x=1, y=3),
        ])

        team = Team.objects.create(
            name="Nom d'équipe 1",
            tournament=trnm2,
            password=make_password("password"),
        )

        Player.objects.create(team=team, user=user, name_in_game="pseudo")

        # invalid slot
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            {
                "seat_slot": 0,
            },
            content_type="application/json",
        )
        self.assertEqual(request.status_code, 400)

        # invalid tournament
        trnm = event.get_tournaments()[0]
        seat_slot = SeatSlot.objects.create(tournament=trnm)
        seat_slot.seats.set([
            Seat.objects.create(event=event, x=2, y=1),
            Seat.objects.create(event=event, x=2, y=2),
            Seat.objects.create(event=event, x=2, y=3),
        ])
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            {
                "seat_slot": seat_slot.id,
            },
            content_type="application/json",
        )
        self.assertEqual(request.status_code, 400)

        # slot already occupied
        Team.objects.create(
            name="Nom d'équipe 2",
            tournament=trnm2,
            password=make_password("password"),
            seat_slot=seat_slot2
        )
        request = self.client.patch(
            f"/v1/tournament/team/{team.id}/",
            {
                "seat_slot": seat_slot2.id,
            },
            content_type="application/json",
        )
        self.assertEqual(request.status_code, 400)



    def test_can_join_a_team_with_a_valid_email(self) -> None:
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
        self.assertEqual(request.status_code, 201)

        Player.objects.filter(user=user.id).delete()

        request = self.client.post(
            "/v1/tournament/manager/",
            {
                "team": team.id,
                "password":"password",
            },
            format="json",
        )
        self.assertEqual(request.status_code, 201)

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
        self.assertEqual(request.status_code, 201)


    def test_cant_join_a_team_with_no_valid_email(self) -> None:
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
        self.assertEqual(request.status_code, 403)

        request = self.client.post(
            "/v1/tournament/manager/",
            {
                "team": user.id,
                "password":"Password123!",
            },
            format="json",
        )
        self.assertEqual(request.status_code, 403)

        request = self.client.post(
            "/v1/tournament/substitute/",
            {
                "team": team.id,
                "password": "Password123!",
                "name_in_game":"pseudo",
            },
            format="json",
        )
        self.assertEqual(request.status_code, 403)
