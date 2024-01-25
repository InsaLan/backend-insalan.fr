""" Views for the pizza module"""
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Pizza, TimeSlot, PizzaOrder, Order
from .serializers import PizzaSerializer

class ReadOnly(permissions.BasePermission):
    def has_permissions(self, request, view) -> bool:
        return request.method in permissions.SAFE_METHODS


class PizzaListFull(generics.ListCreateAPIView):
    pagination_class = None
    queryset = Pizza.objects.all().order_by("name")
    serializer_class = PizzaSerializer
    permissions_classes = [permissions.IsAdminUser | ReadOnly]

class PizzaDetail(generics.ListAPIView):
    """Find a pizza by its id"""
    #TODO: return 404 when no pizza found
    pagination_class = None
    serializer_class = PizzaSerializer

    def get_queryset(self):
         return Pizza.objects.filter(id=self.kwargs["id"]) 

class PizzaSearch(generics.ListAPIView):
    pagination_class = None
    serializer_class = PizzaSerializer

    def get_queryset(self):
        partial_name = self.request.query_params.get("q", None)
        return Pizza.objects.filter(name__contains=partial_name)

class OrderDetail(generics.ListAPIView):
    pagination_class = None
    serializer_class = OrderSerializer

    permissions_classes = [ permissions.IsAdminUser ]

    def get_queryset(self):
        queryset = Order.objects.filter(id=self.kwargs["id"])

class PizzaListByOrder(generics.ListAPiView):
    pass

class PizzaListByTimeSlot(generics.ListAPIView):
    pass
