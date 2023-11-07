from rest_framework import generics
from .models import Constant, Content
import insalan.cms.serializers as serializers


class ContentList(generics.ListAPIView):
    pagination_class = None
    queryset = Content.objects.all()
    serializer_class = serializers.ContentSerializer


class ContentFetch(generics.ListAPIView):
    """Get a content associated to a section"""

    pagination_class = None

    serializer_class = serializers.ContentSerializer

    def get_queryset(self):
        return Content.objects.filter(name=self.kwargs["name"])


class ConstantList(generics.ListAPIView):
    pagination_class = None
    queryset = Constant.objects.all()
    serializer_class = serializers.ConstantSerializer


class ConstantFetch(generics.ListAPIView):
    pagination_class = None
    serializer_class = serializers.ConstantSerializer

    def get_queryset(self):
        return Constant.objects.filter(name=self.kwargs["name"])
