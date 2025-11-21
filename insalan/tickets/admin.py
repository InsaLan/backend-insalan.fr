"""
This module contains the admin configuration for the Ticket model in the Insalan application.
"""

from __future__ import annotations

from typing import Any

from django.db.models.query import QuerySet
from django.contrib import admin, messages
from django.http import HttpRequest
from django.utils.translation import gettext as _
from unfold.admin import ModelAdmin # type: ignore

from insalan.settings import EMAIL_AUTH
from insalan.mailer import MailManager
from insalan.tournament.models.tournament import EventTournament

from .models import Ticket


class OngoingTournamentFilter(admin.SimpleListFilter):
    """
    This filter is used to only show players from the selected tournament
    """
    title = _('Tournament')
    parameter_name = 'tournament'

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin[Any]) -> list[tuple[int, str]]:
        return [(tournament.id, tournament.name)
                for tournament in EventTournament.objects.filter(event__ongoing=True)]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> QuerySet[Ticket]:
        if self.value():
            return queryset.filter(tournament_id=self.value())
        return queryset


class TicketAdmin(ModelAdmin):  # type: ignore
    """
    Admin class for the Ticket model
    """
    list_display = ("id", "user", "status", "tournament", "token")
    search_fields = ["user__username", "user__email", "tournament__name", "token"]
    list_filter = ("status", OngoingTournamentFilter)
    actions = ["send_tickets_to_mail"]

    @admin.action(description=_("Envoyer les tickets par mail"))
    def send_tickets_to_mail(self, request: HttpRequest, queryset: QuerySet[Ticket]) -> None:
        """
        Action to send tickets to mail
        """
        for ticket in queryset:
            if ticket.status == Ticket.Status.VALID:
                mailer = MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"])
                assert mailer is not None
                mailer.send_ticket_mail(
                    ticket.user,
                    ticket,
                )
        messages.info(request, _("Les tickets sélectionnés sont en cours d'envoi."))

admin.site.register(Ticket, TicketAdmin)
