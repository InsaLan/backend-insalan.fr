"""Admin handlers for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django.contrib.auth import password_validation
from django.contrib import admin, messages
from django.utils.translation import gettext as _
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.urls import path, reverse
from django.http import Http404, HttpResponseRedirect
from django.utils.html import escape
from django.contrib.auth.forms import AdminPasswordChangeForm, UsernameField
from django.utils.translation import gettext
from django.contrib.admin.options import IS_POPUP_VAR
from django.template.response import TemplateResponse
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator

sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

from .models import Event, Tournament, Game, Team, Player, Manager, Substitute, Caster, PaymentStatus


class EventAdmin(admin.ModelAdmin):
    """Admin handler for Events"""

    list_display = ("id", "name", "description", "year", "month", "ongoing")
    search_fields = ["name", "year", "month", "ongoing"]


admin.site.register(Event, EventAdmin)


class GameAdmin(admin.ModelAdmin):
    """Admin handler for Games"""

    list_display = ("id", "name", "players_per_team")
    search_fields = ["name"]


admin.site.register(Game, GameAdmin)

class EventTournamentFilter(admin.SimpleListFilter):
    title = 'Event' # or use _('country') for translated title
    parameter_name = 'event'

    def lookups(self, request, model_admin):
        return [(event.id, event.name) for event in Event.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(event__id=self.value())
        else:
            return queryset
        
class GameTournamentFilter(admin.SimpleListFilter):
    title = 'Game' # or use _('country') for translated title
    parameter_name = 'game'

    def lookups(self, request, model_admin):
        return [(game.id, game.name) for game in Game.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(game__id=self.value())
        else:
            return queryset

class TournamentAdmin(admin.ModelAdmin):
    """Admin handler for Tournaments"""

    list_display = ("id", "name", "event", "game", "is_announced", "cashprizes", "get_remplissage")
    search_fields = ["name", "event", "game"]

    list_filter = (EventTournamentFilter,GameTournamentFilter)

    def get_remplissage(self, obj):
        return str(Team.objects.filter(tournament=obj, validated=True).count()) + " / " + str(obj.maxTeam)

    get_remplissage.short_description = 'Remplissage'

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
        model = Team
        fields = ("name", "tournament", "validated")
        field_classes = {"name": UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.name in self.fields:
            self.fields[self._meta.model.name].widget.attrs[
                "autofocus"
            ] = True

    def clean_password2(self):
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
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user

class TeamTournamentFilter(admin.SimpleListFilter):
    title = 'Tournament' # or use _('country') for translated title
    parameter_name = 'tournament'

    def lookups(self, request, model_admin):
        return [(tournament.id, tournament.name) for tournament in Tournament.objects.filter(event__ongoing=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tournament__id=self.value())
        else:
            return queryset

class ValidatedFilter(admin.SimpleListFilter):
    title = 'Validation' # or use _('country') for translated title
    parameter_name = 'validated'

    def lookups(self, request, model_admin):
        return [(True, 'Validé'), (False, 'Non Validé')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(validated=self.value())
        else:
            return queryset

class TeamAdmin(admin.ModelAdmin):
    """Admin handler for Team"""

    list_display = ("id", "name", "tournament", "validated", "get_quota")
    search_fields = ["name", "tournament"]
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
        return str(Player.objects.filter(team=obj).count()) + " / " + str(obj.tournament.game.players_per_team)

    get_quota.short_description = 'Nombre de Joueurs'

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_urls(self):
        return [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.team_change_password),
                name="auth_team_password_change",
            ),
        ] + super().get_urls()
    change_password_form = AdminPasswordChangeForm
    
    @sensitive_post_parameters_m
    def team_change_password(self, request, id, form_url=""):
        """Change the password of a team"""
        team = Team.objects.get(pk=id)
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
                    msg = gettext("The two password fields didn't match.")
                    messages.error(request, msg)
                    return HttpResponseRedirect(
                        reverse(
                            "%s:%s_%s_change"
                            % (
                                self.admin_site.name,
                                team._meta.app_label,
                                team._meta.model_name,
                            ),
                            args=(team.pk,),
                        )
                    )
                team.password = make_password(form.cleaned_data["password1"])
                team.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, team, change_message)
                msg = gettext("Password changed successfully.")
                messages.success(request, msg)
                return HttpResponseRedirect(
                    reverse(
                        "%s:%s_%s_change"
                        % (
                            self.admin_site.name,
                            team._meta.app_label,
                            team._meta.model_name,
                        ),
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
    title = 'Event' # or use _('country') for translated title
    parameter_name = 'event'

    def lookups(self, request, model_admin):
        return [(event.id, event.name) for event in Event.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(team__tournament__event__id=self.value())
        else:
            return queryset

class OngoingTournamentFilter(admin.SimpleListFilter):
    title = 'Tournament' # or use _('country') for translated title
    parameter_name = 'tournament'

    def lookups(self, request, model_admin):
        return [(tournament.id, tournament.name) for tournament in Tournament.objects.filter(event__ongoing=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(team__tournament__id=self.value())
        else:
            return queryset

class PaymentStatusFilter(admin.SimpleListFilter):
    title = 'Payment Status' # or use _('country') for translated title
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return [(payment_status[0], payment_status[1]) for payment_status in PaymentStatus.choices]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment_status=self.value())
        else:
            return queryset

class PlayerAdmin(admin.ModelAdmin):
    """Admin handler for Player Registrations"""

    list_display = ("id", "user", "name_in_game", "team", "payment_status", "get_tournament")
    search_fields = ["user", "team", "payment_status", "name_in_game"]

    list_filter = (EventFilter,OngoingTournamentFilter,PaymentStatusFilter)

    def get_tournament(self, obj):
        return obj.team.tournament.name
    
    get_tournament.short_description = 'Tournament'

admin.site.register(Player, PlayerAdmin)


class ManagerAdmin(admin.ModelAdmin):
    """Admin handler for Manager Registrations"""

    list_display = ("id", "user", "team", "payment_status", "get_tournament")
    search_fields = ["user", "team", "payment_status"]

    list_filter = (EventFilter,OngoingTournamentFilter,PaymentStatusFilter)

    def get_tournament(self, obj):
        return obj.team.tournament.name
    
    get_tournament.short_description = 'Tournament'


admin.site.register(Manager, ManagerAdmin)

class CasterAdmin(admin.ModelAdmin):
    """Admin handler for tournament Casters"""

    list_display = ("id", "name", "tournament")
    search_fields = ["name", "tournament"]

admin.site.register(Caster, CasterAdmin)

class SubstituteAdmin(admin.ModelAdmin):
    """Admin handler for Substitute Registrations"""

    list_display = ("id", "user", "name_in_game", "team", "payment_status", "get_tournament")
    search_fields = ["user", "team", "payment_status", "name_in_game"]

    list_filter = (EventFilter,PaymentStatusFilter)

    def get_tournament(self, obj):
        return obj.team.tournament.name
    
    get_tournament.short_description = 'Tournament'


admin.site.register(Substitute, SubstituteAdmin)
