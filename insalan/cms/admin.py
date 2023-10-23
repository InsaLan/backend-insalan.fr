from django.contrib import admin
from .models import Constant, Content


class ConstantAdmin(admin.ModelAdmin):
    list_display = ("name", "value")
    search_fields = ["name"]


admin.site.register(Constant, ConstantAdmin)
admin.site.register(Content)
