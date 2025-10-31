""" Serializers for pizza models"""

from __future__ import annotations

from decimal import Decimal
from datetime import timedelta
from typing import Any, List, TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import Pizza, Order, TimeSlot, PizzaOrder, PizzaExport, PaymentMethod

if TYPE_CHECKING:
    from django_stubs_ext import ValuesQuerySet


DUPLICATED_ORDER_DELTA_TIME: int = 1  # minutes


class PizzaSerializer(serializers.ModelSerializer[Pizza]):
    """Serializer for a pizza model"""
    image = serializers.ImageField(required=False)

    class Meta:
        model = Pizza
        fields = "__all__"


class PizzaIdSerializer(serializers.Serializer[Pizza]):
    """Serializer to verify a list of pizza IDs"""

    def to_representation(self, instance: Pizza) -> int:
        """Turn a Django object into a serialized representation"""
        return instance.id


class OrderSerializer(serializers.ModelSerializer[Order]):
    """ Serializer for an order"""
    pizza = List
    user = serializers.CharField(required=False, source="get_username")

    class Meta:
        model = Order
        read_only_fields = ("id", )
        fields = ("id", "user", "time_slot", "pizza", "payment_method", "price", "paid",
                  "created_at", "delivered", "delivery_date")

class CreateOrderSerializer(serializers.ModelSerializer[Order]):
    """ Serializer for an order"""
    pizza = serializers.ListField(required=True)
    type = serializers.CharField(required=True)

    class Meta:
        model = Order
        read_only_fields = ("id",)
        fields = ("id", "user", "time_slot", "pizza", "type", "payment_method")

    def create(self, validated_data: Any) -> Order:
        """Create an order"""
        price_type = validated_data.pop('type')
        pizza = validated_data.pop("pizza")
        if "payment_method" not in validated_data:
            payment_method = PaymentMethod.CB
        else:
            payment_method = validated_data["payment_method"]

        price: Decimal
        if payment_method == PaymentMethod.FR:
            price = Decimal(0)
        elif price_type == "staff":
            price = TimeSlot.objects.get(id=validated_data["time_slot"].id).staff_price * len(pizza)
        elif price_type == "player":
            price = TimeSlot.objects.get(
                id=validated_data["time_slot"].id
            ).player_price * len(pizza)
        else:
            price = TimeSlot.objects.get(
                id=validated_data["time_slot"].id
            ).external_price * len(pizza)
        validated_data["price"] = price

        # check if the order is a duplicate
        for order in Order.objects.filter(
            user=validated_data.get("user"),
            time_slot=validated_data["time_slot"].id,
            payment_method=payment_method,
            price=float(price),
            created_at__gt=timezone.now() - timedelta(minutes=DUPLICATED_ORDER_DELTA_TIME)
        ):
            if sorted(order.get_pizza_ids()) == sorted(pizza):
                raise ValidationError("duplicated order")

        order = Order.objects.create(**validated_data)
        for p in pizza:
            PizzaOrder.objects.create(order=order, pizza=Pizza.objects.get(id=p))
        return order

    def to_representation(self, instance: Order) -> Any:
        """Turn a Django object into a serialized representation"""
        return OrderSerializer(instance).data


class OrderIdSerializer(serializers.ModelSerializer[Order]):
    """ Serializer for an order"""

    class Meta:
        """
        Serializer for an order
        """
        model = Order
        fields = ("id", )

    def to_representation(self, instance: Order) -> int:
        """Turn a Django object into a serialized representation"""
        return instance.id


class TimeSlotSerializer(serializers.ModelSerializer[TimeSlot]):
    """Serializer for a timeslot model"""
    orders = serializers.ListField(required=False, source="get_orders_id")

    class Meta:
        model = TimeSlot
        fields = "__all__"


class TimeSlotIdSerializer(serializers.ModelSerializer[TimeSlot]):
    """Serializer for a timeslot model"""

    class Meta:
        """
        Serializer for a timeslot model
        """
        model = TimeSlot
        fields = ("id", )

    def to_representation(self, instance: TimeSlot) -> int:
        """Turn a Django object into a serialized representation"""
        return instance.id


class PizzaByTimeSlotSerializer(serializers.ModelSerializer[TimeSlot]):
    pizza = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = ("id", "pizza", "delivery_time", "start", "end", "pizza_max", "public", "ended")

    def get_pizza(self, obj: TimeSlot) -> dict[int, int]:
        result: dict[int, int] = {}
        # for each pizza type in the timeslot, count the number of pizza ordered
        pizzas = PizzaOrder.objects.filter(
            order__time_slot__id=obj.id
        ).values("pizza__id").distinct()
        for pizza in pizzas:
            result[pizza["pizza__id"]] = PizzaOrder.objects.filter(
                order__time_slot__id=obj.id,
                pizza__id=pizza["pizza__id"]
            ).count()
        return result


class PizzaExportSerializer(serializers.ModelSerializer[PizzaExport]):
    """Serializer for a pizza model"""
    orders = serializers.SerializerMethodField()

    class Meta:
        model = PizzaExport
        fields = "__all__"

    def get_orders(self, obj: PizzaExport) -> ValuesQuerySet[Order, int]:
        return obj.get_orders_id()
