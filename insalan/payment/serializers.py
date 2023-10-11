from rest_framework import serializers
from .models import Transaction, TransactionStatus, Product
import logging

class TransactionSerializer(serializers.ModelSerializer):
    products = serializers.ListField(required=True, source="get_products_id")

    class Meta:
        model=Transaction
        fields = ['payer', 'amount', 'payment_status', 'date', 'products']
        read_only_fields = ['amount']
    
    def create(self, validated_data):
        """ Create a transaction with products based on the request"""
        amount = 0
        transaction_obj = Transaction.objects.create(**validated_data)
        products = validated_data.pop("get_products_id", [])

        print(prodcuts)
        for product in products:
            prod_obj = Product.objects.get(id=product)
            amount += prod_obj.price

        transaction_obj.amount = amount
        return transaction_obj

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"



