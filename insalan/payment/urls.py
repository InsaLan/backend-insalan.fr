"""
This module defines the URL patterns for the payment app.

It includes URL patterns for various views related to payment, such as payment flow, notifications,
product listing, product details, creating a new product, transaction listing, and transaction details.
"""
from django.urls import path

from . import views


app_name = "payment"
urlpatterns = [
    # Flow URLs
    path("pay/", views.PayView.as_view(), name="pay"),
    path("notifications/", views.Notifications.as_view(), name="notifications"),
    # REST URLs
    path("product/", views.ProductList.as_view(), name="list-product"),
    path("product/<int:pk>/", views.ProductDetails.as_view(), name="product-details"),
    path("product/new/", views.CreateProduct.as_view(), name="new-product"),
    path("transaction/", views.TransactionList.as_view(), name="transactions"),
    path(
        "transaction/<int:pk>/", views.TransactionPerId.as_view(), name="transactions/id"
    ),
]
