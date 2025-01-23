"""
    Views for the pizza module
    WORK IN PROGRESS:
    - missing tests
"""

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import Serializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.pizza import serializers
from .models import Pizza, TimeSlot, Order, PizzaExport

class ReadOnly(permissions.BasePermission):
    """Read-Only permissions"""
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

    @swagger_auto_schema(
        responses={
            201: serializers.PizzaSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à créer une pizza")
                        )
                    }
                )

            }
        )
    def post(self, request, *args, **kwargs):
        """Create a pizza."""
        return super().post(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        """Get all pizzas."""
        return super().get(request, *args, **kwargs)

class PizzaListFull(generics.ListAPIView):
    """List all pizzas"""
    pagination_class = None
    queryset = Pizza.objects.all()
    serializer_class = serializers.PizzaSerializer
    permission_classes = [ReadOnly]


class PizzaDetail(generics.RetrieveUpdateDestroyAPIView):
    """Find a pizza by its id"""
    pagination_class = None
    queryset = Pizza.objects.all()
    serializer_class = serializers.PizzaSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
        responses={
            200: serializers.PizzaSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Pizza non trouvée")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """Get a pizza by its id."""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: serializers.PizzaSerializer,
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier cet pizza")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Pizza non trouvée")
                    )
                }
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """Update a pizza."""
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: serializers.PizzaSerializer,
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier cet pizza")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Pizza non trouvée")
                    )
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        """Partially update a pizza."""
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à supprimer cet pizza")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Pizza non trouvée")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """Delete a pizza."""
        return super().delete(request, *args, **kwargs)


class PizzaSearch(generics.ListAPIView):
    """Search a pizza by its name"""
    pagination_class = None
    serializer_class = serializers.PizzaSerializer
    permission_classes = [ReadOnly]

    def get_queryset(self):
        partial_name = self.request.query_params.get("q", None)
        return Pizza.objects.filter(name__contains=partial_name)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                description=_("Nom de la pizza"),
                type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("Identifiant de la pizza")
                        ),
                        "name": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Nom de la pizza")
                        ),
                        "ingredients": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_STRING
                            ),
                        ),
                        "allergens": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_STRING
                            ),
                        ),
                        "image": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Image de la pizza")
                        )
                    }
                )
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Search a pizza by its name
        """
        return super().get(request, *args, **kwargs)

class PizzaListByTimeSlot(generics.ListAPIView):
    """Group pizzas by timeslot"""
    pagination_class = PizzaPagination
    serializer_class = serializers.PizzaByTimeSlotSerializer
    queryset = TimeSlot.objects.all()
    permission_classes = [ permissions.IsAdminUser ]

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                # array of serializers.PizzaByTimeSlotSerializer
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("Identifiant du timeslot")
                        ),
                        "pizza": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description=_("Pizzas commandées pour ce timeslot")
                        ),
                        "delivery_time": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Heure de livraison")
                        ),
                        "start": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Heure de début")
                        ),
                        "end": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Heure de fin")
                        ),
                        "pizza_max": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("Nombre maximum de pizzas")
                        ),
                        "public": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description=_("Timeslot public")
                        ),
                        "ended": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description=_("Timeslot terminé")
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get pizzas ordered for a timeslot
        """
        return super().get(request, *args, **kwargs)

class PizzaListByGivenTimeSlot(generics.RetrieveAPIView):
    """Group pizzas by timeslot"""
    pagination_class = None
    permission_classes = [ReadOnly]
    serializer_class = serializers.PizzaByTimeSlotSerializer
    queryset = TimeSlot.objects.all()

    @swagger_auto_schema(
        responses={
            200: serializers.PizzaByTimeSlotSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Timeslot non trouvé")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get pizzas ordered for a timeslot
        """
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

    @swagger_auto_schema(
        responses={
            201: serializers.TimeSlotSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a timeslot
        """
        return super().post(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_INTEGER
                ),
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get all timeslots
        """
        return super().get(request, *args, **kwargs)


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
    serializer_class = serializers.TimeSlotSerializer

    @swagger_auto_schema(
        responses={
            200: serializers.TimeSlotSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Timeslot non trouvé")
                    )
                }
            )
        }
    )
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

    @swagger_auto_schema(
        responses={
            200: serializers.TimeSlotSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Timeslot non trouvé")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete a timeslot
        """
        return super().delete(request, *args, **kwargs)

class NextTimeSlot(generics.ListAPIView):
    """Find the timeslot in the same day"""
    queryset = TimeSlot.objects.all()
    permission_classes = [ReadOnly]
    serializer_class = serializers.TimeSlotSerializer

    def get(self, request, *args, **kwargs):
        # select incoming timeslot and currents timeslot in the same day
        timeslot = TimeSlot.objects.filter(
            delivery_time__gte=timezone.now().date()
        ).order_by("delivery_time")

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

    @swagger_auto_schema(
        responses={
            200: serializers.OrderIdSerializer,
            201: serializers.OrderIdSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        """Create an order."""
        try:
            return super().post(request, *args, **kwargs)
        except ValidationError as err:
            return JsonResponse({"err": str(err)},
                                status=status.HTTP_400_BAD_REQUEST)

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

    @swagger_auto_schema(
        responses={
            200: serializers.OrderSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Commande non trouvée")
                    )
                }
            )
        }
    )
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "delivered": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description=_("Commande livrée")
                )
            },
        ),
        responses={
            200: serializers.OrderSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Commande non trouvée")
                    )
                }
            )
        }
    )
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

        if "delivered" in data and data["delivered"] is False:
            order.delivered = False
            order.delivery_date = None
            order.save()
            return Response({"detail": _("Modified.")}, status=200)

        return Response({"detail": _("Bad request.")}, status=400)

    @swagger_auto_schema(
        responses={
            200: serializers.OrderSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Commande non trouvée")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete an order
        """
        return super().delete(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "delivered": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description=_("Commande livrée")
                )
            },
        ),
        responses={
            200: serializers.OrderSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Commande non trouvée")
                    )
                }
            )
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update an order
        """
        return super().put(request, *args, **kwargs)

class ExportOrder(generics.ListCreateAPIView):
    """Export an order"""
    queryset = PizzaExport.objects.all()
    permission_classes = [ permissions.IsAdminUser ]
    # body is expected to be empty
    serializer_class = Serializer

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("Identifiant de l'export")
                        ),
                        "orders": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description=_("Commandes exportées")
                        ),
                        "created_at": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Date d'export")
                        )
                    }
                )
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Timeslot non trouvé")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        if not TimeSlot.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        export = PizzaExport.objects.filter(time_slot=self.kwargs["pk"])
        serializer = serializers.PizzaExportSerializer(export, many=True).data

        for s in serializer:
            s.pop("time_slot")

            pizza_count = {}
            for order in s["orders"]:
                order = Order.objects.get(id=order)
                for pizza in order.pizza.all():
                    if pizza.name not in pizza_count:
                        pizza_count[pizza.name] = 1
                    else:
                        pizza_count[pizza.name] += 1

            s["orders"] = pizza_count

        return Response(serializer)

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description=_("Identifiant de l'export")
                        ),
                        "orders": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description=_("Commandes exportées")
                        ),
                        "created_at": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description=_("Date d'export")
                        )
                    }
                )
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Timeslot non trouvé")
                    )
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        if not TimeSlot.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        timeslot = TimeSlot.objects.get(id=self.kwargs["pk"])

        # get the list of orders
        orders = Order.objects.filter(time_slot=timeslot)

        # remove the order already exported
        for export in PizzaExport.objects.filter(time_slot=timeslot):
            orders = orders.exclude(id__in=export.orders.all())

        # if no order to export
        if orders.exists():
            # create the export
            export = PizzaExport.objects.create(time_slot=timeslot)
            export.orders.set(orders)

        # return the export (using get)
        return self.get(request, *args, **kwargs)

class ExportOrderDetails(generics.RetrieveDestroyAPIView):
    """Delete an export by its id."""

    pagination_class = None
    queryset = PizzaExport.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.PizzaExportSerializer

    @swagger_auto_schema(
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description=_("Identifiant de l'export")
                    ),
                    "orders": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description=_("Commandes exportées")
                    ),
                    "created_at": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Date d'export")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Timeslot non trouvé")
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """Get an export by its id."""
        if not PizzaExport.objects.filter(id=self.kwargs["pk"]).exists():
            return Response({"detail": _("Not found.")}, status=404)
        export = PizzaExport.objects.get(id=self.kwargs["pk"])
        serializer = serializers.PizzaExportSerializer(export).data

        pizza_count = {}
        for order in serializer["orders"]:
            order = Order.objects.get(id=order)
            for pizza in order.pizza.all():
                if pizza.name not in pizza_count:
                    pizza_count[pizza.name] = 1
                else:
                    pizza_count[pizza.name] += 1

        serializer["orders"] = pizza_count
        return Response(serializer)

    @swagger_auto_schema(
        responses={
            204: openapi.Response(description=_("Export supprimé.")),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à supprimer cet export.")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Export non trouvé.")
                    )
                }
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        """Delete an export."""
        return super().delete(request, *args, **kwargs)
