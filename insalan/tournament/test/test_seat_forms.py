import json
from django.forms import ValidationError
from django.test import TestCase

from insalan.tournament.models import (
    Event,
    EventTournament,
    Game,
    Team,
    Seat,
    SeatSlot,
)

from insalan.tournament.admin import EventForm, TournamentForm, GameForm, TeamForm


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

        self.tournament = EventTournament.objects.create(
            name="Tourney 1", game=self.game_one, event=self.evobj
        )
        self.tournament_two = EventTournament.objects.create(
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

        self.team = Team.objects.create(tournament=self.tournament, name="Test Team")

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

        # another event with seats/slots
        evobj2 = Event.objects.create(
            name="Test Event 2",
            description="This is a test",
            year=2022,
            month=12,
            ongoing=False,
        )
        seats2 = [
            Seat.objects.create(event=evobj2, x=x, y=y)
            for x in range(10, 30, 4)
            for y in range(10, 30, 4)
        ]

        tournament2 = EventTournament.objects.create(
            name="Tourney 2", game=self.game_one, event=evobj2
        )

        slots2 = [
            SeatSlot.objects.create(tournament=tournament2)
            for _ in range(len(seats2[:: self.game_one.players_per_team]))
        ]

        for slot, seats in zip(
            slots2,
            [
                seats2[i : i + self.game_one.players_per_team]
                for i in range(0, len(seats2), self.game_one.players_per_team)
            ],
        ):
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
            data={
                "name": "Test Event",
                "year": 2021,
                "month": 12,
                "seats": json.dumps([(seat.x, seat.y) for seat in self.seats])
            },
        )
        form.full_clean()
        form.save()
        self.assertEqual(set(Seat.objects.filter(event=self.evobj)), set(self.seats))

    def test_event_form_deletes_removed_seats(self):
        form = EventForm(
            instance=self.evobj,
            data={
                "name": "Test Event",
                "year": 2021,
                "month": 12,
                "seats": json.dumps([(seat.x, seat.y) for seat in self.seats[5:]])
            },
        )
        form.full_clean()
        form.save()
        self.assertEqual(
            set(Seat.objects.filter(event=self.evobj)), set(self.seats[5:])
        )

    def test_event_form_creates_added_seats(self):
        ls = [(seat.x, seat.y) for seat in self.seats]
        ls += [(x, 7) for x in range(1, 7)]
        form = EventForm(instance=self.evobj, data={
            "name": "Test Event",
            "year": 2021,
            "month": 12,
            "seats": json.dumps(ls)
        })
        form.full_clean()
        form.save()
        self.seats += [Seat.objects.get(event=self.evobj, x=x, y=y) for (x, y) in ls]
        self.assertEqual(set(Seat.objects.filter(event=self.evobj)), set(self.seats))

    def test_tournament_form_sends_data_to_frontend(self):
        # form should only send data for its own event
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

    def test_tournament_resets_slots_if_event_changed(self):
        evobj2 = Event.objects.create(
            name="Test Event 2",
            description="This is a test",
            year=2022,
            month=12,
            ongoing=False,
        )

        self.assertTrue(SeatSlot.objects.filter(tournament=self.tournament).exists())

        form = TournamentForm(
            instance=self.tournament,
            data={"event": evobj2.id},
        )
        form.full_clean()
        form.clean()

        self.assertFalse(SeatSlot.objects.filter(tournament=self.tournament).exists())

    def test_tournament_resets_slots_if_game_changed_new_nb_players(self):
        game = Game.objects.create(name="Test Game", players_per_team=4)

        self.assertTrue(SeatSlot.objects.filter(tournament=self.tournament).exists())

        form = TournamentForm(
            instance=self.tournament,
            data={"game": game.id},
        )
        form.full_clean()
        form.clean()

        self.assertFalse(SeatSlot.objects.filter(tournament=self.tournament).exists())

    def test_tournament_keeps_slots_if_game_changed_same_nb_players(self):
        game = Game.objects.create(name="Test Game", players_per_team=5)

        self.assertTrue(SeatSlot.objects.filter(tournament=self.tournament).exists())

        form = TournamentForm(
            instance=self.tournament,
            data={"game": game.id},
        )
        form.full_clean()
        form.clean()

        self.assertTrue(SeatSlot.objects.filter(tournament=self.tournament).exists())

    def test_tournament_form_invalid_if_wrong_nb_seats_in_slot(self):
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

    def test_tournament_form_invalid_if_seat_used_more_than_once(self):
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

    def test_tournament_form_deletes_removed_slots(self):
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

    def test_tournament_form_adds_new_slots(self):
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

    def test_tournament_form_modifies_edited_slots(self):
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

    def test_game_form_resets_slots_if_players_per_team_changed(self):
        self.assertTrue(SeatSlot.objects.filter(tournament=self.tournament).exists())

        form = GameForm(
            instance=self.game_one,
            data={"players_per_team": 4},
        )

        form.full_clean()
        form.clean()

        self.assertFalse(SeatSlot.objects.filter(tournament=self.tournament).exists())

    def test_team_form_sets_seat_slot(self):
        self.assertIsNone(self.team.seat_slot)

        form = TeamForm(
            instance=self.team,
            data={"seat_slot": self.slots1[0].id},
        )
        form.full_clean()
        form.clean()

        self.assertEqual(self.team.seat_slot.id, self.slots1[0].id)

    def test_team_form_ignores_seat_slot_if_wrong_tournament(self):
        self.assertIsNone(self.team.seat_slot)

        form = TeamForm(
            instance=self.team,
            data={"seat_slot": self.slots2[0].id},
        )
        form.full_clean()
        form.clean()

        # here, the slot object is not found because the query set for that
        # field is filtered for that specific tournament. it seems the passed
        # value is silently discarded
        self.assertIsNone(self.team.seat_slot)

    def test_team_form_ignores_seat_slot_if_slot_taken(self):
        self.assertIsNone(self.team.seat_slot)

        slot = SeatSlot.objects.create(tournament=self.tournament)
        slot.seats.set(self.slots1[0].seats.all())

        team2 = Team.objects.create(
            tournament=self.tournament, name="Test Team 2", seat_slot=slot
        )
        team2.save()

        form = TeamForm(
            instance=self.team,
            data={"seat_slot": slot.id},
        )
        form.full_clean()
        form.clean()

        # here, the slot object is not found because the query set for that
        # field is filtered to include only unused slots. it seems the passed
        # value is silently discarded
        self.assertIsNone(self.team.seat_slot)

    def test_team_form_invalid_if_wrong_nb_seats_in_slot(self):
        self.assertIsNone(self.team.seat_slot)

        slot = SeatSlot.objects.create(tournament=self.tournament)
        slot.seats.set(self.slots1[0].seats.all()[:4])

        form = TeamForm(
            instance=self.team,
            data={"seat_slot": slot.id},
        )

        self.assertFalse(form.is_valid())
