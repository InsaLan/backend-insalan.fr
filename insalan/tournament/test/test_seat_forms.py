import json
from django.core.exceptions import ValidationError
from django.test import TestCase

from insalan.tournament.models import (
    Event,
    Tournament,
    Game,
    Seat,
    SeatSlot,
)

from insalan.tournament.admin import EventForm, TournamentForm


class SeatsFieldTestCase(TestCase):
    """
    Test validation and behavior of the TournamentForm and EventForm with regards to seats and seat slots
    """

    def setUp(self) -> None:
        self.evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )

        self.game_one = Game.objects.create(name="Test Game One", players_per_team=5)
        self.game_two = Game.objects.create(name="Test Game Two", players_per_team=3)

        self.tournament = Tournament.objects.create(
            name="Tourney 1", game=self.game_one, event=self.evobj
        )
        self.tournament_two = Tournament.objects.create(
            name="Tourney 2", game=self.game_two, event=self.evobj
        )

        self.seats = [
            Seat.objects.create(event=self.evobj, x=x, y=y)
            for x in range(1, 7)
            for y in range(1, 7)
        ]

        seats1 = self.seats[:15]
        seats2 = self.seats[15:30]
        self.available_seats = self.seats[30:]

        self.slots1 = [
            SeatSlot.objects.create(tournament=self.tournament)
            for _ in range(len(seats1[:: self.game_one.players_per_team]))
        ]
        self.slots2 = [
            SeatSlot.objects.create(tournament=self.tournament_two)
            for _ in range(len(seats2[:: self.game_two.players_per_team]))
        ]

        seats1_groups = [
            seats1[i : i + self.game_one.players_per_team]
            for i in range(0, len(seats1), self.game_one.players_per_team)
        ]
        seats2_groups = [
            seats2[i : i + self.game_two.players_per_team]
            for i in range(0, len(seats1), self.game_two.players_per_team)
        ]

        for slot, seats in zip(self.slots1, seats1_groups):
            slot.seats.set(seats)

        for slot, seats in zip(self.slots2, seats2_groups):
            slot.seats.set(seats)

    def test_event_form_sends_data_to_frontend(self):
        form = EventForm(instance=self.evobj)
        self.assertEqual(
            form.fields["canvas_params"].initial["oldSeats"],
            [(seat.x, seat.y) for seat in self.seats],
        )

    def test_event_form_doesnt_modify_if_no_changes(self):
        form = EventForm(
            instance=self.evobj,
            data={"seats": json.dumps([(seat.x, seat.y) for seat in self.seats])},
        )
        form.full_clean()
        self.assertEqual(set(Seat.objects.filter(event=self.evobj)), set(self.seats))

    def test_event_form_deletes_removed_seats(self):
        form = EventForm(
            instance=self.evobj,
            data={"seats": json.dumps([(seat.x, seat.y) for seat in self.seats[5:]])},
        )
        form.full_clean()
        self.assertEqual(
            set(Seat.objects.filter(event=self.evobj)), set(self.seats[5:])
        )

    def test_event_form_creates_added_seats(self):
        ls = [(seat.x, seat.y) for seat in self.seats]
        ls += [(x, 7) for x in range(1, 7)]
        form = EventForm(instance=self.evobj, data={"seats": json.dumps(ls)})
        form.full_clean()
        self.seats += [Seat.objects.get(event=self.evobj, x=x, y=y) for (x, y) in ls]
        self.assertEqual(set(Seat.objects.filter(event=self.evobj)), set(self.seats))

    def test_tournament_form_sends_data_to_frontend(self):
        form = TournamentForm(instance=self.tournament)

        expected = {
            "eventSeats": [(seat.x, seat.y) for seat in self.seats],
            "unavailableSeats": [
                (seat.x, seat.y) for slot in self.slots2 for seat in slot.seats.all()
            ],
            "seatsPerSlot": self.tournament.game.players_per_team,
            "seatSlots": {
                slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
                for slot in self.slots1
            },
        }
        for key in expected:
            self.assertEqual(form.fields["canvas_params"].initial[key], expected[key])

    def test_tournament_form_raises_error_if_wrong_nb_seats_in_slot(self):
        seat = Seat.objects.create(event=self.evobj, x=10, y=10)
        slots = {
            slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
            for slot in self.slots1
        }
        slots[self.slots1[0].id].append((seat.x, seat.y))

        form = TournamentForm(
            instance=self.tournament,
            data={"seat_slots": json.dumps(slots)},
        )
        self.assertFalse(form.is_valid())

    def test_tournament_raises_error_if_seat_used_more_than_once(self):
        seat = self.seats[0]
        slots = {
            slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
            for slot in self.slots1
        }
        slots[self.slots1[0].id].append((seat.x, seat.y))

        form = TournamentForm(
            instance=self.tournament,
            data={"seat_slots": json.dumps(slots)},
        )
        self.assertFalse(form.is_valid())

    def test_tournament_deletes_removed_slots(self):
        slots = {
            slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
            for slot in self.slots1
        }
        slots.pop(self.slots1[0].id)

        form = TournamentForm(
            instance=self.tournament,
            data={"seat_slots": json.dumps(slots)},
        )
        form.full_clean()
        form.clean()

        self.assertEqual(
            set(SeatSlot.objects.filter(tournament=self.tournament)),
            set(self.slots1[1:]),
        )

    def test_tournament_adds_new_slots(self):
        slots = {
            slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
            for slot in self.slots1
        }
        slots[42069] = [(seat.x, seat.y) for seat in self.available_seats[:5]]

        form = TournamentForm(
            instance=self.tournament,
            data={"seat_slots": json.dumps(slots)},
        )
        form.full_clean()
        form.clean()

        self.assertEqual(
            len(SeatSlot.objects.filter(tournament=self.tournament)),
            len(self.slots1) + 1,
        )

        new_slot = (
            set(SeatSlot.objects.filter(tournament=self.tournament)) - set(self.slots1)
        ).pop()

        self.assertEqual(
            set(new_slot.seats.all()),
            set(self.available_seats[:5]),
        )

    def test_tournament_modifies_edited_slots(self):
        slots = {
            slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
            for slot in self.slots1
        }

        slots[self.slots1[0].id] = [
            (seat.x, seat.y) for seat in self.available_seats[:5]
        ]

        form = TournamentForm(
            instance=self.tournament,
            data={"seat_slots": json.dumps(slots)},
        )
        form.full_clean()
        form.clean()

        self.assertEqual(
            set(SeatSlot.objects.filter(tournament=self.tournament)),
            set(self.slots1),
        )

        slot = SeatSlot.objects.get(id=self.slots1[0].id)

        self.assertEqual(
            set(slot.seats.all()),
            set(self.available_seats[:5]),
        )
