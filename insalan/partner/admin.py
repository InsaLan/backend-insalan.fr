from django.contrib import admin

from .models import Partner


class PartnerAdmin(admin.ModelAdmin[Partner]):  # pylint: disable=unsubscriptable-object
    list_display = ("id", "name", "url", "logo", "partner_type")
    search_fields = ["name"]


admin.site.register(Partner, PartnerAdmin)
