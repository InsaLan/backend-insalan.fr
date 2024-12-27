"""Views for the Payment module"""

from decimal import Decimal
import json
import logging

import requests

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import insalan.settings as app_settings
import insalan.payment.serializers as serializers

from .models import Transaction, TransactionStatus, Product, Payment, Discount
from .tokens import Token

logger = logging.getLogger(__name__)


class ProductList(generics.ListAPIView):
    """
    Get all products
    """
    paginator = None
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: serializers.ProductSerializer,
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get all products
        """
        return super().get(request, *args, **kwargs)


class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update or delete a product
    """
    paginator = None
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: serializers.ProductSerializer,
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get a product
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=serializers.ProductSerializer,
        responses={
            200: serializers.ProductSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Produit non trouvé")
                    )
                }
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update a product
        """
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: serializers.ProductSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Produit non trouvé")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a product
        """
        return super().delete(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=serializers.ProductSerializer,
        responses={
            200: serializers.ProductSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Produit non trouvé")
                    )
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update a product
        """
        return super().patch(request, *args, **kwargs)

class TransactionList(generics.ListAPIView):
    """
    Get all transactions
    """
    paginator = None
    serializer_class = serializers.TransactionSerializer
    queryset = Transaction.objects.all().order_by("last_modification_date")
    permission_classes = [permissions.IsAdminUser]


class TransactionPerId(generics.RetrieveAPIView):
    """
    Get a transaction by its ID
    """
    paginator = None
    serializer_class = serializers.TransactionSerializer
    queryset = Transaction.objects.all()
    permission_classes = [permissions.IsAdminUser]


class CreateProduct(generics.CreateAPIView):
    """
    Create a product
    """
    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        request_body=serializers.ProductSerializer,
        responses={
            200: serializers.ProductSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a product
        """
        return super().post(request, *args, **kwargs)

class Notifications(APIView):
    """
    Notifications view
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "metadata": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "uuid": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("UUID of the transaction")
                        )
                    }
                ),
                "eventType": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=_("Type of event")
                ),
                "data": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description=_("Data of the event")
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_BOOLEAN,
                        description=_("Notification received")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            )
        }
    )
    def post(self, request):
        """Notification POST"""

        data = request.data
        if not data.get("metadata") or not data["metadata"].get("uuid"):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Access to .metadata.uuid is verified
        uuid = data["metadata"]["uuid"]
        try:
            trans_obj = Transaction.objects.get(id=uuid)
        except Transaction.DoesNotExist:
            logger.error("Unable to find transaction %s", uuid)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ntype = data.get("eventType")  # defaults to None
        data = data.get("data", {})

        if ntype == "Order":
            # From "Order", get the payments
            # Check that the id is an integer
            order_id = data.get("id")
            if not isinstance(order_id, int):
                logger.error(
                    "Invalid ID for Order event, except integer, got %s", order_id
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)

            logger.info("Tied transaction %s to order ID %s", trans_obj.id, order_id)
            trans_obj.order_id = order_id
            trans_obj.touch()
            trans_obj.save()

            payments = data.get("payments")
            if payments is None:
                logger.warning(
                    "No payment data found while trying to validate transaction %s. Is that right?",
                    order_id,
                )
                return Response(status=status.HTTP_200_OK)

            for pay_data in payments:
                pid = pay_data.get("id")
                if pid is None:
                    logger.warning(
                        "No identifier found on payment for transaction %s!!", order_id
                    )
                    continue
                amount = pay_data.get("amount")
                if amount is None:
                    logger.warning(
                        "No amount found on payment for transaction %s's payment %s!!",
                        order_id,
                        pid,
                    )
                    continue
                if not isinstance(amount, int):
                    logger.warning(
                        "Amount for payment %s of transaction %s is not an integer. This may be fine, but beware.",
                        pid,
                        order_id,
                    )
                amount = Decimal(amount) / 100
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
            pay_id = data.get("id")
            if pay_id is None:
                logger.error("Payment ID is none for payment event!")
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(pay_id, int):
                logger.error('Payment ID "%s" is not an integer')
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # The payment could be "None" if we haven't received "Order" yet
            pay_objs = list(Payment.objects.filter(id=pay_id)) + [None]
            pay_obj = pay_objs[0]
            if pay_obj is not None and pay_obj.transaction != trans_obj:
                logger.error(
                    "Mismatch! Payment %s is known to belong to transaction %s but HA metadata says %s",
                    pay_id,
                    trans_obj.id,
                    pay_obj.transaction.id,
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)

            order_id = data.get("order", {}).get("id")
            if order_id is None:
                logger.error(
                    "Payment %s has no order field or no order.id field", pay_id
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(order_id, int):
                logger.error("Payment %s has an order.id field that is not int", pay_id)
                return Response(status=status.HTTP_400_BAD_REQUEST)

            if pay_obj is not None and trans_obj.order_id != order_id:
                logger.error(
                    "Mismatch! Payment %s is known to belong to transaction %s but HA data says %s",
                    pay_id,
                    trans_obj.order_id,
                    order_id,
                )
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if pay_obj is None:
                logger.warning(
                    "Validating transaction %s based on payment %s to be generated later",
                    trans_obj.id,
                    pay_id,
                )

            # Check the state
            state = data.get("state")
            if state == "Authorized":
                # Ok we should be good now
                trans_obj.validate_transaction()

            elif state in ["Refused", "Unknown"]:
                # This code should show that a payment failed
                trans_obj.fail_transaction()

            elif state in ["Refunded"]:
                # Refund
                trans_obj.refund_transaction()

            else:
                logger.warning(
                    'Payment %s shows status "%s" unknown or already assigned',
                    pay_id,
                    state,
                )

        else:
            logger.error("Unrecognized payment notification event type %s", ntype)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class PayView(generics.CreateAPIView):
    """
    Pay view
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    queryset = Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer

    def create(self, request):
        """Process a payment request"""
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
            
            amount = transaction_obj.amount
            
            # If the user has a discount for some products, apply them
            for product in transaction_obj.products.all():
                discounts = Discount.objects.filter(user=payer, product=product, used=False)
                if discounts.exists():
                    discount = discounts.first()
                    amount = transaction_obj.amount - discount.discount
                    # Add the discount to the transaction object
                    transaction_obj.discounts.add(discount)

            # helloasso intent
            helloasso_amount = int(
                amount * 100
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
                timeout=45,
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description=_("Montant à payer")
                ),
                "product": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("ID du produit")
                ),
                "payer": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("ID de l'utilisateur")
                ),
                "metadata": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description=_("Métadonnées")
                )
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(
                        type=openapi.TYPE_BOOLEAN,
                        description=_("Paiement effectué")
                    ),
                    "redirect_url": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("URL de redirection")
                    )
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données de transaction invalides")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """Process a payment request"""
        return super().post(request, *args, **kwargs)
