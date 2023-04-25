from rest_framework import generics, permissions

from .models import Partner
from .serializers import PartnerSerializer


class ReadOnly(permissions.BasePermission):

    def has_permission(self, request, view) -> bool:
        return request.method in permissions.SAFE_METHODS


class PartnerList(generics.ListCreateAPIView):
    queryset = Partner.objects.all().order_by('id')
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]


class PartnerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]
