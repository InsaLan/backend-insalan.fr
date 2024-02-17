"""Payment Admin Panel Code"""
# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django.contrib import admin, messages

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from .models import Product, Transaction, Payment, TransactionStatus


class ProductAdmin(admin.ModelAdmin):
    """Admin handler for Products"""

    list_display = ("id", "price", "name", "desc", "category", "associated_tournament", "associated_timeslot")
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

    actions = ["export"]

    def has_add_permission(self, _request):
        """Remove the ability to add a payment from the backoffice"""
        return False

    def has_change_permission(self, _request, _obj=None):
        """Remove the ability to edit a payment from the backoffice"""
        return False

    def has_delete_permission(self, _request, _obj=None):
        """Remove the ability to edit a payment from the backoffice"""
        return False

    def export(self, request, queryset):
        """
        Export the selected payments to a CSV file
        """
        export = "id;prix;type;statut;date de paiement;date de dernière modification\n"
        for payment in queryset:
            # /!\ This will be removed when the payment timeouts are implemented
            payment_status = payment.transaction.payment_status
            if payment.transaction.payment_status == TransactionStatus.PENDING:
                payment_status = TransactionStatus.FAILED
            payment_type = ""
            for product in payment.transaction.products.all():
                payment_type += f"{product.name}, "
            payment_type = payment_type[:-2]

            export += f"{payment.id};{payment.amount};{payment_type};{payment_status};{payment.transaction.creation_date};{payment.transaction.last_modification_date}\n"
        response = HttpResponse(export, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=export.csv"
        return response

    export.short_description = "Exporter les paiements sélectionnés"

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
        "payer__username",
        "products__name",
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
