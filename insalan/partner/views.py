from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_yasg import openapi  # type: ignore[import]
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import]

from rest_framework import generics, permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Partner
from .serializers import PartnerSerializer


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in permissions.SAFE_METHODS


class PartnerList(generics.ListCreateAPIView[Partner]):  # pylint: disable=unsubscriptable-object
    paginator = None
    queryset = Partner.objects.all().order_by("id")
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        responses={
            200: PartnerSerializer,
            201: PartnerSerializer,
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
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a partner
        """
        return super().post(request, *args, **kwargs)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        responses={
            200: PartnerSerializer,
        }
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Get all partners
        """
        return super().get(request, *args, **kwargs)


# pylint: disable-next=unsubscriptable-object
class PartnerDetail(generics.RetrieveUpdateDestroyAPIView[Partner]):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        responses={
            200: PartnerSerializer,
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Partenaire non trouvé")
                    )
                }
            )
        }
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Get a partner
        """
        return super().get(request, *args, **kwargs)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        responses={
            200: PartnerSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Partenaire non trouvé")
                    )
                }
            )
        }
    )
    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a partner
        """
        return super().put(request, *args, **kwargs)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        responses={
            200: PartnerSerializer,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Données invalides")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Partenaire non trouvé")
                    )
                }
            )
        }
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Partially update a partner
        """
        return super().patch(request, *args, **kwargs)

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        responses={
            204: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Partenaire supprimé")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Partenaire non trouvé")
                    )
                }
            )
        }
    )
    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a partner
        """
        return super().delete(request, *args, **kwargs)
