import logging
from typing import Any

from rest_framework import serializers

from insalan.user.models import User

from .models import Transaction, Product


logger = logging.getLogger(__name__)


class TransactionSerializer(serializers.ModelSerializer[Transaction]):

    payer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    products = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), many=True)

    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = ["amount", "payer", "payment_status", "intent_id", "creation_date",
                            "last_modification_date"]

    def create(self, validated_data: Any) -> Transaction:
        """Create a transaction with products based on the request."""
        logger.debug("in the serializer %s", validated_data)
        transaction_obj = Transaction.new(**validated_data)
        return transaction_obj


class ProductSerializer(serializers.ModelSerializer[Product]):

    class Meta:
        model = Product
        fields = "__all__"
