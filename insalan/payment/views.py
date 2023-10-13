import json
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from os import getenv
import requests
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction, TransactionStatus, Product
from .serializers import TransactionSerializer
from datetime import date
from .tokens import Tokens
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render
import insalan.payment.serializers as serializers
from django.http import HttpResponseRedirect
from .models import Product, Transaction
import logging

logger = logging.getLogger(__name__)
class ProductList(generics.ListAPIView):
    paginator = None
    serializer_class =  serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
    paginator = None
    serializer_class= serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

class TransactionList(generics.ListAPIView):
    paginator = None
    serializer_class =serializers.TransactionSerializer
    queryset = Transaction.objects.all().order_by('last_modification_date')
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
class ReturnView(generics.ListAPIView):
    pass
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
        data['payer'] = payer.id
        logger.debug(f"data in view = {data}") # contient des données
        transaction = serializers.TransactionSerializer(data=data)
        transaction.is_valid()
        logger.debug(transaction.validated_data)
        if transaction.is_valid(raise_exception=True):
            transaction_obj = transaction.save()
            # helloasso intent
            helloasso_amount = int(transaction_obj.amount * 100) # helloasso reads prices in cents
            HELLOASSO_URL = getenv('HELLOASSO_ENDPOINT')
            intent_body = {
                    "totalAmount": helloasso_amount,
                    "initialAmount": helloasso_amount,
                    "itemName": str(transaction_obj.id),
                    "backUrl":   f"{getenv('HELLOASSO_BACK_URL')}?id={transaction_obj.id}",
                    "errorUrl":  f"{getenv('HELLOASSO_ERROR_URL')}?id={transaction_obj.id}",
                    "returnUrl": f"{getenv('HELLOASSO_RETURN_URL')}?id={transaction_obj.id}",
                    "containsDonation": False,
                    "payer": {
                        "firstName": payer.first_name,
                        "lastName": payer.last_name,
                        "email": payer.email,
                    },
            }
            headers = {
               'authorization': 'Bearer ' + token.get_token(),
                'Content-Type': 'application/json',
            }

            checkout_init = requests.post(f"{HELLOASSO_URL}/v5/organizations/insalan-test/checkout-intents", data=json.dumps(intent_body), headers=headers)# initiate a helloasso intent
            logger.debug(checkout_init.text)
            redirect_url = checkout_init.json()['redirectUrl']
            logger.debug(intent_body)
            return HttpResponseRedirect(redirect_to=redirect_url)
        return JsonResponse({'problem': 'oui'})
        #return HttpResponseRedirect(checkout_init.redirectUrl)


    """
    # lets parse the request
    user=request.user
    for asked_product in user_request_body:
        try:
            product = Product.objects.get(pk=asked_product[id])
            product_list.append(product)
            if asked_product == user_request_body.pop():
                name+=product.name
            else :
                name+=product.name + ", "
            # need that all product implement a Product Model (with an id as pk, and a price)
            amount += product.price
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass # do something

    transaction=Transaction(amount=amount, payer=user, products=product_list, date=date.today())
    # need to put a list field of product in Transaction model

    # lets init a checkout to helloasso
    url = static_urls.get_checkout_url()
    headers = {
        'authorization': 'Bearer ' + tokens.get_token(),
        'Content-Type': 'application/json',
    }
    request_status=False
    while request_status!=True:
        checkout_init=requests.post(url = url, headers=headers, data=json.dumps(body))
        if checkout_init.status_code==200:
            request_status=True
        elif checkout_init.status_code==401:
            tokens.refresh()
        elif checkout_init.status_code==403:
            pass # cry, problem concerning the perms of the token
        elif checkout_init.status_code==400:
            pass # the value are false
        else:
            pass
    return HttpResponseRedirect(redirect_to=json.loads(checkout_init.text)['id'])
@csrf_exempt
class validate_payment(request, id):
    Transaction.objects.get(id=id).payment_status=TransactionStatus.SUCCEDED

class get_transactions(request):
    transactions=TransactionSerializer(Transaction.objects.all(), many=True)
    return JsonResponse(transactions.data)

"""



