from django.contrib import admin

from .models import Ticket


class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "token")
    search_fields = ["user"]


admin.site.register(Ticket, TicketAdmin)
