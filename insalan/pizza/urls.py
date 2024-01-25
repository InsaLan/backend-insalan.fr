""" URLs for pizza
- /pizza: return pizza list id
- /pizza/full: list pizza available with their infos
- /pizza/<id>: get/update/delete a pizza by id
- /pizza/search?q=<str>: search a pizza by str (supports autocompletion)
- /pizza/by-order: get pizza order by order
- /pizza/by-timeslot: get pizza order by timeslot
- /pizza/timeslot/<timestamp>
- /pizza/timeslot/next/
- /pizza/order/
"""
from django.urls import path

from . import views

urlpatterns = [
   path("", views.PizzaListFull.as_view(), name="list"), 
   path("<int:id>/", views.PizzaDetail.as_view(), name="detail"),
   path("search/",views.PizzaSearch.as_view(), name="fuzzy-find"), 
   path("by-order/", views.PizzaListByOrder.as_view(), name="list/by-order"),
   path("by-timeslot/", views.PizzaListByTimeslot.as_view(), name="list/by-timeslot"),
   path("order/<int:order_id>", views.OrderDetail.as_view(), name="order/detail"),
]
