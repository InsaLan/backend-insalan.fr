"""
This module contains serializers for the CMS app.

It includes serializers for Content and Constant models.
"""

from rest_framework import serializers

from .models import Content, Constant, File


class ContentSerializer(serializers.ModelSerializer):
    """Serializer for a content in the cms"""

    class Meta:
        """
        Meta class for the ContentSerializer.
        """
        model = Content
        fields = ["name", "content"]


class ConstantSerializer(serializers.ModelSerializer):
    """Serializer for a constant in the cms"""

    class Meta:
        """
        Meta class for the ConstantSerializer.
        """
        model = Constant
        fields = ["name", "value"]

class FileSerializer(serializers.ModelSerializer):
    """Serializer for a file in the cms"""

    class Meta:
        """
        Meta class for the FileSerializer.
        """
        model = File
        fields = ["name", "file"]