"""
This module defines the URL patterns for the tickets app.

It includes the following URL patterns:
- get/<str:username>/<str:token>: Maps to the 'get' view function.
- scan/<str:token>: Maps to the 'scan' view function.
- qrcode/<str:token>: Maps to the 'qrcode' view function.
"""

from django.urls import path
from . import views

app_name = "tickets"
urlpatterns = [
    path("get/<str:user_id>/<str:token>/", views.get, name="get"),
    path("scan/<str:token>/", views.scan, name="scan"),
    path("qrcode/<str:token>/", views.qrcode, name="qrcode"),
    path("generate/<str:token>/", views.generate_pdf, name="generate"),
    path("pay/", views.pay, name="pay"),
    path("unpaid/", views.unpaid, name="unpaid"),
]
