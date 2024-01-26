""" Views for the pizza module"""
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Pizza, TimeSlot, PizzaOrder, Order
from .serializers import PizzaSerializer, PizzaIdSerializer, OrderSerializer, TimeSlotSerializer, PizzaByOrderSerializer, TimeSlotIdSerializer, OrderIdSerializer
from rest_framework.pagination import PageNumberPagination

class ReadOnly(permissions.BasePermission):
    def has_permissions(self, request, view) -> bool:
        return request.method in permissions.SAFE_METHODS

"""
WORK IN PROGRESS: 
- missing POST, PUT, DELETE for endpoints
- missing permissions
- missing tests
"""

class PizzaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class PizzaList(generics.ListAPIView):
    """List all pizzas id"""
    pagination_class = None
    queryset = Pizza.objects.all().order_by("name")
    serializer_class = PizzaIdSerializer
    permissions_classes = [ReadOnly]

class PizzaListFull(generics.ListAPIView):
    """List all pizzas"""
    pagination_class = None
    queryset = Pizza.objects.all().order_by("name")
    serializer_class = PizzaSerializer
    permissions_classes = [ReadOnly]

class PizzaDetail(generics.RetrieveAPIView):
    """Find a pizza by its id"""
    pagination_class = None
    queryset = Pizza.objects.all().order_by("name")
    serializer_class = PizzaSerializer
    permissions_classes = [ReadOnly]

class PizzaSearch(generics.ListAPIView):
    """Search a pizza by its name"""
    pagination_class = None
    serializer_class = PizzaSerializer

    def get_queryset(self):
        partial_name = self.request.query_params.get("q", None)
        return Pizza.objects.filter(name__contains=partial_name)


class PizzaListByGivenOrder(generics.RetrieveAPIView):
    """Group pizzas by order"""
    pagination_class = None
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

class PizzaListByTimeSlot(generics.ListAPIView):
    """Group pizzas by timeslot"""
    pagination_class = PizzaPagination
    serializer_class = PizzaByOrderSerializer
    queryset = TimeSlot.objects.all()

class PizzaListByGivenTimeSlot(generics.RetrieveAPIView):
    """Group pizzas by timeslot"""
    pagination_class = None

    def get(self, request, *args, **kwargs):
        timeslot = TimeSlot.objects.get(id=self.kwargs["pk"])
        serializer = PizzaByOrderSerializer(timeslot)
        # only return the pizzas ordered
        return Response(serializer.data)

class TimeSlotList(generics.ListAPIView):
    """List all timeslots"""
    pagination_class = PizzaPagination
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotIdSerializer
    permissions_classes = [ReadOnly]


class TimeSlotListFull(generics.ListAPIView):
    """List all timeslots"""
    pagination_class = PizzaPagination
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permissions_classes = [ReadOnly]


class TimeSlotDetail(generics.RetrieveAPIView):
    """Find a timeslot by its id"""
    queryset = TimeSlot.objects.all()
    permissions_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        timeslot = TimeSlot.objects.get(id=self.kwargs["pk"])
        serializer = TimeSlotSerializer(timeslot, context={"request": request}).data

        order_serialized = []
        for order in serializer["orders"]:
            order = Order.objects.get(id=order)
            order_serializer = OrderSerializer(order).data
            order_serializer.pop("time_slot")
            order_serialized.append(order_serializer)
        serializer["orders"].clear()
        serializer["orders"] = order_serialized

        serializer.pop("player_product")
        serializer.pop("staff_product")
        serializer.pop("external_product")

        return Response(serializer)

class NextTimeSlot(generics.ListAPIView):
    """Find the next timeslot"""
    queryset = TimeSlot.objects.all()
    permissions_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        # select incoming timeslot and currents timeslot
        timeslot = TimeSlot.objects.filter(ended=False).order_by("start")

        serializers = []
        for ts in timeslot:
            serializer = TimeSlotSerializer(ts, context={"request": request}).data

            serializer.pop("player_product")
            serializer.pop("staff_product")
            serializer.pop("external_product")

            serializers.append(serializer)

        return Response(serializers)
    
class OrderList(generics.ListAPIView):
    """List all orders"""
    queryset = Order.objects.all()
    serializer_class = OrderIdSerializer
    permissions_classes = [ReadOnly]

class OrderListFull(generics.ListAPIView):
    """List all orders"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permissions_classes = [ReadOnly]

class OrderDetail(generics.RetrieveAPIView):
    """Find an order by its id"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permissions_classes = [ReadOnly]
    queryset = Order.objects.all()

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=self.kwargs["pk"])
        serializer = OrderSerializer(order, context={"request": request}).data

        timeslot = TimeSlot.objects.get(id=serializer["time_slot"])
        timeslot_serializer = TimeSlotSerializer(timeslot).data
        timeslot_serializer.pop("player_product")
        timeslot_serializer.pop("staff_product")
        timeslot_serializer.pop("external_product")
        serializer["time_slot"] = timeslot_serializer

        return Response(serializer)
