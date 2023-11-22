"""Register our models in Django admin panel"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import User

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

admin.site.register(User, CustomUserAdmin)
admin.site.register(Permission)
