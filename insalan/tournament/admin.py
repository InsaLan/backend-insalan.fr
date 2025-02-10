"""Admin handlers for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

import json
from typing import Any

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    ReadOnlyPasswordHashField,
    UsernameField,
)
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet
from django.forms.models import ModelChoiceField
from django.http import Http404, HttpResponseRedirect
from django.http.request import HttpRequest
from django.template.response import TemplateResponse
from django.urls import path, resolve, reverse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import gettext as _
from django.views.decorators.debug import sensitive_post_parameters
from django.db.models import Q

from insalan.mailer import MailManager
from insalan.tournament.manage import (
    create_empty_knockout_matchs,
    create_group_matchs,
    create_swiss_matchs,
    launch_match,
)
from insalan.admin import ADMIN_ORDERING

from .models import (
    BestofType,
    Bracket,
    BracketSet,
    Caster,
    Event,
    Game,
    Group,
    GroupMatch,
    GroupTiebreakScore,
    KnockoutMatch,
    Manager,
    MatchStatus,
    PaymentStatus,
    Player,
    Score,
    Seat,
    SeatSlot,
    Seeding,
    Substitute,
    SwissMatch,
    SwissRound,
    SwissSeeding,
    Team,
    Tournament,
    TournamentMailer,
)

sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

ADMIN_ORDERING += [
    ('tournament', [
        'Event',
        'Game',
        'Tournament',
        'Team',
        'Seat',
        'SeatSlot',
        'Player',
        'Manager',
        'Substitute',
        'Caster',
        'TournamentMailer',
        'Group',
        'GroupMatch',
        'Bracket',
        'BracketMatch',
        'Knockout',
        'KnockoutMatch',
        'SwissRound',
        'SwissMatch',
        'GroupTiebreakScore'
    ]),
]

class SeatCanvasWidget(forms.Widget):
    """
    Custom widget for the seat canvas
    """
    def render(self, name, value, attrs=None, renderer=None):
        element_id = attrs["id"] if attrs else "id_" + name
        return (
            f'<input id="{element_id}" type="hidden" name="{name}" value="" />'
            '<canvas id="seat_canvas" width="900" height="900" />'
        )

class SeatCanvas(forms.Field):
    """
    Custom field for the seat canvas
    """
    widget = SeatCanvasWidget

    def clean(self, value):
        if value is None:
            return None
        value = json.loads(value)
        return value

class EventForm(forms.ModelForm):
    """
    Custom form for the Event model
    """
    seats = SeatCanvas()
    canvas_params = forms.JSONField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        seats = Seat.objects.filter(event=self.instance)
        data = {
            "cellSize": 25,
            "pickedColor": "brown",  # css colors
            "oldSeats": [(seat.x, seat.y) for seat in seats]
        }
        self.fields["canvas_params"].initial = data

    def save(self, commit: bool = True):
        """Override the save method to save seats related with the event."""
        if not self.instance.pk:
            # Force saving the instance otherwise the seats cannot be created
            # at the same time as the event.
            instance = super().save(commit=False)
            instance.save()
        else:
            instance = super().save(commit=commit)

        seats = self.cleaned_data.get("seats")

        if seats is not None:
            old_seats = Seat.objects.filter(event=instance)
            to_delete = [seat for seat in old_seats if [seat.x, seat.y] not in seats]
            to_create = [
                (x, y)
                for (x, y) in seats
                if (x, y) not in [(seat.x, seat.y) for seat in old_seats]
            ]

            for seat in to_delete:
                seat.delete()
            for (x, y) in to_create:
                seat = Seat.objects.create(event=instance, x=x, y=y)
                seat.save()

        return instance

    class Meta:
        """
        Meta class for the form
        """
        model = Event
        fields = "__all__"

class EventAdmin(admin.ModelAdmin):
    """Admin handler for Events"""

    form = EventForm

    list_display = ("id", "name", "description", "year", "month", "ongoing")
    search_fields = ["name", "year", "month", "ongoing"]

    class Media:
        css = {
            'all': ('css/seat_canvas.css',)
        }
        js = (
            'js/seat_canvas.js',
            'js/event_seat_canvas.js',
        )


admin.site.register(Event, EventAdmin)

class GameForm(forms.ModelForm):
    """
    Custom form for the Game model
    """
    def clean(self) -> dict[str, Any] | None:
        # if players_per_team changed, reset associated seat_slots
        new_players_per_team = self.cleaned_data.get("players_per_team")
        if new_players_per_team is not None and new_players_per_team != self.instance.players_per_team:
            tournaments = Tournament.objects.filter(game=self.instance)
            seat_slots = SeatSlot.objects.filter(tournament__in=tournaments)
            seat_slots.delete()

    class Meta:
        """
        Meta class for the form
        """
        model = Game
        fields = "__all__"


class GameAdmin(admin.ModelAdmin):
    """Admin handler for Games"""
    form = GameForm

    list_display = ("id", "name", "players_per_team")
    search_fields = ["name"]


admin.site.register(Game, GameAdmin)

class EventTournamentFilter(admin.SimpleListFilter):
    """
    This filter is used to only show tournaments from the selected event
    """
    title = _('Event')
    parameter_name = 'event'

    def lookups(self, request, model_admin):
        return [(event.id, event.name) for event in Event.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(event__id=self.value())
        return queryset

class GameTournamentFilter(admin.SimpleListFilter):
    """
    This filter is used to only show tournaments from the selected game
    """
    title = _('Game')
    parameter_name = 'game'

    def lookups(self, request, model_admin):
        return [(game.id, game.name) for game in Game.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(game__id=self.value())
        return queryset

class SeatSlotSelection(forms.Widget):
    """
    Custom widget for listing seat slots and allowing selection
    """
    def render(self, name, value, attrs=None, renderer=None):
        return (
            '<div style="display: flex; flex-direction: row;" >'
                '<div style="display: flex; flex-direction: column; justify-content: center;" >'
                    '<input type="button" id="id_slot_selection_create" value="Créer un slot" />'
                    '<input type="button" id="id_slot_selection_delete" value="Supprimer le slot" />'
                    '<span id="id_slot_selection_error" style="color: red; white-space: pre-wrap;"></span>'
                '</div>'
                '<select id="id_slot_selection" name="slot_selection" multiple />'
            '</div>'
        )


class TournamentForm(forms.ModelForm):
    """
    Custom form for the Tournament model
    """
    seat_slots = SeatCanvas()
    slot_selection = forms.Field(widget=SeatSlotSelection(), required=False)
    canvas_params = forms.JSONField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        seats = Seat.objects.filter(event=self.instance.event)
        seat_slots = SeatSlot.objects.filter(tournament=self.instance)

        other_tournament_slots = SeatSlot.objects.exclude(tournament=self.instance).filter(tournament__event=self.instance.event)

        data = {
            "cellSize": 25,
            "pickedColor": "lightgray",  # css colors
            "eventSeats": [(seat.x, seat.y) for seat in seats],
            "unavailableSeats": [(seat.x, seat.y) for slot in other_tournament_slots for seat in slot.seats.all()],
            "seatsPerSlot": self.instance.game.players_per_team,  # for client side validation
            "seatSlots": {
                slot.id: [(seat.x, seat.y) for seat in slot.seats.all()]
                for slot in seat_slots
            }
        }
        self.fields["canvas_params"].initial = data

    def clean(self) -> dict[str, Any] | None:
        # if event changed, reset seat_slots
        new_event = self.cleaned_data.get("event")
        if new_event is not None and new_event != self.instance.event:
            self.cleaned_data["seat_slots"] = {}

        # if game changed, reset seat_slots if different number of players
        new_game = self.cleaned_data.get("game")
        if new_game is not None and new_game.players_per_team != self.instance.game.players_per_team:
            self.cleaned_data["seat_slots"] = {}

        seat_slots = self.cleaned_data.get("seat_slots")

        if seat_slots is not None:
            # validation
            for seats in seat_slots.values():
                # Ensure that the number of seats is consistent with the tournament
                if len(seats) != self.instance.game.players_per_team:
                    raise ValidationError(
                    _("Le nombre de places est incorrect pour ce tournoi")
                    )

            # Ensure that every used seat is used only once
            other_tournament_slots = SeatSlot.objects.exclude(tournament=self.instance)
            unavailable_seats = set((seat.x, seat.y) for slot in other_tournament_slots for seat in slot.seats.all())
            all_seats = set(tuple(seat) for seats in seat_slots.values() for seat in seats)
            if unavailable_seats.intersection(all_seats):
                raise ValidationError(
                _("Les places ne peuvent pas être partagés entre plusieurs slots")
                )

            # modification
            old_slots = SeatSlot.objects.filter(tournament=self.instance)
            to_delete = old_slots.exclude(id__in=[int(ss_id) for ss_id in seat_slots])
            to_create = [seats for slot, seats in seat_slots.items() if int(slot) not in [slot.id for slot in old_slots]]

            # check remaining slots for modification
            remaining_slots = old_slots.difference(to_delete)

            for slot in to_delete:
                slot.delete()
            for seat_coords in to_create:
                slot = SeatSlot.objects.create(tournament=self.instance)
                seats = [Seat.objects.get(event=self.instance.event, x=x, y=y) for x, y in seat_coords]
                slot.seats.set(seats)
                slot.save()
            for slot in remaining_slots:
                seats = [Seat.objects.get(event=self.instance.event, x=x, y=y) for x, y in seat_slots[str(slot.id)]]
                slot.seats.set(seats)
                slot.save()

        return self.cleaned_data

    class Meta:
        """
        Meta class for the form
        """
        model = Tournament
        fields = "__all__"


class TournamentAdmin(admin.ModelAdmin):
    """Admin handler for Tournaments"""

    list_display = ("id", "name", "event", "game", "is_announced", "cashprizes", "get_occupancy")
    search_fields = ["name", "event__name", "game__name"]

    list_filter = (EventTournamentFilter,GameTournamentFilter)

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Use TournamentForm only for editing an existing tournament.
        """
        if obj is not None:
            kwargs["form"] = TournamentForm
        return super().get_form(request, obj, change, **kwargs)

    def get_occupancy(self, obj):
        """
        Returns the occupancy of the tournament
        """
        return str(Team.objects.filter(tournament=obj, validated=True).count()) + " / " + str(obj.maxTeam)

    get_occupancy.short_description = 'Remplissage'

    class Media:
        css = {
            'all': ('css/seat_canvas.css',)
        }
        js = (
            'js/seat_canvas.js',
            'js/tournament_seat_canvas.js',
        )

admin.site.register(Tournament, TournamentAdmin)

class TeamForm(forms.ModelForm):
    """Form for Team"""
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user’s password, but you can change the password using "
            '<a href="{}">this form</a>.'
        ),
    )

    class Meta:
        """Meta options for the form"""
        model = Team
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get("password")
        if password:
            password.help_text = password.help_text.format(
                f"../../{self.instance.pk}/password/"
            )
        user_permissions = self.fields.get("user_permissions")
        if user_permissions:
            user_permissions.queryset = user_permissions.queryset.select_related(
                "content_type"
            )

        seat_slot = self.fields.get("seat_slot")
        if (seat_slot and self.instance.tournament):
            seat_slot.queryset = seat_slot.queryset.filter(
                tournament=self.instance.tournament
            ).filter(
                Q(team=None) | Q(team=self.instance)
            )

    def clean(self):
        """
        validate seat slot
        """
        seat_slot = self.cleaned_data.get("seat_slot")
        tournament = self.cleaned_data.get("tournament") or self.instance.tournament

        if seat_slot is not None:
            # filters mean if it's not the same tournament, seat_slot is None => impossible
            if seat_slot.tournament.id != tournament.id:
                raise ValidationError(_("Ce slot appartient à un autre tournoi."))

            # filters mean if it's used, seat_slot is None => impossible
            if hasattr(seat_slot, "team") and seat_slot.team.id != self.instance.id:
                raise ValidationError(_("Slot déjà utilisé."))

            if seat_slot.seats.count() != tournament.game.players_per_team:
                raise ValidationError(_("Slot inadapté au tournoi."))

        return self.cleaned_data

class TeamCreationForm(forms.ModelForm):
    """
    A form that creates a team, from the given username, tournament, validation and password.
    """

    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        """
        Meta options for the form
        """
        model = Team
        fields = ("name", "tournament", "validated", "seed")
        field_classes = {"name": UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pylint: disable-next=no-member
        if self._meta.model.name in self.fields:
            # pylint: disable-next=no-member
            self.fields[self._meta.model.name].widget.attrs[
                "autofocus"
            ] = True

    def clean_password2(self):
        """
        Check that the two password entries match
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        """
        Save the provided password in hashed format
        """
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user

class TeamTournamentFilter(admin.SimpleListFilter):
    """
    This filter is used to only show teams from the selected tournament
    """
    title = _('Tournoi')
    parameter_name = 'tournament'

    def lookups(self, request, model_admin):
        return [(tournament.id, tournament.name) for tournament in Tournament.objects.filter(event__ongoing=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tournament__id=self.value())
        return queryset

class ValidatedFilter(admin.SimpleListFilter):
    """
    This filter is used to only show teams from the selected tournament
    """
    title = _('Validation')
    parameter_name = 'validated'

    def lookups(self, request, model_admin):
        return [(True, 'Validé'), (False, 'Non Validé')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(validated=self.value())
        return queryset

class TeamAdmin(admin.ModelAdmin):
    """Admin handler for Team"""

    list_display = ("id", "name", "tournament", "validated", "get_quota")
    search_fields = ["name", "tournament__name"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("name", "tournament", "validated", "password1", "password2"),
            },
        ),
    )
    form = TeamForm
    add_form = TeamCreationForm
    change_team_password_template = None

    list_filter = (TeamTournamentFilter,ValidatedFilter)

    def get_quota(self, obj):
        """
        Returns the quota of the team
        """
        return str(Player.objects.filter(team=obj).count()) + " / " + str(obj.tournament.game.players_per_team)

    get_quota.short_description = 'Nombre de Joueurs'

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, change, **defaults)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_urls(self):
        return [
            path(
                "<team_id>/password/",
                self.admin_site.admin_view(self.team_change_password),
                name="auth_team_password_change",
            ),
        ] + super().get_urls()
    change_password_form = AdminPasswordChangeForm

    @sensitive_post_parameters_m
    def team_change_password(self, request, team_id, form_url="", *args, **kwargs):
        """Change the password of a team"""
        team = Team.objects.get(pk=team_id)
        if not self.has_change_permission(request, team):
            raise PermissionDenied
        if team is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(id),
                }
            )
        if request.method == "POST":
            form = self.change_password_form(team, request.POST)
            if form.is_valid():
                if form.cleaned_data["password1"] != form.cleaned_data["password2"]:
                    msg = _("The two password fields didn't match.")
                    messages.error(request, msg)
                    return HttpResponseRedirect(
                        reverse(
                            f"{self.admin_site.name}:{team._meta.app_label}_{team._meta.model_name}_change",
                            args=(team.pk,),
                        )
                    )
                team.password = make_password(form.cleaned_data["password1"])
                team.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, team, change_message)
                msg = _("Password changed successfully.")
                messages.success(request, msg)
                return HttpResponseRedirect(
                    reverse(
                        f"{self.admin_site.name}:{team._meta.app_label}_{team._meta.model_name}_change",
                        args=(team.pk,),
                    )
                )
        else:
            form = self.change_password_form(team)

        fieldsets = [(None, {"fields": list(form.base_fields)})]
        admin_form = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            "title": _("Change password: %s") % escape(team.name),
            "adminForm": admin_form,
            "form_url": form_url,
            "form": form,
            "is_popup": (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            "is_popup_var": IS_POPUP_VAR,
            "add": True,
            "change": False,
            "has_delete_permission": False,
            "has_change_permission": True,
            "has_absolute_url": False,
            "opts": self.opts,
            "original": team,
            "save_as": False,
            "show_save": True,
            **self.admin_site.each_context(request),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_team_password_template
            or "admin/auth/user/change_password.html",
            context,
        )

admin.site.register(Team, TeamAdmin)

class EventFilter(admin.SimpleListFilter):
    """
    This filter is used to only show players from the selected event
    """
    title = _('Event')
    parameter_name = 'event'

    def lookups(self, request, model_admin):
        return [(event.id, event.name) for event in Event.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(team__tournament__event__id=self.value())
        return queryset

class OngoingTournamentFilter(admin.SimpleListFilter):
    """
    This filter is used to only show players from the selected tournament
    """
    title = _('Tournament')
    parameter_name = 'tournament'

    def lookups(self, request, model_admin):
        return [(tournament.id, tournament.name) for tournament in Tournament.objects.filter(event__ongoing=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(team__tournament__id=self.value())
        return queryset

class PaymentStatusFilter(admin.SimpleListFilter):
    """
    This filter is used to only show players from the selected payment status
    """
    title = _('Payment Status')
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return [(payment_status[0], payment_status[1]) for payment_status in PaymentStatus.choices]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment_status=self.value())
        return queryset

class PlayerAdmin(admin.ModelAdmin):
    """Admin handler for Player Registrations"""

    list_display = ("id", "user", "name_in_game", "team", "payment_status", "get_tournament")
    search_fields = ["user__username", "team__name", "name_in_game"]

    list_filter = (EventFilter,OngoingTournamentFilter,PaymentStatusFilter)

    def get_tournament(self, obj):
        """
        Returns the tournament of the player
        """
        return obj.team.tournament.name

    get_tournament.short_description = 'Tournament'

admin.site.register(Player, PlayerAdmin)


class ManagerAdmin(admin.ModelAdmin):
    """Admin handler for Manager Registrations"""

    list_display = ("id", "user", "team", "payment_status", "get_tournament")
    search_fields = ["user__username", "team__name"]

    list_filter = (EventFilter,OngoingTournamentFilter,PaymentStatusFilter)

    def get_tournament(self, obj):
        """
        Returns the tournament of the manager
        """
        return obj.team.tournament.name

    get_tournament.short_description = 'Tournament'


admin.site.register(Manager, ManagerAdmin)

class CasterAdmin(admin.ModelAdmin):
    """Admin handler for tournament Casters"""

    list_display = ("id", "name", "tournament")
    search_fields = ["name", "tournament__name"]

admin.site.register(Caster, CasterAdmin)

class SubstituteAdmin(admin.ModelAdmin):
    """Admin handler for Substitute Registrations"""

    list_display = ("id", "user", "name_in_game", "team", "payment_status", "get_tournament")
    search_fields = ["user__username", "team__name", "name_in_game"]

    list_filter = (EventFilter,PaymentStatusFilter)

    def get_tournament(self, obj):
        """
        Returns the tournament of the substitute
        """
        return obj.team.tournament.name

    get_tournament.short_description = 'Tournament'


admin.site.register(Substitute, SubstituteAdmin)


def update_bo_type_action(queryset,new_bo_type):
    queryset.update(bo_type=new_bo_type)

@admin.action(description=_("Passer en Bo1"))
def update_to_Bo1_action(modeladmin,request,queryset):
    update_bo_type_action(queryset,BestofType.BO1)
    modeladmin.message_user(request,_("Les matchs ont bien été mis à jour"))

@admin.action(description=_("Passer en Bo3"))
def update_to_Bo3_action(modeladmin,request,queryset):
    update_bo_type_action(queryset,BestofType.BO3)
    modeladmin.message_user(request,_("Les matchs ont bien été mis à jour"))

@admin.action(description=_("Passer en Bo5"))
def update_to_Bo5_action(modeladmin,request,queryset):
    update_bo_type_action(queryset,BestofType.BO5)
    modeladmin.message_user(request,_("Les matchs ont bien été mis à jour"))

@admin.action(description=_("Passer en Bo7"))
def update_to_Bo7_action(modeladmin,request,queryset):
    update_bo_type_action(queryset,BestofType.BO7)
    modeladmin.message_user(request,_("Les matchs ont bien été mis à jour"))

@admin.action(description=_("Passer à un classement"))
def update_to_ranking_action(modeladmin,request,queryset):
    update_bo_type_action(queryset,BestofType.RANKING)
    modeladmin.message_user(request,_("Les matchs ont bien été mis à jour"))

update_bo_type_action_list = [
    update_to_Bo1_action,
    update_to_Bo3_action,
    update_to_Bo5_action,
    update_to_Bo7_action,
    update_to_ranking_action
]


class RoundNumberFilter(admin.SimpleListFilter):
    """Filter for group and swiss match round number"""
    title = _("numéro de round")
    parameter_name = "round_number"

    def lookups(self, request, model_admin):
        return [(str(i),f"Round {i}") for i in set(model_admin.get_queryset(request).values_list("round_number", flat=True))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(round_number=self.value())
        return queryset


class BracketMatchFilter(admin.SimpleListFilter):
    """Filter for bracket matchs"""
    title = _("niveau dans l'arbre")
    parameter_name = "round_number"

    def lookups(self, request, model_admin):
        lookup = {
            "W0" : "Grande finale",
            "W1" : "Finale winner",
            "L1" : "Finale looser"
        }
        depths = [bracket.get_depth() for bracket in Bracket.objects.all()]

        if len(depths):
            max_depth = max(depths)
        else:
            max_depth = 0

        for depth in range(1,max_depth):
            if depth == 1:
                lookup["W2"] = "Demi-finale winner"
            elif depth == 2:
                lookup["W3"] = "Quart de finale winner"
            else:
                lookup["W" + str(depth+1)] = f"1/{2**depth}ème winner"

        for tour,round_number in enumerate(range(2*(max_depth-1),1,-1)):
            lookup["L" + str(round_number)] = f"Tour {tour+1} looser"
        return lookup.items()

    def queryset(self, request, queryset):
        if self.value():
            br_set = BracketSet.WINNER if self.value()[0] == "W" else BracketSet.LOOSER
            return queryset.filter(round_number=self.value()[1:],bracket_set=br_set)
        return queryset


class GroupTeamsInline(admin.TabularInline):
    model = Seeding
    extra = 1

    def formfield_for_foreignkey(self, db_field: ForeignKey[Any], request: HttpRequest | None, **kwargs: Any) -> ModelChoiceField | None:
        if db_field.name == "team":
            resolved = resolve(request.path_info)
            if "object_id" in resolved.kwargs:
                kwargs["queryset"] = Team.objects.filter(tournament=self.parent_model.objects.get(pk=resolved.kwargs["object_id"]).tournament,validated=True).order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ScoreInline(admin.TabularInline):
    model = Score
    extra = 0

    def formfield_for_foreignkey(self, db_field: ForeignKey[Any], request, **kwargs):
        if db_field.name == "team":
            resolved = resolve(request.path_info)
            if "object_id" in resolved.kwargs:
                kwargs["queryset"] = Team.objects.filter(tournament=self.parent_model.objects.get(pk=resolved.kwargs["object_id"]).get_tournament(),validated=True).order_by("name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class GroupAdmin(admin.ModelAdmin):
    """Admin handler for Groups"""

    list_display = ("id", "name", "tournament")
    search_fields = ["name","tournament"]
    inlines = [GroupTeamsInline]
    actions = ["create_group_matchs_action"]

    list_filter = ["tournament","tournament__event","tournament__game"]

    @admin.action(description=_("Créer les matchs des poules"))
    def create_group_matchs_action(self,request,queryset):
        for group in queryset:
            matchs_status = GroupMatch.objects.filter(group=group).values_list("status", flat=True)
            if MatchStatus.ONGOING in matchs_status or MatchStatus.COMPLETED in matchs_status:
                self.message_user(request,_("Impossible de créer les matchs, des matchs existent déjà et sont en cours ou terminés."),messages.ERROR)
                return

            create_group_matchs(group)
            self.message_user(request,_("Matchs créés avec succes"))

admin.site.register(Group, GroupAdmin)

class GroupMatchAdmin(admin.ModelAdmin):
    """Admin handle for group matchs"""

    list_display = ("id", "group", "status","round_number","index_in_round","bo_type",)
    search_fields = ["index_in_round","round_number"]
    # filter_horizontal = ("teams",)
    inlines = [ScoreInline]
    actions = [
        "launch_group_matchs_action",
        *update_bo_type_action_list
    ]

    list_filter = ["group__tournament","group",RoundNumberFilter,"index_in_round","status"]

    @admin.action(description=_("Lancer les matchs"))
    def launch_group_matchs_action(self,request,queryset):
        for match in queryset:
            if match.status != MatchStatus.COMPLETED:
                for team in match.get_teams():
                    team_matchs = GroupMatch.objects.filter(teams=team,round_number__lt=match.round_number)
                    for team_match in team_matchs:
                        if team_match.status == MatchStatus.ONGOING:
                            self.message_user(request,_(f"L'équipe {team.name} est encore dans un match en cours"), messages.ERROR)
                            return
                        if team_match.status == MatchStatus.SCHEDULED:
                            self.message_user(request,_(f"L'équipe {team.name} n'a pas encore joué un ou des matchs des rounds précédent"), messages.ERROR)
                            return

                launch_match(match)
        self.message_user(request,_("Les matchs ont bien été lancés"))


admin.site.register(GroupMatch, GroupMatchAdmin)

class MailerAdmin(admin.ModelAdmin):
    """
    Admin handler for TournamentMailer
    """
    exclude = ('mail', 'number')
    list_display = ('mail', 'number')

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def add_view(self, request, form_url="", extra_context=None):
        super().add_view(request, form_url, extra_context)
        return self.changeform_view(request, None, form_url, {
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
            'title': _('Envoyer un mail'),
    })

    # replace the list url with the add one
    def get_urls(self):
        custom_urls = [
            path('add/', self.admin_site.admin_view(self.add_view), name='tournament_tournamentmailer_add'),
            path('', self.admin_site.admin_view(self.changelist_view), name='tournament_tournamentmailer_changelist'),
        ]
        return custom_urls

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        # remove everything from the queryset
        TournamentMailer.objects.all().delete()

        # create an object for each mailer
        for mailer in MailManager.mailers.values():
            mailer_obj = TournamentMailer.objects.create(
                mail=mailer.mail_from,
                number=len(mailer.queue)
            )
            mailer_obj.save()

        # return the queryset
        return TournamentMailer.objects.all()

    def response_add(self, request, obj, post_url_continue=None):
        messages.info(request, _("Le mail est en cours d'envoi"))
        return HttpResponseRedirect(reverse('admin:mailer_add'))

admin.site.register(TournamentMailer, MailerAdmin)

class BracketAdmin(admin.ModelAdmin):
    """Admin handle for Brackets"""

    list_display = ("id", "name", "tournament")
    search_fields = ["name","tournament","tournament__event","tournament__game"]
    actions = ["create_empty_knockout_matchs_action"]

    list_filter = ["tournament","tournament__event","tournament__game"]

    @admin.action(description=_("Créer les matchs"))
    def create_empty_knockout_matchs_action(self,request,queryset):
        for bracket in queryset:
            if any([MatchStatus.SCHEDULED != m.status for m in KnockoutMatch.objects.filter(bracket=bracket)]):
                self.message_user(request,_("Des matchs existent déjà et sont en cours ou terminés"))

            create_empty_knockout_matchs(bracket)
            self.message_user(request,_("Matchs créer avec succès"))

    @admin.action(description=_("Remplir les matchs"))
    def fill_knockout_matchs_action(self,request,queryset):
        for bracket in queryset:
            # TODO: Fix this
            # fill_knockout_matchs(bracket)
            pass

admin.site.register(Bracket, BracketAdmin)

class KnockoutMatchAdmin(admin.ModelAdmin):
    """Admin handle for Knockout matchs"""

    list_display = ("id", "bracket", "status","bracket_set","round_number","index_in_round","bo_type",)
    inlines = [ScoreInline]
    actions = [
        "launch_knockout_matchs_action",
        *update_bo_type_action_list
    ]

    list_filter = [ "bracket__tournament", "bracket", "bracket_set", BracketMatchFilter, "index_in_round", "status"]

    @admin.action(description=_("Lancer les matchs"))
    def launch_knockout_matchs_action(self,request,queryset):
        for match in queryset:
            if match.status != MatchStatus.COMPLETED:
                for team in match.get_teams():
                    team_matchs = KnockoutMatch.objects.filter(teams=team,round_index__gt=match.round_number)
                    for team_match in team_matchs:
                        if team_match.status == MatchStatus.ONGOING:
                            self.message_user(request,_(f"L'équipe {team.name} est encore dans un match en cours"), messages.ERROR)
                            return
                        if team_match.status == MatchStatus.SCHEDULED:
                            self.message_user(request,_(f"L'équipe {team.name} n'a pas encore joué un ou des matchs des rounds précédent"), messages.ERROR)
                            return

                launch_match(match)
        self.message_user(request,_("Les matchs ont bien été lancés"))


admin.site.register(KnockoutMatch, KnockoutMatchAdmin)

class SwissSeedingInline(admin.TabularInline):
    model = SwissSeeding
    extra = 0

    def formfield_for_foreignkey(self, db_field: ForeignKey[Any], request: HttpRequest | None, **kwargs: Any) -> ModelChoiceField | None:
        if db_field.name == "team":
            resolved = resolve(request.path_info)
            if "object_id" in resolved.kwargs:
                kwargs["queryset"] = Team.objects.filter(tournament=self.parent_model.objects.get(pk=resolved.kwargs["object_id"]).tournament).order_by("name")
        return super().formfield_for_foreignkey(db_field,request,**kwargs)

class SwissRoundAdmin(admin.ModelAdmin):
    """Admin handle for Swiss Round"""

    list_display = ("id", "tournament")
    search_fields = ["tournament"]
    inlines = [SwissSeedingInline]
    actions = ["create_swiss_matchs_action"]

    list_filter = ["tournament","tournament__game","tournament__event"]

    @admin.action(description=_("Créer les matchs du système suisse"))
    def create_swiss_matchs_action(self,request,queryset):
        for swiss in queryset:
            matchs_status = SwissMatch.objects.filter(swiss=swiss).values_list("status", flat=True)
            if any([status != MatchStatus.SCHEDULED for status in matchs_status]):
                self.message_user(request,_("Des matchs existent déjà et sont en cours ou terminés"))
                return

            create_swiss_matchs(swiss)
            self.message_user(request,_("Matchs créés avec succès"))

admin.site.register(SwissRound,SwissRoundAdmin)

class SwissMatchAdmin(admin.ModelAdmin):
    """Admin handle for Swiss matchs"""

    list_display = ("id","swiss","status","round_number","index_in_round","bo_type","score_group")
    inlines = [ScoreInline]
    actions = [
        "launch_swiss_matchs_action",
        *update_bo_type_action_list
    ]

    list_filter = ["swiss__tournament","swiss",RoundNumberFilter,"index_in_round","status"]

    @admin.action(description=_("Lancer les matchs"))
    def launch_swiss_matchs_action(self,request,queryset):
        for match in queryset:
            if match.status != MatchStatus.COMPLETED:
                for team in match.get_teams():
                    team_matchs = SwissMatch.objects.filter(teams=team,round_number__lt=match.round_number)
                    for team_match in team_matchs:
                        if team_match.status == MatchStatus.ONGOING:
                            self.message_user(request,_(f"L'équipe {team.name} est encore dans un match en cours"), messages.ERROR)
                            return
                        if team_match.status == MatchStatus.SCHEDULED:
                            self.message_user(request,_(f"L'équipe {team.name} n'a pas encore joué un ou des matchs des rounds précédent"), messages.ERROR)
                            return

                launch_match(match)
        self.message_user(request,_("Les matchs ont bien été lancés"))

admin.site.register(SwissMatch, SwissMatchAdmin)


class SeatAdmin(admin.ModelAdmin):
    """Admin handler for Seating"""

    list_display = ("id", "event", "x", "y")
    search_fields = ["event"]
    list_filter = ["event"]


admin.site.register(Seat, SeatAdmin)

class SeatSlotForm(forms.ModelForm):
    class Meta:
        model = SeatSlot
        fields = ['tournament', 'seats']

    def clean(self):
        """
        Validation for seat slot
        """
        seats = self.cleaned_data.get('seats')
        tournament = self.cleaned_data.get('tournament')

        # Ensure that the number of seats is consistent with the tournament
        if seats and tournament:
            if seats.count() != tournament.game.players_per_team:
                raise ValidationError(
                _("Le nombre de places est incorrect pour ce tournoi")
                )

        # Ensure that the seats are all in the same event
        if seats:
            event = seats.first().event
            if not all([seat.event.id == event.id for seat in seats]):
                raise ValidationError(
                _("Les places doivent être dans le même événement")
                )

        # Ensure that all seats are not part of another slot
        if seats:
            other_slots = SeatSlot.objects.exclude(id=self.instance.id)
            other_seats = {seat for slot in other_slots for seat in slot.seats.all()}
            if other_seats.intersection(seats):
                raise ValidationError(
                _("Les places ne peuvent pas être partagés entre plusieurs slots")
                )

        return self.cleaned_data


class SeatSlotAdmin(admin.ModelAdmin):
    """Admin handler for SeatSlot"""
    list_display = ("id", "get_seats")
    form = SeatSlotForm

    @admin.display(description="Seats")
    def get_seats(self, obj):
        return ", ".join([f"({seat.x}, {seat.y})" for seat in obj.seats.all()])

admin.site.register(SeatSlot, SeatSlotAdmin)
