"""Register our models in Django admin panel"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Image", {
            'fields': ('image',),
        }),
        ("Email options", {
            'fields': ('email_active',),
        })
    )

admin.site.register(User, CustomUserAdmin)
# Register your models here.
