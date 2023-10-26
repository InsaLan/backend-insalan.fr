"""Payment Admin Panel Code"""
# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django import forms
from django.contrib import admin, messages

from django.utils.translation import gettext_lazy as _

from .models import Product, Transaction, Payment


class ProductAdmin(admin.ModelAdmin):
    """Admin handler for Products"""

    list_display = ("id", "price", "name", "desc", "category", "associated_tournament")
    search_fields = ["id", "price", "name"]


admin.site.register(Product, ProductAdmin)


@admin.action(description=_("Rembourser la transaction"))
def reimburse_transactions(modeladmin, request, queryset):
    """Reimburse all selected actions"""
    for transaction in queryset:
        (is_err, msg) = transaction.refund_transaction(request.user.username)
        if is_err:
            modeladmin.message_user(
                request, _("Erreur: %(msg)s") % {"msg": msg}, messages.ERROR
            )
            break


class PaymentAdmin(admin.ModelAdmin):
    """
    Admin handler for payments"
    """

    list_display = ("id", "amount", "transaction")

    def has_add_permission(self, _request):
        """Remove the ability to add a payment from the backoffice"""
        return False

    def has_change_permission(self, _request, _obj=None):
        """Remove the ability to edit a payment from the backoffice"""
        return False

    def has_delete_permission(self, _request, _obj=None):
        """Remove the ability to edit a payment from the backoffice"""
        return False


admin.site.register(Payment, PaymentAdmin)


class TransactionAdmin(admin.ModelAdmin):
    """
    Admin handler for Transactions
    In the backoffice, Transactions can only be seen, they cannot be add,
    removed or changed this way
    """

    list_display = (
        "id",
        "payer",
        "payment_status",
        "creation_date",
        "intent_id",
        "order_id",
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
        "order_id",
        "last_modification_date",
        "amount",
    ]

    # actions = [reimburse_transactions]

    def has_add_permission(self, _request):
        """Remove the ability to add a transaction from the backoffice"""
        return False

    def has_change_permission(self, _request, _obj=None):
        """Remove the ability to edit a transaction from the backoffice"""
        return False

    def has_delete_permission(self, _request, _obj=None):
        """Remove the ability to edit a transaction from the backoffice"""
        return False


admin.site.register(Transaction, TransactionAdmin)
