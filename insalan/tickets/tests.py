"""
This module contains unit tests for the `Ticket` model and API endpoints.

The tests cover the following functionalities:
- Creating tickets
- Retrieving existing tickets
- Handling non-existing tickets
- Scanning tickets
- Generating QR codes for tickets

The tests are organized into two classes:
- `TicketTestCase`: Contains unit tests for the `Ticket` model.
- `Ticket_TODO`: Contains API endpoint tests for ticket-related operations.

"""
import uuid

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.test import APITestCase

from insalan.tournament.models import Event, Game, Tournament
from insalan.user.models import User
from .models import Ticket

def create_ticket(
    username: str,
    token: str,
    tourney: Tournament,
    ticket_status: Ticket.Status = Ticket.Status.VALID,
) -> int:
    """
    Create a ticket for the given username and token.
    """
    user = User.objects.create_user(
        username=username,
        password=username,
        email=f"{username}@example.com",
    )
    Ticket.objects.create(
        user=user, token=uuid.UUID(token), status=ticket_status, tournament=tourney
    )
    return user.id


class TicketTestCase(TestCase):
    """
    Test case for the `Ticket` model.
    """
    def setUp(self) -> None:
        """
        Create a ticket for each of the following users:
        - `user1`: Valid ticket
        - `user2`: Cancelled ticket
        """
        event_one = Event.objects.create(
            name="InsaLan Test", description="Test", month=2023, year=12, ongoing=True
        )
        game_one = Game.objects.create(name="Counter-Strike 2", short_name="CS2")
        tourney_one = Tournament.objects.create(
            name="Tournament", event=event_one, game=game_one, rules=""
        )
        create_ticket("user1", "00000000-0000-0000-0000-000000000001", tourney_one)
        create_ticket(
            "user2",
            "00000000-0000-0000-0000-000000000002",
            tourney_one,
            Ticket.Status.CANCELLED,
        )

    def test_get_existing_tickets(self) -> None:
        """
        Test that the tickets created in the `setUp` method exist and have the
        correct attributes.
        """
        token1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
        ticket = Ticket.objects.get(token=token1)
        self.assertEqual(ticket.token, token1)
        self.assertEqual(ticket.user, User.objects.get(username="user1"))
        self.assertEqual(ticket.status, Ticket.Status.VALID)

        token2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
        ticket = Ticket.objects.get(token=token2)
        self.assertEqual(ticket.token, token2)
        self.assertEqual(ticket.user, User.objects.get(username="user2"))
        self.assertEqual(ticket.status, Ticket.Status.CANCELLED)

    def test_get_non_existing_tickets(self):
        """
        Test that the tickets not created in the `setUp` method do not exist.
        """
        token = uuid.UUID("00000000-0000-0000-0000-000000000003")
        with self.assertRaises(Ticket.DoesNotExist):
            Ticket.objects.get(token=token)


class TicketTODO(APITestCase):
    """
    Test case for the ticket-related API endpoints.
    """
    def setUp(self) -> None:
        """
        Create test environment for the API endpoint tests.
        """
        User.objects.create_user(
            username="user", password="user", email="user@example.com"
        )
        User.objects.create_user(
            username="admin", password="admin", email="admin@example.com", is_staff=True
        )
        event_one = Event.objects.create(
            name="InsaLan Test", description="Test", month=2023, year=12, ongoing=True
        )
        game_one = Game.objects.create(name="Counter-Strike 2", short_name="CS2")
        Tournament.objects.create(
            name="Tournament", event=event_one, game=game_one, rules=""
        )

    def login(self, username: str) -> None:
        """
        Log in as the given user.
        """
        self.assertTrue(self.client.login(username=username, password=username))

    def test_get(self) -> None:
        """
        Test the `get` API endpoint.
        """
        tourney = Tournament.objects.all()[0]
        user1_id = create_ticket("user1", "00000000-0000-0000-0000-000000000001", tourney)

        response = self.client.get(
            reverse(
                "tickets:get", args=[user1_id, "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("user")

        response = self.client.get(
            reverse(
                "tickets:get", args=[user1_id, "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("admin")

        response = self.client.get(
            reverse("tickets:get", args=[user1_id, "invalid-uuid"])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"err": _("UUID invalide")})

        response = self.client.get(
            reverse(
                "tickets:get", args=[1000, "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Utilisateur⋅ice non trouvé⋅e")})

        response = self.client.get(
            reverse(
                "tickets:get", args=[user1_id, "00000000-0000-0000-0000-000000000002"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Ticket non trouvé")})

        response = self.client.get(
            reverse(
                "tickets:get", args=[user1_id, "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "user": "user1",
                "identity": "",
                "token": "00000000-0000-0000-0000-000000000001",
                "status": "VA",
                "tournament": "Tournament",
                "team": None,
            },
        )

    def test_scan(self) -> None:
        """
        Test the `scan` API endpoint.
        """
        tourney = Tournament.objects.all()[0]
        create_ticket("user1", "00000000-0000-0000-0000-000000000001", tourney)
        create_ticket(
            "user2",
            "00000000-0000-0000-0000-000000000002",
            tourney,
            ticket_status=Ticket.Status.CANCELLED,
        )
        create_ticket(
            "user3",
            "00000000-0000-0000-0000-000000000003",
            tourney,
            ticket_status=Ticket.Status.SCANNED,
        )

        response = self.client.get(
            reverse("tickets:scan", args=["00000000-0000-0000-0000-000000000001"])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("user")

        response = self.client.get(
            reverse("tickets:scan", args=["00000000-0000-0000-0000-000000000001"])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("admin")

        response = self.client.get(
            reverse("tickets:scan", args=["00000000-0000-0000-0000-000000000001"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"success": True})

        response = self.client.get(reverse("tickets:scan", args=["invalid-uuid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"err": _("UUID invalide")})

        response = self.client.get(
            reverse("tickets:scan", args=["00000000-0000-0000-0000-000000000000"])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Ticket non trouvé")})

        response = self.client.get(
            reverse("tickets:scan", args=["00000000-0000-0000-0000-000000000002"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"err": _("Ticket annulé")})

        response = self.client.get(
            reverse("tickets:scan", args=["00000000-0000-0000-0000-000000000003"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"err": _("Ticket déjà scanné")})

    def test_qrcode(self) -> None:
        """
        Test the `qrcode` API endpoint.
        """
        tourney = Tournament.objects.all()[0]
        create_ticket(
            "user1", "00000000-0000-0000-0000-000000000001", tourney
        )

        response = self.client.get(
            reverse("tickets:qrcode", args=["00000000-0000-0000-0000-000000000001"])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("user")

        response = self.client.get(
            reverse("tickets:qrcode", args=["00000000-0000-0000-0000-000000000001"])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Ticket non trouvé")})

        self.login("user1")

        response = self.client.get(reverse("tickets:qrcode", args=["invalid-uuid"]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"err": _("UUID invalide")})

        response = self.client.get(
            reverse("tickets:qrcode", args=["00000000-0000-0000-0000-000000000002"])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Ticket non trouvé")})

        response = self.client.get(
            reverse("tickets:qrcode", args=["00000000-0000-0000-0000-000000000001"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "</svg>")
