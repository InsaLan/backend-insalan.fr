"""Test module for the payment's models."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.forms import ValidationError
from django.test import TestCase

from insalan.pizza.models import TimeSlot
from insalan.tournament.models import Game, Event, EventTournament

from ..models import Payment, Product, ProductCategory, Transaction


TIMEZONE: ZoneInfo = ZoneInfo('Europe/Paris')


class TestProductModel(TestCase):
    """Test class for the Product model."""

    def setUp(self) -> None:
        event: Event = Event.objects.create(name="test_event")
        game: Game = Game.objects.create(name="test_game")
        self.tournament: EventTournament = EventTournament.objects.create(
            event=event,
            game=game,
        )
        self.time_slot: TimeSlot = TimeSlot.objects.create(
            delivery_time=datetime(2026, 3, 7, 21, tzinfo=TIMEZONE),
            start=datetime(2026, 3, 7, 12, tzinfo=TIMEZONE),
            end=datetime(2026, 3, 7, 19, 30, tzinfo=TIMEZONE),
            pizza_max=100,
        )
        self.product = Product.objects.create(
            price=Decimal(10.0),
            name="test_product",
            desc="test description",
            category=ProductCategory.REGISTRATION_PLAYER,
            associated_tournament=self.tournament,
            associated_timeslot=self.time_slot,
            available_from=datetime(2025, 12, 1, tzinfo=TIMEZONE),
            available_until=datetime(2026, 3, 6, tzinfo=TIMEZONE),
        )

    def test_create_product(self) -> None:
        """Tests create a product object."""
        self.assertEqual(self.product.price, Decimal(10.0))
        self.assertEqual(self.product.name, "test_product")
        self.assertEqual(self.product.desc, "test description")
        self.assertEqual(
            self.product.category,
            ProductCategory.REGISTRATION_PLAYER,
        )
        self.assertEqual(self.product.associated_tournament, self.tournament)
        self.assertEqual(self.product.associated_timeslot, self.time_slot)
        self.assertEqual(
            self.product.available_from,
            datetime(2025, 12, 1, tzinfo=TIMEZONE),
        )
        self.assertEqual(
            self.product.available_until,
            datetime(2026, 3, 6, tzinfo=TIMEZONE),
        )

    def test_name_too_long(self) -> None:
        """Tests that product name can't be too long."""
        self.product.name = "A" * 1025
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_name_empty(self) -> None:
        """Tests that product name can't be empty."""
        self.product.name = ""
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_desc_too_long(self) -> None:
        """Tests that product description can't be too long."""
        self.product.desc = "A" * 1025
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_desc_empty(self) -> None:
        """Tests that product description can't be empty."""
        self.product.desc = ""
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_can_be_bought_now(self) -> None:
        """Tests the can_be_bought_now method."""
        with patch(
            'django.utils.timezone.now',
            return_value=datetime(2025, 11, 30, tzinfo=TIMEZONE),
        ) as mock_now:
            self.assertFalse(self.product.can_be_bought_now())
        mock_now.assert_called_once_with()

        with patch(
            'django.utils.timezone.now',
            return_value=datetime(2026, 2, 1, tzinfo=TIMEZONE),
        ) as mock_now:
            self.assertTrue(self.product.can_be_bought_now())
        mock_now.assert_called_once_with()

        with patch(
            'django.utils.timezone.now',
            return_value=datetime(2026, 3, 7, tzinfo=TIMEZONE),
        ) as mock_now:
            self.assertFalse(self.product.can_be_bought_now())
        mock_now.assert_called_once_with()


class TestPaymentModel(TestCase):
    """Test class for the Payment model."""

    def test_create_payment(self) -> None:
        """Tests create a payment object."""
        transaction: Transaction = Transaction.objects.create(
            creation_date=datetime(2026, 1, 30, tzinfo=TIMEZONE),
            last_modification_date=datetime(2026, 1, 31, tzinfo=TIMEZONE),
        )
        payment: Payment = Payment.objects.create(
            id=10,
            transaction=transaction,
            amount=Decimal(10.0)
        )
        self.assertEqual(payment.id, 10)
        self.assertEqual(payment.transaction, transaction)
        self.assertEqual(payment.amount, Decimal(10.0))
