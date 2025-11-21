"""Register our models in Django admin panel"""

from __future__ import annotations

import copy
from typing import Any

from django import forms
from django.db.models.query import QuerySet
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Permission
from django.forms.renderers import BaseRenderer
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.urls import path, reverse, URLPattern
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _
from django.views.decorators.debug import sensitive_post_parameters
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from insalan.mailer import MailManager
from insalan.settings import EMAIL_AUTH
from insalan.tournament.models import Player, Manager, Substitute
from insalan.utils import FieldOpts, FieldSets

from .models import User


sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())


class EmailActivatedFilter(SimpleListFilter):
    title = 'Validation du Courriel' # or use _('country') for translated title
    parameter_name = 'permissions'

    def lookups(self, request: HttpRequest, model_admin: ModelAdmin[User]
                ) -> list[tuple[bool, str]]:
        return [(True, 'Courriel validé'), (False, 'Courriel non validé')]

    def queryset(self, request: HttpRequest, queryset: QuerySet[User]) -> QuerySet[User]:
        if self.value():
            # if true, return users with email active permission
            if self.value() == 'True':
                return queryset.filter(user_permissions__codename='email_active')
            if self.value() == 'False':
                return queryset.exclude(user_permissions__codename='email_active')
            assert False, f"unreachable path: unexpected value {repr(self.value())}"
        else:
            return queryset


class ButtonWidget(forms.Widget):
    """Custom widget for the resend email button."""

    def render(self, name: str, value: Any, attrs: dict[str, Any] | None = None,
               renderer: BaseRenderer | None = None) -> SafeString:
        return SafeString('<input type="button" value="' + \
            _("Renvoyer le courriel de confirmation") + \
            '" onclick="window.location.href=\'../resend\'" />')


class Button(forms.Field):
    """
    Custom field for the resend email button
    """
    widget = ButtonWidget

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("disabled", True)
        super().__init__(*args, **kwargs)


class UserForm(UserChangeForm[User]):  # pylint: disable=unsubscriptable-object
    """
    Custom form for the User model
    """
    confirmation = Button()

    class Meta:
        """
        Meta class for the User form
        """
        model = User
        fields = "__all__"

class CustomUserAdmin(DjangoUserAdmin):
    """
    Custom admin panel for the User model
    """
    assert DjangoUserAdmin.fieldsets is not None
    fieldsets = (
        DjangoUserAdmin.fieldsets[0],
        (
            "Informations personnelles",
            {
                'fields': ('first_name', 'last_name', 'email', 'display_name', 'pronouns','status'),
            },
        ),
        (
            DjangoUserAdmin.fieldsets[2][0],
            {
                'fields': (*DjangoUserAdmin.fieldsets[2][1]['fields'], 'confirmation'),
                'classes': DjangoUserAdmin.fieldsets[2][1].get('classes', ''),
                'description': DjangoUserAdmin.fieldsets[2][1].get('description', ''),
            },
        ),
        *DjangoUserAdmin.fieldsets[3:],
        (
            "Image",
            {
                'fields': ('image',),
            },
        ),
    )
    # add email to the add user form
    add_fieldsets: tuple[tuple[str | None, FieldOpts]] = DjangoUserAdmin.add_fieldsets + (
        ("Email", {
            'fields': ('email',),
        }),
    )

    # use our custom form
    form = UserForm

    # order the fields in the admin panel by creation date
    ordering = ('-date_joined',)

    # list of fields to display in the admin panel
    list_display = ('id', 'username', 'email', 'is_staff', 'get_number_of_registration')

    # add custom sort filter by has email activated in permission
    list_filter = (*DjangoUserAdmin.list_filter, EmailActivatedFilter)

    def get_fieldsets(self, request: HttpRequest, obj: User | None = None
                      ) -> FieldSets:
        """Use special form during user creation."""
        if not obj:
            return self.add_fieldsets
        if self.fieldsets:
            if obj.has_perm("email_active"):
                modified_fieldsets = copy.deepcopy(self.fieldsets)
                modified_fieldsets[2][1]['fields'] = tuple(filter(
                    lambda x: x != 'confirmation',
                    modified_fieldsets[2][1]['fields']
                ))
                return modified_fieldsets
            return self.fieldsets
        return super().get_fieldsets(request, obj)

    def get_number_of_registration(self, obj: User) -> int:
        return Player.objects.filter(user=obj).count() + \
               Manager.objects.filter(user=obj).count() + \
               Substitute.objects.filter(user=obj).count()
    get_number_of_registration.short_description = (  # type: ignore[attr-defined]
        'Number of registrations'
    )


    def get_urls(self) -> list[URLPattern]:
        """
        Add the resend email url to the admin panel
        """
        return [
            path(
                "<int:user_id>/resend/",
                self.admin_site.admin_view(self.resend_email),
                name="auth_user_resend_email",
            ),
        ] + super().get_urls()

    @sensitive_post_parameters_m
    def resend_email(self, request: HttpRequest, user_id: int) -> HttpResponse:
        """
        Resend the email to the user
        """
        user = User.objects.get(pk=user_id)
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        if user is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(user_id),
                }
            )
        if user.has_perm("email_active"):
            msg = _("User email was already validated.")
            messages.error(request, msg)
            return HttpResponseRedirect(
                reverse(
                    f"{self.admin_site.name}:{user._meta.app_label}_{user._meta.model_name}_change",
                    args=(user.pk,),
                )
            )
        mailer = MailManager.get_mailer(EMAIL_AUTH["contact"]["from"])
        assert mailer is not None
        mailer.send_email_confirmation(user)
        msg = _("The confirmation email was resent.")
        messages.success(request, msg)
        return HttpResponseRedirect(
            reverse(
                f"{self.admin_site.name}:{user._meta.app_label}_{user._meta.model_name}_change",
                args=(user.pk,),
            )
        )

@admin.register(User) # Register with Unfold fields for the theme
class UserAdmin(CustomUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

admin.site.register(Permission)
