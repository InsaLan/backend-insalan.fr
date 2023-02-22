from django.contrib import admin

from .models import Partner

class PartnerAdmin(admin.ModelAdmin):

    list_display = ('name', 'url', 'logo', 'type')
    search_fields = ['name']


admin.site.register(Partner, PartnerAdmin)
