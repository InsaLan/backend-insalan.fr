"""Payment Admin Panel Code"""

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Product, Transaction, Payment, TransactionStatus, Discount


class ProductAdmin(ModelAdmin[Product]):  # pylint: disable=unsubscriptable-object
    """Admin handler for Products"""

    list_display = ("id", "price", "name", "desc", "category", "associated_tournament",
                    "associated_timeslot")
    search_fields = ["id", "price", "name"]


admin.site.register(Product, ProductAdmin)


# @admin.action(description=_("Rembourser la transaction"))
# def reimburse_transactions(modeladmin, request, queryset):
#     """Reimburse all selected actions"""
#     for transaction in queryset:
#         (is_err, msg) = transaction.refund_transaction(request.user.username)
#         if is_err:
#             model_admin.message_user(
#                 request, _("Erreur: %(msg)s") % {"msg": msg}, messages.ERROR
#             )
#             break


class PaymentAdmin(ModelAdmin[Payment]):  # pylint: disable=unsubscriptable-object
    """Admin handler for payments."""

    list_display = ("id", "amount", "transaction")

    actions = ["export"]

    def has_add_permission(self, _request: HttpRequest) -> bool:
        """Remove the ability to add a payment from the backoffice"""
        return False

    def has_change_permission(self, _request: HttpRequest, _obj: Payment | None = None) -> bool:
        """Remove the ability to edit a payment from the backoffice"""
        return False

    def has_delete_permission(self, _request: HttpRequest, _obj: Payment | None = None) -> bool:
        """Remove the ability to edit a payment from the backoffice"""
        return False

    def export(self, request: HttpRequest, queryset: QuerySet[Payment]) -> HttpResponse:
        """
        Export the selected payments to a CSV file
        """
        export = "id;prix;type;statut;date de paiement;date de dernière modification\n"
        for payment in queryset:
            # /!\ This will be removed when the payment timeouts are implemented
            payment_status = payment.transaction.payment_status
            if payment.transaction.payment_status == TransactionStatus.PENDING:
                payment_status = TransactionStatus.FAILED
            payment_type = ", ".join(
                [product.name for product in payment.transaction.products.all()]
            )

            # pylint: disable-next=line-too-long
            export += f"{payment.id};{payment.amount};{payment_type};{payment_status};{payment.transaction.creation_date};{payment.transaction.last_modification_date}\n"
        response = HttpResponse(export, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=export.csv"
        return response
    export.short_description = "Exporter les paiements sélectionnés"  # type: ignore[attr-defined]


admin.site.register(Payment, PaymentAdmin)


class TransactionAdmin(ModelAdmin[Transaction]):  # pylint: disable=unsubscriptable-object
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

    def has_add_permission(self, _request: HttpRequest) -> bool:
        """Remove the ability to add a transaction from the backoffice"""
        return False

    def has_change_permission(self, _request: HttpRequest, _obj: Transaction | None = None) -> bool:
        """Remove the ability to edit a transaction from the backoffice"""
        return False

    def has_delete_permission(self, _request: HttpRequest, _obj: Transaction | None = None) -> bool:
        """Remove the ability to edit a transaction from the backoffice"""
        return False


admin.site.register(Transaction, TransactionAdmin)


class DiscountAdmin(ModelAdmin[Discount]):  # pylint: disable=unsubscriptable-object
    """
    Admin handler for Discounts
    """

    list_display = ("id", "discount", "user", "product", "used")
    search_fields = ["id", "discount", "user", "product", "reason"]


admin.site.register(Discount, DiscountAdmin)
