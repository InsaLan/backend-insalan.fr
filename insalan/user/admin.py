"""Register our models in Django admin panel"""
import copy

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext as _
from django.urls import path, reverse
from django import forms
from django.http import Http404, HttpResponseRedirect
from django.utils.html import escape
from django.core.exceptions import PermissionDenied
from django.contrib.admin import SimpleListFilter
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from insalan.tournament.models import Player, Manager, Substitute

from insalan.mailer import MailManager
from insalan.settings import EMAIL_AUTH
from .models import User

sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

class EmailActivatedFilter(SimpleListFilter):
    title = 'Validation du Courriel' # or use _('country') for translated title
    parameter_name = 'permissions'

    def lookups(self, request, model_admin):
        return [(True, 'Courriel validé'), (False, 'Courriel non validé')]

    def queryset(self, request, queryset):
        if self.value():
            # if true, return users with email active permission
            if self.value() == 'True':
                return queryset.filter(user_permissions__codename='email_active')
            elif self.value() == 'False':
                return queryset.exclude(user_permissions__codename='email_active')
        else:
            return queryset

class ButtonWidget(forms.Widget):
    """
    Custom widget for the resend email button
    """
    def render(self, name, value, attrs=None, renderer=None):
        return '<input type="button" value="' + \
            _("Renvoyer le courriel de confirmation") + \
            '" onclick="window.location.href=\'../resend\'" />'

class Button(forms.Field):
    """
    Custom field for the resend email button
    """
    widget = ButtonWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("disabled", True)
        super().__init__(*args, **kwargs)

class UserForm(UserChangeForm):
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


class CustomUserAdmin(UserAdmin):
    """
    Custom admin panel for the User model
    """
    fieldsets = (UserAdmin.fieldsets[0],) + (
        ("Informations personnelles", {
            'fields': ('first_name', 'last_name', 'email', 'display_name', 'pronouns','status'),
        }),
    ) + ((
            UserAdmin.fieldsets[2][0],
            {
                'fields': UserAdmin.fieldsets[2][1]['fields'] + ('confirmation',),
                'classes': UserAdmin.fieldsets[2][1].get('classes', ''),
                'description': UserAdmin.fieldsets[2][1].get('description', ''),
            },
        ),) + UserAdmin.fieldsets[3:] + (
        ("Image", {
            'fields': ('image',),
        }),
    )
    # add email to the add user form
    add_fieldsets = UserAdmin.add_fieldsets + (
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
    list_filter = UserAdmin.list_filter + (EmailActivatedFilter,)

    def get_fieldsets(self, request, obj=None):
        """
        Use special form during user creation
        """
        if not obj:
            return self.add_fieldsets
        if self.fieldsets:
            if obj.has_perm("email_active"):
                modified_fieldsets = copy.deepcopy(self.fieldsets)
                modified_fieldsets[2][1]['fields'] = tuple(filter(lambda x: x != 'confirmation', modified_fieldsets[2][1]['fields']))
                return modified_fieldsets
            else:
                return self.fieldsets
        return super().get_fieldsets(request, obj)

    def get_number_of_registration(self, obj):
        return Player.objects.filter(user=obj).count() + Manager.objects.filter(user=obj).count() + Substitute.objects.filter(user=obj).count()
    get_number_of_registration.short_description = 'Number of registrations'

    def get_urls(self):
        """
        Add the resend email url to the admin panel
        """
        return [
            path(
                "<id>/resend/",
                self.admin_site.admin_view(self.resend_email),
                name="auth_user_resend_email",
            ),
        ] + super().get_urls()

    @sensitive_post_parameters_m
    def resend_email(self, request, user_id, form_url=""):
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
        else:
            MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_email_confirmation(user)
            msg = _("The confirmation email was resent.")
            messages.success(request, msg)
            return HttpResponseRedirect(
                reverse(
                    f"{self.admin_site.name}:{user._meta.app_label}_{user._meta.model_name}_change",
                    args=(user.pk,),
                )
            )



admin.site.register(User, CustomUserAdmin)
admin.site.register(Permission)
