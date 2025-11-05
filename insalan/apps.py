"""
This module contains the configuration for the Insalan app.
"""

import django_stubs_ext
from django.apps import AppConfig
from rest_framework import generics, serializers


class InsalanConfig(AppConfig):
    """Insalan configuration"""

    name: str = "insalan"

    def ready(self) -> None:
        # pylint: disable=line-too-long
        """
        Fix `TypeError: 'type' object is not subscriptable` issue.
        https://github.com/typeddjango/django-stubs?tab=readme-ov-file#i-cannot-use-queryset-or-manager-with-type-annotations
        """
        # pylint: enable=line-too-long
        django_stubs_ext.monkeypatch(extra_classes=[
            generics.CreateAPIView,
            generics.DestroyAPIView,
            generics.GenericAPIView,
            generics.ListAPIView,
            generics.ListCreateAPIView,
            generics.RetrieveDestroyAPIView,
            generics.RetrieveUpdateDestroyAPIView,
            generics.RetrieveAPIView,
            generics.UpdateAPIView,
            serializers.PrimaryKeyRelatedField,
            serializers.RelatedField,
        ])
