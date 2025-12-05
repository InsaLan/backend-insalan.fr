"""Tests for the ecological statistics app."""

from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse


from rest_framework import status
from rest_framework.test import APITestCase

from insalan.tournament.models import (
    Event,
    EventTournament,
    Game,
    Manager,
    Player,
    Substitute,
    Team,
)
from insalan.user.models import User

from .models import TransportationMethod, TravelData


class TravelDataModelTestCase(TestCase):
    """Tests for the TravelData model."""

    def setUp(self) -> None:
        self.event = Event.objects.create(
            name="Test event",
        )
        self.travel_data = TravelData.objects.create(
            city="Nantes",
            transportation_method=TransportationMethod.CAR,
            event=self.event,
        )

    def test_create_travel_data(self) -> None:
        """Test creating a TravelData."""
        travel_data = TravelData.objects.create(
            city="Rennes",
            transportation_method=TransportationMethod.BIKE,
            event=self.event,
        )
        self.assertEqual(travel_data.city, "Rennes")
        self.assertEqual(travel_data.transportation_method, TransportationMethod.BIKE)
        self.assertEqual(travel_data.event.id, self.event.id)

    def test_city_empty(self) -> None:
        """Test creating a TravelData with a city too long."""
        self.travel_data.city = ""
        with self.assertRaises(ValidationError):
            self.travel_data.full_clean()

    def test_city_length_limit(self) -> None:
        """Test creating a TravelData with a city too long."""
        self.travel_data.city = "X" * 256
        with self.assertRaises(ValidationError):
            self.travel_data.full_clean()


class CreateTravelDataTestCase(APITestCase):
    """Tests for the CreateTravelData API endpoint."""

    def setUp(self) -> None:
        self.user = User.objects.create(
            username="user",
            email="user@example.com",
        )
        self.event = Event.objects.create(
            name="Test event",
        )
        game = Game.objects.create()
        self.tournament = EventTournament.objects.create(
            game=game,
            event=self.event,
        )
        self.team = Team.objects.create(tournament=self.tournament)
        TravelData.objects.create(
            city="Nantes",
            transportation_method=TransportationMethod.CAR,
            event=self.event,
        )

    def test_post_player(self) -> None:
        """Test to create a TravelData as a player."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_player_already_sent_data(self) -> None:
        """Test to create a TravelData as a player that as already sent travel data."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team, ecological_data_sent=True)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Données écologique déjà envoyées"})

    def test_post_manager(self) -> None:
        """Test to create a TravelData as a manager."""
        self.client.force_login(user=self.user)
        Manager.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_manager_already_sent_data(self) -> None:
        """Test to create a TravelData as a manager that as already sent travel data."""
        self.client.force_login(user=self.user)
        Manager.objects.create(user=self.user, team=self.team, ecological_data_sent=True)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Données écologique déjà envoyées"})

    def test_post_substitute(self) -> None:
        """Test to create a TravelData as a substitute."""
        self.client.force_login(user=self.user)
        Substitute.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_substitute_already_sent_data(self) -> None:
        """Test to create a TravelData as a substitute that as already sent travel data."""
        self.client.force_login(user=self.user)
        Substitute.objects.create(user=self.user, team=self.team, ecological_data_sent=True)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Données écologique déjà envoyées"})

    def test_post_unauthenticated(self) -> None:
        """Test trying to post data without being authenticated."""
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_not_registered(self) -> None:
        """Test to create a TravelData when registered in the tournament."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"detail": "L'utilisateur n'est pas inscrit au tournois"})

    def test_post_missing_tournament_field(self) -> None:
        """Test post without the tournament field."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"tournament": "Champ manquant"})

    def test_post_missing_city_field(self) -> None:
        """Test post without the city field."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"city": ["Ce champ est obligatoire."]})

    def test_post_missing_transportation_method_field(self) -> None:
        """Test post without the transportation_method field."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"transportation_method": ["Ce champ est obligatoire."]})

    def test_post_missing_event_field(self) -> None:
        """Test post without the event field."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"event": ["Ce champ est obligatoire."]})

    def test_post_empty_city_field(self) -> None:
        """Test post with the city field empty."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"city": ["Ce champ ne peut être vide."]})

    def test_post_empty_transportation_method_field(self) -> None:
        """Test post with the transportation_method field empty."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            "transportation_method": ["«\xa0\xa0» n'est pas un choix valide."],
        })

    def test_post_invalid_transportation_method(self) -> None:
        """Test post with an invalid transportation method."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "Invalid transportation method",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            "transportation_method": [
                "«\xa0Invalid transportation method\xa0» n'est pas un choix valide.",
            ],
        })

    def test_post_tournament_not_found(self) -> None:
        """Test post with an invalid tournament."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": 9999,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"detail": "Tournois invalide"})

    def test_post_event_not_found(self) -> None:
        """Test post with an invalid event."""
        self.client.force_login(user=self.user)
        Player.objects.create(user=self.user, team=self.team)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "tournament": self.tournament.id,
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": 9999,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            "event": ["Clé primaire «\xa09999\xa0» non valide - l'objet n'existe pas."],
        })
