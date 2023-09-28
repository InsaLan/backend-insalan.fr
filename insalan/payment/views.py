import json
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from os import getenv
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction, TransactionStatus, Product
from .serializers import TransactionSerializer
from datetime import date
from .tokens import tokens

from django.shortcuts import render

# Create your views here.


def pay(request):
    # lets parse the request
    user_request_body = json.loads(request.body)
    product_list=[]
    amount=0
    name=""
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
    url = f"https://{getenv('HELLOASSO_URL')}/organizations/{getenv('ASSOCIATION_NAME')}/checkout-intents"
    body = {
        "totalAmount": amount,
        "initialAmount": amount,
        "itemName": name[:255],
        "backUrl": "back_url"+"/"+transaction.id,
        "errorUrl": "error_url",
        "returnUrl": "return_url",
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
    # redirect to json.loads(checkout_init.text)['id']
@csrf_exempt
def validate_payment(request, id):
    Transaction.objects.get(id=id).payment_status=TransactionStatus.SUCCEDED

def get_transactions(request):
    transactions=TransactionSerializer(Transaction.objects.all(), many=True)
    return JsonResponse(transactions.data)





