"""
This module contains views for handling content and constants in the CMS (Content Management System)
of the Insalan website.
"""

from typing import Any

from django.db.models.query import QuerySet

from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from insalan.cms import serializers

from .models import Constant, Content, File


class ContentList(generics.ListAPIView[Content]):  # pylint: disable=unsubscriptable-object
    """
    Get all content
    """
    pagination_class = None
    queryset = Content.objects.all()
    serializer_class = serializers.ContentSerializer


class ContentFetch(generics.ListAPIView[Content]):  # pylint: disable=unsubscriptable-object
    """Get a content associated to a section"""

    pagination_class = None

    serializer_class = serializers.ContentSerializer

    def get_queryset(self) -> QuerySet[Content]:
        # Ignore type error because djongo doesn't have types stubs.
        return Content.objects.filter(name=self.kwargs["name"])  # type: ignore[no-any-return]


class ConstantList(generics.ListAPIView[Constant]):  # pylint: disable=unsubscriptable-object
    """
    Get all constants
    """
    pagination_class = None
    queryset = Constant.objects.all()
    serializer_class = serializers.ConstantSerializer


class ConstantFetch(generics.ListAPIView[Constant]):  # pylint: disable=unsubscriptable-object
    """
    Get a constant associated to a section
    """
    pagination_class = None
    serializer_class = serializers.ConstantSerializer

    def get_queryset(self) -> QuerySet[Constant]:
        # Ignore type error because djongo doesn't have types stubs.
        return Constant.objects.filter(name=self.kwargs["name"])  # type: ignore[no-any-return]


class FileList(generics.ListAPIView[File]):  # pylint: disable=unsubscriptable-object
    """
    Get all files
    """
    pagination_class = None
    queryset = File.objects.all()
    serializer_class = serializers.FileSerializer


class FileFetch(generics.ListAPIView[File]):  # pylint: disable=unsubscriptable-object
    """
    Get a file by name
    """
    pagination_class = None
    serializer_class = serializers.FileSerializer

    def get_queryset(self) -> QuerySet[File]:
        # Ignore type error because djongo doesn't have types stubs.
        return File.objects.filter(name=self.kwargs["name"])  # type: ignore[no-any-return]


class FullList(APIView):
    """Get all constants, content and files."""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        constants = Constant.objects.all()
        content = Content.objects.all()
        files = File.objects.all()

        constants_serializer = serializers.ConstantSerializer(constants, many=True)
        content_serializer = serializers.ContentSerializer(content, many=True)
        files_serializer = serializers.FileSerializer(files, many=True,
                                                      context={'request': request})

        return Response({
            "constants": constants_serializer.data,
            "contents": content_serializer.data,
            "files": files_serializer.data
        })
