from django.contrib import admin

from unfold.admin import ModelAdmin # type: ignore
from .models import Partner


class PartnerAdmin(ModelAdmin):  # type: ignore
    list_display = ("id", "name", "url", "logo", "partner_type")
    search_fields = ["name"]


admin.site.register(Partner, PartnerAdmin)
