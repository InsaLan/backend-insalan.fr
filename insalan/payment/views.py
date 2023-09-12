import json
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from os import getenv
import requests
from .models import Transaction
from datetime import date

from django.shortcuts import render

# Create your views here.


def pay(request):
    # lets parse the request
    user_request_body = json.loads(request.body)
    product_list=[]
    amount=0
    name=""
    user=request.user #not that but this is the idea
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
    url = f"https://api.helloasso.com/v5/organizations/{getenv('HELLOASSO_NAME')}/checkout-intents"
    body = {
        "totalAmount": amount,
        "initialAmount": amount,
        "itemName": name[:255],
        "backUrl": getenv("BACK_URL"),
        "errorUrl": getenv("ERROR_URL"),
        "returnUrl": getenv("RETURN_URL"),
        "containsDonation": False,
        "payer": {
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
        },
        "metadata" :{
            "id": transaction.id,
        },
    }
    token=request.

    # need to put BACK_URL, ERROR_URL and RETURN_URL in .env






