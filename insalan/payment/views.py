"""Views for the Payment module"""

import json
import logging

from datetime import date
from os import getenv

import requests

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

import insalan.payment.serializers as serializers

from .hooks import PaymentCallbackSystem
from .models import Transaction, TransactionStatus, Product, ProductCount
from .tokens import Tokens

logger = logging.getLogger(__name__)


class ProductList(generics.ListAPIView):
    paginator = None
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]


class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
    paginator = None
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]


class TransactionList(generics.ListAPIView):
    paginator = None
    serializer_class = serializers.TransactionSerializer
    queryset = Transaction.objects.all().order_by("last_modification_date")
    permission_classes = [permissions.IsAdminUser]


class TransactionPerId(generics.RetrieveAPIView):
    paginator = None
    serializer_class = serializers.TransactionSerializer
    queryset = Transaction.objects.all()
    permission_classes = [permissions.IsAdminUser]


class CreateProduct(generics.CreateAPIView):
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]


class BackView(generics.ListAPIView):
    pass

class ReturnView(APIView):
    """View for the return"""
    def get(self, request, **kwargs):
        trans_id = request.query_params.get("id")
        checkout_id = request.query_params.get("checkoutIntentId")
        code = request.query_params.get("code")

        if None in [trans_id, checkout_id, code]:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        transaction_obj = Transaction.objects.filter(payment_status=TransactionStatus.PENDING, id=trans_id, intent_id=checkout_id)
        if len(transaction_obj) == 0:
            return Response(status=status.HTTP_403_FORBIDDEN)

        transaction_obj = transaction_obj[0]

        if code != "success":
            transaction_obj.payment_status = TransactionStatus.FAILED
            transaction_obj.touch()
            transaction_obj.save()
            return Response(status=status.HTTP_403_FORBIDDEN)

        transaction_obj.payment_status = TransactionStatus.SUCCEEDED
        transaction_obj.touch()
        transaction_obj.save()

        return Response(transaction_obj)

class ErrorView(generics.ListAPIView):
    pass


class PayView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer

    def create(self, request):
        token = Tokens()
        payer = request.user
        data = request.data.copy()
        data["payer"] = payer.id
        logger.debug(f"data in view = {data}")  # contient des données
        transaction = serializers.TransactionSerializer(data=data)
        transaction.is_valid()
        logger.debug(transaction.validated_data)
        if transaction.is_valid(raise_exception=True):
            transaction_obj = transaction.save()
            # helloasso intent
            helloasso_amount = int(
                transaction_obj.amount * 100
            )  # helloasso reads prices in cents
            HELLOASSO_URL = getenv("HELLOASSO_ENDPOINT")
            intent_body = {
                "totalAmount": helloasso_amount,
                "initialAmount": helloasso_amount,
                "itemName": str(transaction_obj.id),
                "backUrl": f"{getenv('HELLOASSO_BACK_URL')}?id={transaction_obj.id}",
                "errorUrl": f"{getenv('HELLOASSO_ERROR_URL')}?id={transaction_obj.id}",
                "returnUrl": f"{getenv('HELLOASSO_RETURN_URL')}?id={transaction_obj.id}",
                "containsDonation": False,
                "payer": {
                    "firstName": payer.first_name,
                    "lastName": payer.last_name,
                    "email": payer.email,
                },
            }
            headers = {
                "authorization": "Bearer " + token.get_token(),
                "Content-Type": "application/json",
            }

            checkout_init = requests.post(
                f"{HELLOASSO_URL}/v5/organizations/insalan-test/checkout-intents",
                data=json.dumps(intent_body),
                headers=headers,
            )  # initiate a helloasso intent
            logger.debug(checkout_init.text)
            checkout_json = checkout_init.json()
            redirect_url = checkout_json["redirectUrl"]
            intent_id = checkout_json["id"]
            transaction_obj.intent_id = intent_id
            transaction_obj.save()
            logger.debug(intent_body)
            return HttpResponseRedirect(redirect_to=redirect_url)
        return JsonResponse({"problem": "oui"})
