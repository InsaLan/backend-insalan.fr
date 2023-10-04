"""Register our models in Django admin panel"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Image", {
            'fields': ('image',),
        }),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Permission)
