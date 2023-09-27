from rest_framework import serializers

from .models import Content, Constant

class ContentSerializer(serializers.ModelSerializer):
    """ Serializer for a content in the cms """
    class Meta:
        model = Content
        fields = ["section", "content"]

class ConstantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constant
        fields = ["name", "value"]
