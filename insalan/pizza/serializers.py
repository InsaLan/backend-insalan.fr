""" Serializers for pizza models"""
from rest_framework import serializers

from .models import Pizza, Order, TimeSlot, PizzaOrder, PizzaExport, PaymentMethod
from typing import List

class PizzaSerializer(serializers.ModelSerializer):
    """Serializer for a pizza model"""
    image = serializers.ImageField(required=False)

    class Meta:
        model = Pizza
        fields = "__all__"

class PizzaIdSerializer(serializers.Serializer):
    """Serializer to verify a list of pizza IDs"""

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id

class OrderSerializer(serializers.ModelSerializer):
    """ Serializer for an order"""
    pizza = List
    user = serializers.CharField(required=False, source="get_username")

    class Meta:
        model = Order
        read_only_fields = ("id", )
        fields = ("id", "user", "time_slot", "pizza", "payment_method", "price", "paid", "created_at", "delivered", "delivery_date")

class CreateOrderSerializer(serializers.ModelSerializer):
    """ Serializer for an order"""
    pizza = serializers.ListField(required=True)
    type = serializers.CharField(required=True)

    class Meta:
        model = Order
        read_only_fields = ("id", )
        fields = ("id", "user", "time_slot", "pizza", "type", "payment_method")

    def create(self, validated_data):
        """Create an order"""
        price_type = validated_data.pop('type')
        pizza = validated_data.pop("pizza")
        if "payment_method" not in validated_data:
            payment_method = PaymentMethod.CB
        else:
            payment_method = validated_data["payment_method"]

        if payment_method == PaymentMethod.FR:
            price = 0
        elif price_type == "staff":
            price = TimeSlot.objects.get(id=validated_data["time_slot"].id).staff_price * len(pizza)
        elif price_type == "player":
            price = TimeSlot.objects.get(id=validated_data["time_slot"].id).player_price * len(pizza)
        else:
            price = TimeSlot.objects.get(id=validated_data["time_slot"].id).external_price * len(pizza)
        validated_data["price"] = price
        order = Order.objects.create(**validated_data)
        for p in pizza:
            PizzaOrder.objects.create(order=order, pizza=Pizza.objects.get(id=p))
        return order

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return OrderSerializer(instance).data

class OrderIdSerializer(serializers.ModelSerializer):
    """ Serializer for an order"""

    class Meta:
        """
        Serializer for an order
        """
        model = Order
        fields = ("id", )
    
    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id

class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for a timeslot model"""
    orders = serializers.ListField(required=False, source="get_orders_id")

    class Meta:
        model = TimeSlot
        fields = "__all__"

class TimeSlotIdSerializer(serializers.ModelSerializer):
    """Serializer for a timeslot model"""

    class Meta:
        """
        Serializer for a timeslot model
        """
        model = TimeSlot
        fields = ("id", )

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id

class PizzaByTimeSlotSerializer(serializers.ModelSerializer):
    pizza = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = ("id", "pizza", "delivery_time", "start", "end", "pizza_max", "public", "ended")

    def get_pizza(self, obj):
        result = {}
        # for each pizza type in the timeslot, count the number of pizza ordered
        for pizza in PizzaOrder.objects.filter(order__time_slot__id=obj.id).values("pizza__id").distinct():
            result[pizza["pizza__id"]] = PizzaOrder.objects.filter(order__time_slot__id=obj.id, pizza__id=pizza["pizza__id"]).count()
        return result

class PizzaExportSerializer(serializers.ModelSerializer):
    """Serializer for a pizza model"""
    orders = serializers.SerializerMethodField()

    class Meta:
        model = PizzaExport
        fields = "__all__"

    def get_orders(self, obj):
        return obj.get_orders_id()
