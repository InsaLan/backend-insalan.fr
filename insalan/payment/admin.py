# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django import forms
from django.contrib import admin

from .models import Product, Transaction


class ProductAdmin(admin.ModelAdmin):
    """Admin handler for Products"""

    list_display = ("price", "name", "desc")
    search_fields = ["price", "name"]


admin.site.register(Product, ProductAdmin)


class TransactionAdmin(admin.ModelAdmin):
    """Admin handler for Transactions"""

    list_display = (
        "id",
        "payer",
        "payment_status",
        "creation_date",
        "last_modification_date",
        "amount",
    )
    search_fields = [
        "id",
        "payer",
        "products",
        "payment_status",
        "creation_date",
        "last_modification_date",
        "amount",
    ]
    readonly_fields = ["amount"]

    def save_model(self, request, obj, form, change):
        """Save the model, recomputing the amount"""
        obj.synchronize_amount()
        super().save_model(request, obj, form, change)


admin.site.register(Transaction, TransactionAdmin)
