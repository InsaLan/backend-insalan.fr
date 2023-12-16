"""
This module contains the admin configuration for the Ticket model in the Insalan application.
"""

from django.contrib import admin

from .models import Ticket


class TicketAdmin(admin.ModelAdmin):
    """
    Admin class for the Ticket model
    """
    list_display = ("id", "user", "status", "tournament", "token")
    search_fields = ["user"]


admin.site.register(Ticket, TicketAdmin)
