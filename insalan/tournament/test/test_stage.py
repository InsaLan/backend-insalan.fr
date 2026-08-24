"""Tournament Stage Module Tests"""

from datetime import date
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from rest_framework.test import APITestCase

from insalan.tournament.models import (
    Player,
    Team,
    EventTournament,
    Event,
    Game,
    Stage,
    Bracket,
    BracketType
)
from insalan.user.models import User

class StageTestCase(APITestCase):
    """Stage Unit Test Class"""

    def setUp(self) -> None:
        """Setup method for Player Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,8,1), date_end=date(2023,8,2), description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(game=game, event=event)
        stg = Stage.objects.create(name="Test Stage", tournament=trnm, index=1)

        # Now the users
        user_one = User.objects.create_superuser(
            username="testplayer",
            email="player.user.test@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )

    def test_stage_functions_not_admin(self) -> None:
        """Check that APIs are refused to non-admins"""
        raise NotImplementedError()

    def test_add_stage(self) -> None:
        """
        Create a stage from the API
        """
        event = Event.objects.get(date_start=date(2023,8,1))
        game = Game.objects.get(name="Test Game")
        trnm = EventTournament.objects.get(game=game, event=event)

        user = User.objects.get(username="testplayer")
        self.client.force_login(user=user)

        data = {
            "name": "Stage addition",
            "index": 1,
            "tournament": trnm.pk
        }

        request = self.client.post("/v1/tournament/stage/create/", data)
        self.assertEqual(request.status_code, 201)
        Stage.objects.get(name="Stage addition")

    def test_update_stage(self) -> None:
        """
        Update a stage from the API
        """
        event = Event.objects.get(date_start=date(2023,8,1))
        game = Game.objects.get(name="Test Game")
        trnm = EventTournament.objects.get(game=game, event=event)
        stage = Stage.objects.create(name="Stage update", index=1, tournament=trnm)

        user = User.objects.get(username="testplayer")
        self.client.force_login(user=user)

        data = {
            "name": "Stage update",
            "index": 3,
            "tournament": trnm.pk
        }

        request = self.client.put(f"/v1/tournament/stage/{stage.pk}/update/", data)
        self.assertEqual(request.status_code, 200)
        self.assertEqual(Stage.objects.get(pk=stage.pk).index, 3)

    def test_delete_stage(self) -> None:
        """
        Delete a stage from the API
        """
        event = Event.objects.get(date_start=date(2023,8,1))
        game = Game.objects.get(name="Test Game")
        trnm = EventTournament.objects.get(game=game, event=event)
        stage = Stage.objects.create(name="Stage deletion", index=1, tournament=trnm)

        user = User.objects.get(username="testplayer")
        self.client.force_login(user=user)


        request = self.client.delete(f"/v1/tournament/stage/{stage.pk}/delete/")
        self.assertEqual(request.status_code, 204)
        self.assertRaises(Stage.DoesNotExist, Stage.objects.get, pk=stage.pk)

    def test_add_groups(self) -> None:
        """
        Add group to a stage
        """
        raise NotImplementedError()

    def test_add_groups_autofill(self) -> None:
        """
        Add group with autofill to a stage
        """
        raise NotImplementedError()

    def test_add_brackets(self) -> None:
        """
        Add brackets to a stage
        """
        raise NotImplementedError()

    def test_add_swiss(self) -> None:
        """
        Add swiss rounds to a stage
        """
        raise NotImplementedError()
