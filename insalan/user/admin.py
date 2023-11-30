"""Register our models in Django admin panel"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import User
from django.contrib.admin import SimpleListFilter

class EmailActivatedFilter(SimpleListFilter):
    title = 'permissions' # or use _('country') for translated title
    parameter_name = 'permissions'

    def lookups(self, request, model_admin):
        return [(True, 'Validé'), (False, 'Non validé')]

    def queryset(self, request, queryset):
        if self.value():
            # if true, return users with email active permission
            if self.value() == 'True':
                return queryset.filter(user_permissions__codename='email_active')
            elif self.value() == 'False':
                return queryset.exclude(user_permissions__codename='email_active')
        else:
            return queryset

class CustomUserAdmin(UserAdmin):
    fieldsets = (UserAdmin.fieldsets[0],) + (
        ("Informations personnelles", {
            'fields': ('first_name', 'last_name', 'email', 'display_name', 'pronouns','status'),
        }),
    ) + UserAdmin.fieldsets[2:] + (
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

    # order the fields in the admin panel by creation date
    ordering = ('date_joined',)

    # add custom sort filter by has email activated in permission
    list_filter = UserAdmin.list_filter + (EmailActivatedFilter,)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Permission)
