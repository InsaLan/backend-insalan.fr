"""Admin handlers for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django.contrib import admin
from django.utils.translation import gettext as _

from .models import Event, Tournament, Game, Team, Player, Manager, Caster


class EventAdmin(admin.ModelAdmin):
    """Admin handler for Events"""

    list_display = ("id", "name", "description", "year", "month", "ongoing")
    search_fields = ["name", "year", "month", "ongoing"]


admin.site.register(Event, EventAdmin)


class GameAdmin(admin.ModelAdmin):
    """Admin handler for Games"""

    list_display = ("id", "name")
    search_fields = ["name"]


admin.site.register(Game, GameAdmin)


class TournamentAdmin(admin.ModelAdmin):
    """Admin handler for Tournaments"""

    list_display = ("id", "name", "event", "game", "is_announced", "cashprizes")
    search_fields = ["name", "event", "game"]


admin.site.register(Tournament, TournamentAdmin)


class TeamAdmin(admin.ModelAdmin):
    """Admin handler for Team"""

    list_display = ("id", "name", "tournament", "validated")
    search_fields = ["name", "tournament"]


admin.site.register(Team, TeamAdmin)


class PlayerAdmin(admin.ModelAdmin):
    """Admin handler for Player Registrations"""

    list_display = ("id", "user", "team", "payment_status", "ticket")
    search_fields = ["user", "team", "payment_status"]


admin.site.register(Player, PlayerAdmin)


class ManagerAdmin(admin.ModelAdmin):
    """Admin handler for Manager Registrations"""

    list_display = ("id", "user", "team", "payment_status", "ticket")
    search_fields = ["user", "team", "payment_status"]


admin.site.register(Manager, ManagerAdmin)

class CasterAdmin(admin.ModelAdmin):
    """Admin handler for tournament Casters"""

    list_display = ("id", "name", "tournament")
    search_fields = ["name", "tournament"]

admin.site.register(Caster, CasterAdmin)
