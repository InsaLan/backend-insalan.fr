import json
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from os import getenv
import requests
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction, TransactionStatus, Product
from .serializers import TransactionSerializer
from datetime import date
from .tokens import tokens
from rest_framework import generics, permissions

from django.shortcuts import render
import insalan.payment.serializers as serializers
from .models import Product, Transaction

# Create your views here.

class ProductList(generics.ListAPIView):
    pagination = None
    serializer_class =  serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
    pagination = None
    serializer_class= serializers.ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAdminUser]

class TransactionList(generics.ListAPIView):
    pagination = None
    serializer_class =serializers.TransactionSerializer
    queryset = Transaction.objects.all()
    permission_classes = [permissions.IsAdminUser]

class TransactionPerId(generics.RetrieveAPIView):
    pagination = None
    serializer_class = serializers.TransactionSerializer
    queryset = Transaction.objects.all().order_by('date')
    permission_classes = [permissions.IsAdminUser]


class CreateProduct(generics.CreateAPIView):
    pass

class PayView(generics.CreateAPIView):
    pass
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
    body = {
        "totalAmount": amount,
        "initialAmount": amount,
        "itemName": name[:255],
        "backUrl": static_urls.get_back_url()+"/"+transaction.id,
        "errorUrl": static_urls.get_error_url(),
        "returnUrl": static_urls.get_return_url(),
        "containsDonation": False,
        "payer": {
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
        },
    }
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



