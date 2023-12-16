"""
This module contains views for handling content and constants in the CMS (Content Management System) of the Insalan website.
"""
from rest_framework import generics

from insalan.cms import serializers

from .models import Constant, Content


class ContentList(generics.ListAPIView):
    """
    Get all content
    """
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
    """
    Get all constants
    """
    pagination_class = None
    queryset = Constant.objects.all()
    serializer_class = serializers.ConstantSerializer


class ConstantFetch(generics.ListAPIView):
    """
    Get a constant associated to a section
    """
    pagination_class = None
    serializer_class = serializers.ConstantSerializer

    def get_queryset(self):
        return Constant.objects.filter(name=self.kwargs["name"])
