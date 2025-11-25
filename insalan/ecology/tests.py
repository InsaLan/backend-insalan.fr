"""Tests for the ecological statistics app."""

from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse


from rest_framework import status
from rest_framework.test import APITestCase

from insalan.tournament.models import Event
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
        TravelData.objects.create(
            city="Nantes",
            transportation_method=TransportationMethod.CAR,
            event=self.event,
        )

    def test_post(self) -> None:
        """Test to create a TravelData."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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

    def test_post_duplicate(self) -> None:
        """Test posting duplicate of an already existing entry."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Nantes",
                "transportation_method": "CAR",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_missing_city_field(self) -> None:
        """Test post without the city field."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_transportation_method_field(self) -> None:
        """Test post without the transportation_method field."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_event_field(self) -> None:
        """Test post without the event field."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "transportation_method": "BIKE",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_empty_city_field(self) -> None:
        """Test post with the city field empty."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "",
                "transportation_method": "BIKE",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_empty_transportation_method_field(self) -> None:
        """Test post with the transportation_method field empty."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "transportation_method": "",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_transportation_method(self) -> None:
        """Test post with an invalid transportation method."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "transportation_method": "Invalid transportation method",
                "event": self.event.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_event_not_found(self) -> None:
        """Test post with an invalid event."""
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("ecology:create-travel-data"),
            data={
                "city": "Rennes",
                "transportation_method": "BKIE",
                "event": 9999,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
