"""Admin handlers for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django.contrib import admin

from .models import Event, Tournament, Game, Team

class EventAdmin(admin.ModelAdmin):
    """Admin handler for Events"""
    list_display = ('id', 'name', 'description', 'year', 'month', 'ongoing')
    search_fields = ['name', 'year', 'month', 'ongoing']

admin.site.register(Event, EventAdmin)

class GameAdmin(admin.ModelAdmin):
    """Admin handler for Games"""
    list_display = ('id', 'name')
    search_fields = ['name']

admin.site.register(Game, GameAdmin)

class TournamentAdmin(admin.ModelAdmin):
    """Admin handler for Tournaments"""
    list_display = ('id', 'name', 'event', 'game')
    search_fields = ['name', 'event', 'game']

admin.site.register(Tournament, TournamentAdmin)

class TeamAdmin(admin.ModelAdmin):
    """Admin handler for Team"""
    list_display = ('id', 'name', 'tournament')
    search_fields = ['name', 'tournament']

admin.site.register(Team, TeamAdmin)
