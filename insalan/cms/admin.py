"""
This module contains the admin configuration for the CMS app.

It defines the admin classes for the Constant and Content models, and registers them with the Django admin site.
"""
from django.contrib import admin
from .models import Constant, Content


class ConstantAdmin(admin.ModelAdmin):
    """
    Admin class for the Constant model
    """
    list_display = ("name", "value")
    search_fields = ["name"]


admin.site.register(Constant, ConstantAdmin)
admin.site.register(Content)
