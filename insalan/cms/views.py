"""
This module contains views for handling content and constants in the CMS (Content Management System) of the Insalan website.
"""
from rest_framework import generics
from rest_framework.response import Response

from insalan.cms import serializers

from .models import Constant, Content, File


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

class FileList(generics.ListAPIView):
    """
    Get all files
    """
    pagination_class = None
    queryset = File.objects.all()
    serializer_class = serializers.FileSerializer

class FileFetch(generics.ListAPIView):
    """
    Get a file by name
    """
    pagination_class = None
    serializer_class = serializers.FileSerializer

    def get_queryset(self):
        return File.objects.filter(name=self.kwargs["name"])

class FullList(generics.ListAPIView):
    """
    Get all constants, content and files
    """
    pagination_class = None
    queryset = Constant.objects.all()
    serializer_class = serializers.ConstantSerializer

    def get(self, request, *args, **kwargs):
        constants = Constant.objects.all()
        content = Content.objects.all()
        files = File.objects.all()

        constants_serializer = serializers.ConstantSerializer(constants, many=True)
        content_serializer = serializers.ContentSerializer(content, many=True)
        files_serializer = serializers.FileSerializer(files, many=True)

        return Response({
            "constants": constants_serializer.data,
            "content": content_serializer.data,
            "files": files_serializer.data
        })
