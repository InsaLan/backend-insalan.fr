"""
This module contains the admin configuration for the Ticket model in the Insalan application.
"""
from django.utils.translation import gettext as _
from django.contrib import admin
from django.contrib import messages

from insalan.settings import EMAIL_AUTH
from insalan.mailer import MailManager
from .models import Ticket


class TicketAdmin(admin.ModelAdmin):
    """
    Admin class for the Ticket model
    """
    list_display = ("id", "user", "status", "tournament", "token")
    search_fields = ["user__username", "user__email", "tournament__name", "token"]
    actions = ["send_tickets_to_mail"]

    @admin.action(description=_("Envoyer les tickets par mail"))
    def send_tickets_to_mail(self, request, queryset):
        """
        Action to send tickets to mail
        """
        for ticket in queryset:
            MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"]).send_ticket_mail(ticket.user, ticket)
        messages.info(request, _("Les tickets sélectionnés sont en cours d'envoi."))

admin.site.register(Ticket, TicketAdmin)
