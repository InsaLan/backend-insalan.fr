from rest_framework import serializers
from .models import Transaction, TransactionStatus, Product

class TransactionSerializer(serializers.ModelSerializer):
    products = serializers.ListField(required=True) 
    class Meta:
        model=Transaction
        fields = ['payer', 'amount', 'payment_status', 'date']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
