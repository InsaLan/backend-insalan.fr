from rest_framework import serializers

from .models import Partner


class PartnerSerializer(serializers.ModelSerializer[Partner]):
    class Meta:
        model = Partner
        fields = ["id", "name", "url", "logo", "partner_type"]
