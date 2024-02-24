from rest_framework import generics, permissions

from .models import Partner
from .serializers import PartnerSerializer

from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return request.method in permissions.SAFE_METHODS


class PartnerList(generics.ListCreateAPIView):
    paginator = None
    queryset = Partner.objects.all().order_by("id")
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
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
    def post(self, request, *args, **kwargs):
        """
        Create a partner
        """
        return super().post(request, *args, **kwargs)
    
    @swagger_auto_schema(
        responses={
            200: PartnerSerializer,
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get all partners
        """
        return super().get(request, *args, **kwargs)

class PartnerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    @swagger_auto_schema(
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
    def get(self, request, *args, **kwargs):
        """
        Get a partner
        """
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
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
    def put(self, request, *args, **kwargs):
        """
        Update a partner
        """
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
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
    def patch(self, request, *args, **kwargs):
        """
        Partially update a partner
        """
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
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
    def delete(self, request, *args, **kwargs):
        """
        Delete a partner
        """
        return super().delete(request, *args, **kwargs)
