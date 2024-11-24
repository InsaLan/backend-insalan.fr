""" URLs for pizza
- /pizza/pizza:
   - GET: return pizza list id
   - POST: create a pizza (admin only)
- /pizza/pizza/full: list pizza available with their infos
- /pizza/pizza/<id>: get/update/delete a pizza by id
- /pizza/pizza/search?q=<str>: search a pizza by str (supports autocompletion)
- /pizza/pizza/by-timeslot/: get pizza order by timeslot
- /pizza/pizza/by-timeslot/<id>: get pizza order for a timeslot
- /pizza/timeslot/:
   - GET: return timeslot list id
   - POST: create a timeslot (admin only)
- /pizza/timeslot/full: return timeslot list with their infos
- /pizza/timeslot/<id>:
   - GET: return timeslot by id
   - DELETE: delete timeslot by id
- /pizza/timeslot/next/: get the next timeslot
- /pizza/order/:
   - GET: return order list id
   - POST: create an order (admin only, user can only use /pay)
- /pizza/order/full
- /pizza/order/<id>:
   - GET: get an order by id
   - PATCH: update an order by id
   - DELETE: delete an order by id
"""
from django.urls import path

from . import views

urlpatterns = [
   path("pizza/", views.PizzaList.as_view(), name="pizza/list"),
   path("pizza/full/", views.PizzaListFull.as_view(), name="pizza/list/full"),
   path("pizza/<int:pk>/", views.PizzaDetail.as_view(), name="pizza/detail"),
   path("pizza/search/",views.PizzaSearch.as_view(), name="pizza/fuzzy-find"),
   path("pizza/by-timeslot/", views.PizzaListByTimeSlot.as_view(), name="pizza/list/by-timeslot"),
   path("pizza/by-timeslot/<int:pk>/", views.PizzaListByGivenTimeSlot.as_view(),
        name="pizza/list/by-timeslot-id"),
   path("timeslot/", views.TimeSlotList.as_view(), name="timeslot/list"),
   path("timeslot/full/", views.TimeSlotListFull.as_view(), name="timeslot/list/full"),
   path("timeslot/<int:pk>/", views.TimeSlotDetail.as_view(), name="timeslot/detail"),
   path("timeslot/<int:pk>/export/", views.ExportOrder.as_view(), name="timeslot/export"),
   path("timeslot/next/", views.NextTimeSlot.as_view(), name="timeslot/list/next"),
   path("order/", views.OrderList.as_view(), name="order/list"),
   path("order/full/", views.OrderListFull.as_view(), name="order/list/full"),
   path("order/<int:pk>/", views.OrderDetail.as_view(), name="order/detail"),
   path("export/<int:pk>/", views.ExportOrderDelete.as_view(), name="export/delete"),
]
