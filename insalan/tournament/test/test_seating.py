from django.db.utils import IntegrityError
from django.test import TestCase

from insalan.tournament.models import (
    Event,
    EventTournament,
    Game,
    Seat,
    SeatSlot,
)

from insalan.tournament.admin import SeatSlotForm


class SeatTestCase(TestCase):
    """
    Test the seat model
    """

    def setUp(self) -> None:
        self.evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        self.evobj_two = Event.objects.create(
            name="Test Event 2",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )

    def test_seats_unique_with_coords_and_event(self) -> None:
        """
        Test that seats are unique with regards to coordinates and the event
        """
        Seat.objects.create(event=self.evobj, x=1, y=1)
        Seat.objects.create(event=self.evobj_two, x=1, y=1)
        Seat.objects.create(event=self.evobj, x=2, y=1)
        Seat.objects.create(event=self.evobj, x=1, y=2)

        self.assertRaises(
            IntegrityError, Seat.objects.create, event=self.evobj, x=1, y=1
        )


class SeatSlotFormTestCase(TestCase):
    """
    Test the seat slot form
    """

    def setUp(self) -> None:
        self.evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        self.evobj_two = Event.objects.create(
            name="Test Event 2",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )

        self.game_one = Game.objects.create(name="Test Game One", players_per_team=5)
        self.game_two = Game.objects.create(name="Test Game Two", players_per_team=3)

        self.tournament = EventTournament.objects.create(
            name="Tourney 1", game=self.game_one, event=self.evobj
        )
        self.tournament_two = EventTournament.objects.create(
            name="Tourney 2", game=self.game_two, event=self.evobj_two
        )

        self.seats = [
            Seat.objects.create(event=self.evobj, x=1, y=1),
            Seat.objects.create(event=self.evobj, x=1, y=2),
            Seat.objects.create(event=self.evobj, x=1, y=3),
            Seat.objects.create(event=self.evobj, x=1, y=4),
            Seat.objects.create(event=self.evobj, x=1, y=5),
            Seat.objects.create(event=self.evobj, x=1, y=6),
        ]

        self.seats_two = [
            Seat.objects.create(event=self.evobj_two, x=1, y=1),
            Seat.objects.create(event=self.evobj_two, x=1, y=2),
            Seat.objects.create(event=self.evobj_two, x=1, y=3),
            Seat.objects.create(event=self.evobj_two, x=1, y=4),
            Seat.objects.create(event=self.evobj_two, x=1, y=5),
            Seat.objects.create(event=self.evobj_two, x=1, y=6),
        ]

    def test_number_of_seats_is_valid(self) -> None:
        """
        Test that the number of seats is valid
        """

        # too few seats, invalid
        form = SeatSlotForm(
            data={"tournament": self.tournament, "seats": self.seats[:4]}
        )
        self.assertFalse(form.is_valid())

        # correct number of seats, valid
        form = SeatSlotForm(
            data={"tournament": self.tournament, "seats": self.seats[:5]}
        )
        self.assertTrue(form.is_valid())

        # too many seats, invalid
        form = SeatSlotForm(
            data={"tournament": self.tournament, "seats": self.seats[:6]}
        )
        self.assertFalse(form.is_valid())

    def test_all_seats_are_in_same_event(self) -> None:
        # seats in different events, invalid
        form = SeatSlotForm(
            data={
                "tournament": self.tournament_two,
                "seats": [self.seats[0]] + self.seats_two[:2],
            }
        )
        self.assertFalse(form.is_valid())

        # seats in the same event, valid
        form = SeatSlotForm(
            data={"tournament": self.tournament_two, "seats": self.seats[:3]}
        )
        self.assertTrue(form.is_valid())

        form = SeatSlotForm(
            data={"tournament": self.tournament_two, "seats": self.seats_two[:3]}
        )
        self.assertTrue(form.is_valid())

    def test_no_seat_sharing_between_slots(self) -> None:
        seat_slot = SeatSlot.objects.create(tournament=self.tournament_two)
        seat_slot.seats.set(self.seats[:3])

        # seats shared between slots, invalid
        for seats in (self.seats[:3], self.seats[1:4], self.seats[2:5]):
            form = SeatSlotForm(
                data={"tournament": self.tournament_two, "seats": seats}
            )
            self.assertFalse(form.is_valid())

        # seats not shared between slots, valid
        form = SeatSlotForm(
            data={"tournament": self.tournament_two, "seats": self.seats[3:6]}
        )
        self.assertTrue(form.is_valid())
