from rest_framework import serializers
from .models import Transaction, TransactionStatus

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Transaction
        fields = ['payer', 'amount', 'payment_status', 'date']