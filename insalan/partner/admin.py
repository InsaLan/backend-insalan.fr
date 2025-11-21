from django.contrib import admin

from unfold.admin import ModelAdmin
from .models import Partner


class PartnerAdmin(ModelAdmin[Partner]):  # pylint: disable=unsubscriptable-object
    list_display = ("id", "name", "url", "logo", "partner_type")
    search_fields = ["name"]


admin.site.register(Partner, PartnerAdmin)
