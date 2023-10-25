"""Views for the Payment module"""

import json
import logging

import requests

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

import insalan.settings as app_settings
import insalan.payment.serializers as serializers

from .models import Transaction, TransactionStatus, Product
from .tokens import Token

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


class Notifications(APIView):
    """
    Notifications view
    """
    def post(self, request):
        data = request.data
        if not data.get("metadata") or not data["metadata"].get("uuid"):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        uuid = data["metadata"]["uuid"]
        trans_obj = Transaction.objects.get(id=uuid)
        if trans_obj is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ntype = data["eventType"]
        data = data["data"]

        logger.warn("NTYPE: %s", ntype)
        logger.warn("DATA: %s", data)

        if ntype == "Order":
            # Check that the order is still unfinished
            pass
        elif ntype == "Payment":
            # Check how the payments are going, this should signal a completed
            # or cancelled/refunded payment
            pass
        elif ntype == "Form":
            # Those notifications are mostly useless, it's about changes to the
            # org
            pass

        return Response(status=status.HTTP_200_OK)


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

        transaction_obj = Transaction.objects.filter(
            payment_status=TransactionStatus.PENDING, id=trans_id, intent_id=checkout_id
        )
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

        # Execute hooks
        transaction_obj.run_success_hooks()

        return Response(status=status.HTTP_200_OK)


class ErrorView(generics.ListAPIView):
    pass


class PayView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer

    def create(self, request):
        token = Token.get_instance()
        payer = request.user
        data = request.data.copy()
        data["payer"] = payer.id
        transaction = serializers.TransactionSerializer(data=data)
        transaction.is_valid()
        logger.debug(transaction.validated_data)
        if transaction.is_valid(raise_exception=True):
            transaction_obj = transaction.save()
            # helloasso intent
            helloasso_amount = int(
                transaction_obj.amount * 100
            )  # helloasso reads prices in cents
            intent_body = {
                "totalAmount": helloasso_amount,
                "initialAmount": helloasso_amount,
                "itemName": str(transaction_obj.id),
                "backUrl": app_settings.HA_BACK_URL,
                "errorUrl": app_settings.HA_ERROR_URL,
                "returnUrl": app_settings.HA_RETURN_URL,
                "containsDonation": False,
                "payer": {
                    "firstName": payer.first_name,
                    "lastName": payer.last_name,
                    "email": payer.email,
                },
                "metadata": {
                    "uuid": str(transaction_obj.id),
                }
            }
            headers = {
                "authorization": "Bearer " + token.get_token(),
                "Content-Type": "application/json",
            }

            checkout_init = requests.post(
                f"{app_settings.HA_URL}/v5/organizations/{app_settings.HA_ORG_SLUG}/checkout-intents",
                data=json.dumps(intent_body),
                headers=headers,
                timeout=1,
            )  # initiate a helloasso intent
            logger.debug(checkout_init.text)
            checkout_json = checkout_init.json()
            redirect_url = checkout_json["redirectUrl"]
            intent_id = checkout_json["id"]
            transaction_obj.intent_id = intent_id
            transaction_obj.save()
            logger.debug(intent_body)

            # Execute hooks
            transaction_obj.run_prepare_hooks()

            return HttpResponseRedirect(redirect_to=redirect_url)
        return JsonResponse(
            {"err": _("Données de transaction invalides")},
            status=status.HTTP_400_BAD_REQUEST,
        )
