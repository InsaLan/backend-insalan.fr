from rest_framework import serializers

from .models import Partner


# Serializers define the API representation.
class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ['id', 'name', 'url', 'logo', 'type']
