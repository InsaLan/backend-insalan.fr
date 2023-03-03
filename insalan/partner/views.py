from rest_framework import generics

from .models import Partner
from .serializers import PartnerSerializer


class PartnerList(generics.ListCreateAPIView):
    queryset = Partner.objects.all().order_by('id')
    serializer_class = PartnerSerializer


class PartnerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
