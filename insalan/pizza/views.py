"""
    Views for the pizza module
    WORK IN PROGRESS: 
    - missing tests
"""
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

import insalan.pizza.serializers as serializers
from .models import Pizza, TimeSlot, Order

class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, _view):
        return request.method in permissions.SAFE_METHODS

class PizzaPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class PizzaList(generics.ListCreateAPIView):
    """List all pizzas id"""
    pagination_class = None
    queryset = Pizza.objects.all()
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.PizzaIdSerializer
        return serializers.PizzaSerializer

class PizzaListFull(generics.ListAPIView):
    """List all pizzas"""
    pagination_class = None
    queryset = Pizza.objects.all()
    serializer_class = serializers.PizzaSerializer
    permission_classes = [ReadOnly]

class PizzaDetail(generics.RetrieveAPIView):
    """Find a pizza by its id"""
    pagination_class = None
    queryset = Pizza.objects.all()
    serializer_class = serializers.PizzaSerializer
    permission_classes = [ReadOnly]

class PizzaSearch(generics.ListAPIView):
    """Search a pizza by its name"""
    pagination_class = None
    serializer_class = serializers.PizzaSerializer
    permission_classes = [ReadOnly]

    def get_queryset(self):
        partial_name = self.request.query_params.get("q", None)
        return Pizza.objects.filter(name__contains=partial_name)

class PizzaListByTimeSlot(generics.ListAPIView):
    """Group pizzas by timeslot"""
    pagination_class = PizzaPagination
    serializer_class = serializers.PizzaByTimeSlotSerializer
    queryset = TimeSlot.objects.all()
    permission_classes = [ permissions.IsAdminUser ]

class PizzaListByGivenTimeSlot(generics.RetrieveAPIView):
    """Group pizzas by timeslot"""
    pagination_class = None
    permission_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        if not TimeSlot.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        timeslot = TimeSlot.objects.get(id=self.kwargs["pk"])
        serializer = serializers.PizzaByTimeSlotSerializer(timeslot)
        # only return the pizzas ordered
        return Response(serializer.data)

class TimeSlotList(generics.ListCreateAPIView):
    """List all timeslots"""
    pagination_class = PizzaPagination
    queryset = TimeSlot.objects.all()
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.TimeSlotIdSerializer
        return serializers.TimeSlotSerializer


class TimeSlotListFull(generics.ListAPIView):
    """List all timeslots"""
    pagination_class = PizzaPagination
    queryset = TimeSlot.objects.all()
    serializer_class = serializers.TimeSlotSerializer
    permission_classes = [ReadOnly]


class TimeSlotDetail(generics.RetrieveAPIView, generics.DestroyAPIView):
    """Find a timeslot by its id"""
    queryset = TimeSlot.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        if not TimeSlot.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        timeslot = TimeSlot.objects.get(id=self.kwargs["pk"])
        serializer = serializers.TimeSlotSerializer(timeslot, context={"request": request}).data

        order_serialized = []
        for order in serializer["orders"]:
            order = Order.objects.get(id=order)
            order_serializer = serializers.OrderSerializer(order).data
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
    permission_classes = [ReadOnly]

    def get(self, request, *args, **kwargs):
        # select incoming timeslot and currents timeslot
        timeslot = TimeSlot.objects.filter(delivery_time__gte=timezone.now()).order_by("start")

        serializers_data = []
        for ts in timeslot:
            serializer = serializers.TimeSlotSerializer(ts, context={"request": request}).data

            serializer.pop("player_product")
            serializer.pop("staff_product")
            serializer.pop("external_product")

            serializers_data.append(serializer)

        return Response(serializers_data)

class OrderList(generics.ListCreateAPIView):
    """List all orders"""
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.OrderIdSerializer
        return serializers.CreateOrderSerializer

class OrderListFull(generics.ListAPIView):
    """List all orders"""
    queryset = Order.objects.all()
    serializer_class = serializers.OrderSerializer
    permission_classes = [ permissions.IsAdminUser]

class OrderDetail(generics.RetrieveUpdateDestroyAPIView):
    """Find an order by its id"""
    queryset = Order.objects.all()
    permission_classes = [ permissions.IsAdminUser ]
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.OrderSerializer
        return serializers.CreateOrderSerializer

    def get(self, request, *args, **kwargs):
        if not Order.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        order = Order.objects.get(id=self.kwargs["pk"])
        serializer = serializers.OrderSerializer(order, context={"request": request}).data

        timeslot = TimeSlot.objects.get(id=serializer["time_slot"])
        timeslot_serializer = serializers.TimeSlotSerializer(timeslot).data
        timeslot_serializer.pop("player_product")
        timeslot_serializer.pop("staff_product")
        timeslot_serializer.pop("external_product")
        serializer["time_slot"] = timeslot_serializer

        return Response(serializer)

    def patch(self, request, *args, **kwargs):
        if not Order.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        order = Order.objects.get(id=self.kwargs["pk"])
        data = request.data

        if "delivered" in data and data["delivered"] is True:
            order.delivered = True
            order.delivery_date = timezone.now()
            order.save()
            return Response({"detail": _("Modified.")}, status=200)
        elif "delivered" in data and data["delivered"] is False:
            order.delivered = False
            order.delivery_date = None
            order.save()
            return Response({"detail": _("Modified.")}, status=200)
        else:
            return Response({"detail": _("Bad request.")}, status=400)
