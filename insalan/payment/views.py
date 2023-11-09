"""Views for the Payment module"""

from decimal import Decimal
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

from .models import Transaction, TransactionStatus, Product, Payment
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
        """Notification POST"""

        data = request.data
        if not data.get("metadata") or not data["metadata"].get("uuid"):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        uuid = data["metadata"]["uuid"]
        try:
            trans_obj = Transaction.objects.get(id=uuid)
        except Transaction.DoesNotExist:
            logger.error("Unable to find transaction %s", uuid)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ntype = data["eventType"]
        data = data["data"]

        # logger.debug("NTYPE: %s", ntype)
        # logger.debug("DATA: %s", data)

        if ntype == "Order":
            # From "Order", get the payments
            order_id = data["id"]
            logger.info("Tied transaction %s to order ID %s", trans_obj.id, order_id)
            trans_obj.order_id = order_id
            trans_obj.touch()
            trans_obj.save()

            for pay_data in data.get("payments", []):
                pid = pay_data["id"]
                amount = Decimal(pay_data["amount"]) / 100
                Payment.objects.create(id=pid, amount=amount, transaction=trans_obj)
                logger.info(
                    "Created payment %d tied to transaction %s", pid, trans_obj.id
                )

        elif ntype == "Form":
            # Those notifications are mostly useless, it's about changes to the
            # org
            pass
        elif ntype == "Payment":
            # Because we are in single payment, this is our signal to validate
            pay_id = data["id"]
            # The payment could be "None" if we haven't received "Order" yet
            pay_objs = list(Payment.objects.filter(id=pay_id)) + [None]
            pay_obj = pay_objs[0]
            if pay_obj is not None and pay_obj.transaction != trans_obj:
                logger.error(
                    "Mismatch! Payment %d is known to belong to transaction %s but HA metadata says %s",
                    pay_id,
                    trans_obj.id,
                    pay_obj.transaction.id,
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if pay_obj is not None and trans_obj.order_id != int(data["order"]["id"]):
                logger.error(
                    "Mismatch! Payment %d is known to belong to transaction %s but HA data says %s",
                    pay_id,
                    trans_obj.order_id,
                    data["order"]["id"],
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if pay_obj is None:
                logger.warning(
                    "Validating transaction %s based on payment %d to be generated later",
                    trans_obj.id,
                    pay_id,
                )

            # Check the state
            if data["state"] == "Authorized":
                # Ok we should be good now
                trans_obj.validate_transaction()

            elif data["state"] in ["Refused", "Unknown"]:
                # This code should show that a payment failed
                trans_obj.fail_transaction()

            elif data["state"] in ["Refunded"]:
                # Refund
                trans_obj.refund_transaction()

            else:
                logger.warning(
                    "Payment %d shows status %s unknown or already assigned",
                    pay_id,
                    data["state"],
                )

        return Response(status=status.HTTP_200_OK)


class PayView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer

    def create(self, request):
        """Process a payment request"""
        if not app_settings.DEBUG:
            return JsonResponse(
                {"err": _("API inaccessible en production")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = Token.get_instance()
        payer = request.user
        data = request.data.copy()
        data["payer"] = payer.id
        transaction = serializers.TransactionSerializer(data=data)
        transaction.is_valid()
        logger.debug(transaction.validated_data)
        if transaction.is_valid(raise_exception=True):
            transaction_obj = transaction.save()

            # Execute hooks
            go_ahead = transaction_obj.run_prepare_hooks()
            if not go_ahead:
                transaction_obj.fail_transaction()
                logger.error(
                    "Failed pre-condition on payment %s. Deleting.", transaction_obj.id
                )
                transaction_obj.delete()
                return JsonResponse(
                    {"err": _("Préconditions de paiement non remplies")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
                },
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

            logger.info("Redirectory payment to %s", redirect_url)

            return JsonResponse(
                {"success": True, "redirect_url": redirect_url},
                status=status.HTTP_200_OK,
            )
        return JsonResponse(
            {"err": _("Données de transaction invalides")},
            status=status.HTTP_400_BAD_REQUEST,
        )
