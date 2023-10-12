from rest_framework import serializers
from .models import Transaction, TransactionStatus, Product
from insalan.user.models import User
import logging

logger = logging.getLogger(__name__)

class TransactionSerializer(serializers.ModelSerializer):
    payer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model=Transaction
        fields = "__all__"
        read_only_fields = ['amount', 'payer', 'payment_status', 'creation_date', 'last_modification_date']
    
    def create(self, validated_data):
        """ Create a transaction with products based on the request"""
        logger.debug(f"in the serializer {validated_data}")
        transaction_obj = Transaction.new(**validated_data)
        return transaction_obj

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"



