""" Serializers for pizza models"""
from rest_framework import serializers

from .models import Pizza, Order

class PizzaSerializer(serializers.ModelSerializer):
    """Serializer for a pizza model"""
    class Meta:
        model = Pizza
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    """ Serializer for an order"""
    pizza = List
    class Meta:
        model = Order
        read_only_fields = ("id", )
