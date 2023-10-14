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
    """
    Admin handler for Transactions
    In the backoffice, Transactions can only be seen, they cannot be add, removed or changed this way
    """

    list_display = (
        "id",
        "payer",
        "payment_status",
        "creation_date",
        "intent_id",
        "last_modification_date",
        "amount",
    )
    search_fields = [
        "id",
        "payer",
        "products",
        "payment_status",
        "creation_date",
        "intent_id",
        "last_modification_date",
        "amount",
    ]

    def has_add_permission(self, request):
        """Remove the ability to add a transaction from the backoffice """
        return False
    
    def has_change_permission(self, request, obj=None):
        """ Remove the ability to edit a transaction from the backoffice """
        return False

    def has_delete_permission(self, request, obj=None):
        """ Remove the ability to edit a transaction from the backoffice """
        return False

admin.site.register(Transaction, TransactionAdmin)
