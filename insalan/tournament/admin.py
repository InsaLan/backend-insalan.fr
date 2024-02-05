"""Admin handlers for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from typing import Any
from django.contrib.auth import password_validation
from django.contrib import admin, messages
from django.db.models.query import QuerySet
from django.db.models.fields.related import ForeignKey
from django.forms.models import ModelChoiceField
from django.http.request import HttpRequest
from django.utils.translation import gettext as _
from django import forms
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.http import Http404, HttpResponseRedirect
from django.urls import path, reverse, resolve
from django.utils.html import escape
from django.contrib.auth.forms import AdminPasswordChangeForm, UsernameField
from django.contrib.admin.options import IS_POPUP_VAR
from django.template.response import TemplateResponse
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator

from insalan.mailer import MailManager
from .models import Event, Tournament, Game, Team, Player, Manager, Substitute, Caster, PaymentStatus, Group, GroupMatch, KnockoutMatch, Bracket, Seeding, MatchStatus, Score, SwissRound, SwissMatch, SwissSeeding, TournamentMailer
from insalan.tournament.manage import create_group_matchs, create_empty_knockout_matchs, create_swiss_matchs

sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

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

class TournamentAdmin(admin.ModelAdmin):
    """Admin handler for Tournaments"""

    list_display = ("id", "name", "event", "game", "is_announced", "cashprizes", "get_occupancy")
    search_fields = ["name", "event__name", "game__name"]

    list_filter = (EventTournamentFilter,GameTournamentFilter)

    def get_occupancy(self, obj):
        """
        Returns the occupancy of the tournament
        """
        return str(Team.objects.filter(tournament=obj, validated=True).count()) + " / " + str(obj.maxTeam)

    get_occupancy.short_description = 'Remplissage'

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
        """
        Meta options for the form
        """
        model = Team
        fields = ("name", "tournament", "validated")
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
    title = _('Tournament')
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


class GroupTeamsInline(admin.TabularInline):
    model = Seeding
    extra = 1

    def formfield_for_foreignkey(self, db_field: ForeignKey[Any], request: HttpRequest | None, **kwargs: Any) -> ModelChoiceField | None:
        if db_field.name == "team":
            resolved = resolve(request.path_info)
            if "object_id" in resolved.kwargs:
                kwargs["queryset"] = Team.objects.filter(tournament=self.parent_model.objects.get(pk=resolved.kwargs["object_id"]).tournament)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ScoreInline(admin.TabularInline):
    model = Score
    extra = 0

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

    list_display = ("id", "group", "status")
    search_fields = ["index_in_round","round_number"]
    # filter_horizontal = ("teams",)
    inlines = [ScoreInline]
    actions = ["launch_group_matchs_action"]

    list_filter = ["group","group__tournament","round_number","index_in_round"]

    @admin.action(description=_("Lancer les matchs"))
    def launch_group_matchs_action(self,request,queryset):
        for match in queryset:
            for team in match.get_teams():
                team_matchs = GroupMatch.objects.filter(teams=team,round_number__lt=match.round_number)
                for team_match in team_matchs:
                    if team_match.status == MatchStatus.ONGOING:
                        self.message_user(request,_(f"L'équipe {team.name} est encore dans un match en cours"), messages.ERROR)
                        return
                    if team_match.status == MatchStatus.SCHEDULED:
                        self.message_user(request,_(f"L'équipe {team.name} n'a pas encore joué un ou des matchs des rounds précédent"), messages.ERROR)
                        return

            if len(match.get_teams()) == 1:
                match.status = MatchStatus.COMPLETED
                score = Score.objects.get(team=match.get_teams()[0],match=match)
                score.score = match.get_winning_score()
                score.save()
            else:
                match.status = MatchStatus.ONGOING

            match.save()
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
    actions = ["create_empty_knockout_matchs_action","fill_knockout_matchs_action"]

    list_filter = ["tournament","tournament__event"]

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
            # fill_knockout_matchs(bracket)
            pass

admin.site.register(Bracket, BracketAdmin)

class KnockoutMatchAdmin(admin.ModelAdmin):
    """Admin handle for Knockout matchs"""

    list_display = ("id", "bracket", "status")
    filter_horizontal = ("teams",)
    actions = [""]

    list_filter = ["bracket", "bracket__tournament", "round_number", "index_in_round"]

    @admin.action(description=_("Lancer les matchs"))
    def launch_knockout_matchs_action(self,request,queryset):
        for match in queryset:
            for team in match.get_teams():
                team_matchs = KnockoutMatch.objects.filter(teams=team,round_index__gt=match.round_number)
                for team_match in team_matchs:
                    if team_match.status == MatchStatus.ONGOING:
                        self.message_user(request,_(f"L'équipe {team.name} est encore dans un match en cours"), messages.ERROR)
                        return
                    if team_match.status == MatchStatus.SCHEDULED:
                        self.message_user(request,_(f"L'équipe {team.name} n'a pas encore joué un ou des matchs des rounds précédent"), messages.ERROR)
                        return

            if len(match.get_teams()) == 1:
                match.status = MatchStatus.COMPLETED
                score = Score.objects.get(team=match.get_teams()[0],match=match)
                score.score = match.get_winning_score()
                score.save()
            else:
                match.status = MatchStatus.ONGOING

            match.save()
        self.message_user(request,_("Les matchs ont bien été lancés"))


admin.site.register(KnockoutMatch, KnockoutMatchAdmin)

class SwissSeedingInline(admin.TabularInline):
    model = SwissSeeding
    extra = 0

    def formfield_for_foreignkey(self, db_field: ForeignKey[Any], request: HttpRequest | None, **kwargs: Any) -> ModelChoiceField | None:
        if db_field.name == "team":
            resolved = resolve(request.path_info)
            if "object_id" in resolved.kwargs:
                kwargs["queryset"] = Team.objects.filter(tournament=self.parent_model.objects.get(pk=resolved.kwargs["object_id"]).tournament)
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

    list_display = ("id","swiss","status")
    inlines = [ScoreInline]
    actions = ["launch_swiss_matchs_action"]

    list_filter = ["swiss", "swiss__tournament","round_number","index_in_round"]

    @admin.action(description=_("Lancer les matchs"))
    def launch_swiss_matchs_action(self,request,queryset):
        for match in queryset:
            for team in match.get_teams():
                team_matchs = SwissMatch.objects.filter(teams=team,round_number__lt=match.round_number)
                for team_match in team_matchs:
                    if team_match.status == MatchStatus.ONGOING:
                        self.message_user(request,_(f"L'équipe {team.name} est encore dans un match en cours"), messages.ERROR)
                        return
                    if team_match.status == MatchStatus.SCHEDULED:
                        self.message_user(request,_(f"L'équipe {team.name} n'a pas encore joué un ou des matchs des rounds précédent"), messages.ERROR)
                        return

            if len(match.get_teams()) == 1:
                match.status = MatchStatus.COMPLETED
                score = Score.objects.get(team=match.get_teams()[0],match=match)
                score.score = match.get_winning_score()
                score.save()
            else:
                match.status = MatchStatus.ONGOING

            match.save()
        self.message_user(request,_("Les matchs ont bien été lancés"))

admin.site.register(SwissMatch, SwissMatchAdmin)
