"""
This module contains the admin configuration for the CMS app.

It defines the admin classes for the Constant and Content models, and registers them with the Django
admin site.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin # type: ignore

from .models import Constant, Content, File


class ConstantAdmin(ModelAdmin):  # type: ignore
    """
    Admin class for the Constant model
    """
    list_display = ("name", "value")
    search_fields = ["name"]


admin.site.register(Constant, ConstantAdmin)
admin.site.register(Content)
admin.site.register(File)
