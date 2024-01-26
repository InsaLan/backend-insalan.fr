""" Serializers for pizza models"""
from rest_framework import serializers

from .models import Pizza, Order, TimeSlot, PizzaOrder
from typing import List

class PizzaSerializer(serializers.ModelSerializer):
    """Serializer for a pizza model"""
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
        fields = ("id", "user", "time_slot", "pizza", "price", "paid", "created_at", "delivered", "delivery_date")

class OrderIdSerializer(serializers.ModelSerializer):
    """ Serializer for an order"""
    
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
    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id

class PizzaByOrderSerializer(serializers.ModelSerializer):
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