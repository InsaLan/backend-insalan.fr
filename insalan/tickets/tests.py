import uuid

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Ticket
from insalan.tournament.models import Event, Game, Tournament
from insalan.user.models import User


def create_ticket(
    username: str,
    token: str,
    tourney: Tournament,
    status: Ticket.Status = Ticket.Status.VALID,
) -> None:
    user = User.objects.create_user(
        username=username,
        password=username,
        email=f"{username}@example.com",
    )
    Ticket.objects.create(
        user=user, token=uuid.UUID(token), status=status, tournament=tourney
    )


class TicketTestCase(TestCase):
    def setUp(self) -> None:
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
        token = uuid.UUID("00000000-0000-0000-0000-000000000003")
        with self.assertRaises(Ticket.DoesNotExist):
            Ticket.objects.get(token=token)


class Ticket_TODO(APITestCase):
    def setUp(self) -> None:
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
        self.assertTrue(self.client.login(username=username, password=username))

    def test_get(self) -> None:
        tourney = Tournament.objects.all()[0]
        create_ticket("user1", "00000000-0000-0000-0000-000000000001", tourney)

        response = self.client.get(
            reverse(
                "tickets:get", args=["user1", "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("user")

        response = self.client.get(
            reverse(
                "tickets:get", args=["user1", "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.login("admin")

        response = self.client.get(
            reverse("tickets:get", args=["user1", "invalid-uuid"])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"err": _("UUID invalide")})

        response = self.client.get(
            reverse(
                "tickets:get", args=["user2", "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Utilisateur⋅ice non trouvé⋅e")})

        response = self.client.get(
            reverse(
                "tickets:get", args=["user1", "00000000-0000-0000-0000-000000000002"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"err": _("Ticket non trouvé")})

        response = self.client.get(
            reverse(
                "tickets:get", args=["user1", "00000000-0000-0000-0000-000000000001"]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "user": "user1",
                "token": "00000000-0000-0000-0000-000000000001",
                "status": "VA",
            },
        )

    def test_scan(self) -> None:
        tourney = Tournament.objects.all()[0]
        create_ticket("user1", "00000000-0000-0000-0000-000000000001", tourney)
        create_ticket(
            "user2",
            "00000000-0000-0000-0000-000000000002",
            tourney,
            status=Ticket.Status.CANCELLED,
        )
        create_ticket(
            "user3",
            "00000000-0000-0000-0000-000000000003",
            tourney,
            status=Ticket.Status.SCANNED,
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
