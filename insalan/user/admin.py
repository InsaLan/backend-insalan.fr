"""Register our models in Django admin panel"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import User
from django.contrib.admin import SimpleListFilter
from insalan.tournament.models import Player, Manager, Substitute

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
    ordering = ('-date_joined',)

    # list of fields to display in the admin panel
    list_display = ('id', 'username', 'email', 'is_staff', 'get_number_of_registration')

    # add custom sort filter by has email activated in permission
    list_filter = UserAdmin.list_filter + (EmailActivatedFilter,)

    def get_number_of_registration(self, obj):
        return Player.objects.filter(user=obj).count() + Manager.objects.filter(user=obj).count() + Substitute.objects.filter(user=obj).count()
    get_number_of_registration.short_description = 'Number of registrations'
    


admin.site.register(User, CustomUserAdmin)
admin.site.register(Permission)
