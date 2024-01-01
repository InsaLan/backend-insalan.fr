"""Payment Models"""
from decimal import Decimal
from datetime import datetime
import itertools
import logging
import uuid

import requests

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework.serializers import ValidationError

import insalan.settings as app_settings

from insalan.tournament.models import Tournament
from insalan.user.models import User

from .tokens import Token

logger = logging.getLogger(__name__)


class TransactionStatus(models.TextChoices):
    """Information about the current transaction status"""

    FAILED = "FAILED", _("échouée")
    SUCCEEDED = "SUCCEEDED", _("Réussie")
    PENDING = "PENDING", _("En attente")
    REFUNDED = "REFUNDED", _("Remboursé")


class ProductCategory(models.TextChoices):
    """Different recognized categories of products"""

    REGISTRATION_PLAYER = "PLAYER_REG", _("Inscription joueur⋅euse")
    REGISTRATION_MANAGER = "MANAGER_REG", _("Inscription manager")
    REGISTRATION_SUBSTITUTE = "SUBSTITUTE_REG", _("Inscription remplaçant⋅e")
    PIZZA = "PIZZA", _("Pizza")


class Product(models.Model):
    """Object to represent in database anything sellable"""

    price = models.DecimalField(
        null=False, max_digits=5, decimal_places=2, verbose_name=_("prix")
    )
    name = models.CharField(max_length=80, verbose_name=_("intitulé"))
    desc = models.CharField(max_length=80, verbose_name=_("description"))
    category = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        verbose_name=_("Catégorie de produit"),
        default=ProductCategory.PIZZA,
        choices=ProductCategory.choices,
    )
    associated_tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        verbose_name=_("Tournoi associé"),
        null=True,
        blank=True,
    )
    available_from = models.DateTimeField(
        blank=True,
        null=False,
        default=timezone.now,
        verbose_name=_("Disponible à partir de"),
    )
    available_until = models.DateTimeField(
        null=False, verbose_name=_("Disponible jusqu'à")
    )

    def can_be_bought_now(self) -> bool:
        """Returns whether or not the product can be bought now"""
        return self.available_from <= timezone.now() <= self.available_until


class Payment(models.Model):
    """
    A single installment of a payment made through HelloAsso
    """

    class Meta:
        """Meta information"""

        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")

    id = models.IntegerField(
        primary_key=True, editable=False, verbose_name=_("Identifiant du paiement")
    )
    transaction = models.ForeignKey(
        "Transaction", on_delete=models.CASCADE, verbose_name=_("Transaction")
    )
    amount = models.DecimalField(
        blank=False,
        null=False,
        decimal_places=2,
        max_digits=6,
        verbose_name=_("Montant"),
    )


class Transaction(models.Model):
    """
    A transaction is a record from helloasso intent.

    A transaction cannot exist alone and should be used only to reflect helloasso payment
    """

    class Meta:
        """Meta information"""

        ordering = ["-last_modification_date"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, verbose_name=_("Utilisateur")
    )
    products = models.ManyToManyField(
        Product, through="ProductCount"
    )  # A transaction can be composed of n products
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=TransactionStatus.PENDING,
        choices=TransactionStatus.choices,
        null=False,
        verbose_name=_("État de la Transaction"),
    )
    creation_date = models.DateTimeField(verbose_name=_("Date de creation"))
    last_modification_date = models.DateTimeField(
        verbose_name=_("Date de dernière modification")
    )
    intent_id = models.IntegerField(
        blank=False,
        null=True,
        editable=False,
        verbose_name=_("Identifiant du formulaire de paiement"),
    )
    order_id = models.IntegerField(
        null=True,
        editable=False,
        verbose_name=_("Identifiant de commande"),
    )
    amount = models.DecimalField(
        null=False,
        default=0.00,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Montant"),
    )

    @staticmethod
    def new(**data):
        """create a new transaction based on products id list and a payer"""
        fields = {}
        fields["creation_date"] = timezone.make_aware(datetime.now())
        fields["last_modification_date"] = fields["creation_date"]
        fields["payer"] = data["payer"]
        transaction = Transaction.objects.create(**fields)
        data["products"].sort(key=lambda x: int(x.id))
        for pid, grouper in itertools.groupby(data["products"]):
            # Validate that the products can be bought
            if not pid.can_be_bought_now():
                transaction.delete()
                raise ValidationError(
                    {
                        "error": _("Le produit %(id)s est actuellement indisponible")
                        % {"id": pid.id}
                    }
                )
            if pid.associated_tournament and not pid.associated_tournament.is_announced:
                transaction.delete()
                raise ValidationError(
                    {
                        "error": _("Le tournoi %(id)s est actuellement indisponible")
                        % {"id": pid.associated_tournament.id}
                    }
                )
            count = len(list(grouper))
            proc = ProductCount.objects.create(
                transaction=transaction,
                product=pid,
                count=count,
            )
            proc.save()
        transaction.synchronize_amount()
        return transaction

    def product_callback(self, key):
        """Call a product callback on the list of product"""
        from insalan.payment.hooks import PaymentCallbackSystem

        for proccount in ProductCount.objects.filter(transaction=self):
            # Get callback class
            cls = PaymentCallbackSystem.retrieve_handler(proccount.product.category)
            if cls is None:
                logger.warning("No handler found for payment of %s", proccount.product)
                raise RuntimeError(_("Pas de handler trouvé pour un paiement"))
            # Call callback class
            key(cls)(self, proccount.product, proccount.count)

    def run_prepare_hooks(self) -> bool:
        """Run the preparation hook on all products"""
        from insalan.payment.hooks import PaymentCallbackSystem

        for proccount in ProductCount.objects.filter(transaction=self):
            # Get callback class
            cls = PaymentCallbackSystem.retrieve_handler(proccount.product.category)
            if cls is None:
                logger.warning("No handler found for payment of %s", proccount.product)
                raise RuntimeError(_("Pas de handler trouvé pour un paiement"))
            # Call callback class
            res = cls.prepare_transaction(self, proccount.product, proccount.count)
            if not res:
                return False

        return True

    def run_success_hooks(self):
        """Run the success hooks on all products"""
        self.product_callback(lambda cls: cls.payment_success)

    def run_refunded_hooks(self):
        """Run the refund hooks on all products"""
        self.product_callback(lambda cls: cls.payment_refunded)

    def run_failure_hooks(self):
        """Run the failure hooks on all products"""
        self.product_callback(lambda cls: cls.payment_failure)

    def refund_transaction(self, _requester="") -> tuple[bool, str]:
        """
        Refund this transaction

        Refund a succeeded transaction, deleting all associated payments and
        running associated hooks.
        """
        if self.payment_status != TransactionStatus.SUCCEEDED:
            if self.payment_status != TransactionStatus.REFUNDED:
                logger.warning("Attempt to refund %s in invalid state", self.id)
            return (True, _("Transaction %(id)s en état invalide") % {"id": self.id})

        # A lot of the code here is legacy from when this method initiated the
        # refund, instead of changing the model to reflect it

        # token = Token.get_instance()
        # body_refund = {
        # "comment": f"Refunded by {requester}",
        # "sendRefundEmail": True,
        # "cancelOrder": True,
        # }
        # headers_refund = {
        # "authorization": "Bearer " + token.get_token(),
        # "Content-Type": "application/json",
        # }

        # refunded_amount = Decimal("0.0")
        # for pay_obj in Payment.objects.filter(transaction=self):
        # # This bit is legacy, from when this was an action
        # refund_init = requests.post(
        # f"{app_settings.HA_URL}/v5/payments/{pay_obj.id}/refund/",
        # data=body_refund,
        # headers=headers_refund,
        # timeout=1,
        # )

        # if refund_init.status_code != 200:
        # return (
        # True,
        # _("Erreur de remboursement: code %(code)s obtenu via l'API")
        # % {
        # "code": refund_init.status_code,
        # },
        # )
        # refunded_amount += pay_obj.amount
        # pay_obj.delete()

        # if refunded_amount == self.amount:
        Payment.objects.filter(transaction=self).delete()
        logger.info("Transaction %s refunded for %s€", self.id, self.amount)
        self.payment_status = TransactionStatus.REFUNDED
        self.run_refunded_hooks()
        # else:
        # logger.warn(
        # "Only refunded %s€/%s€ of transaction %s",
        # refunded_amount,
        # self.amount,
        # self.id,
        # )

        self.touch()
        self.save()

        return (False, "")

    def synchronize_amount(self):
        """Recompute the amount from the product list"""
        self.amount = Decimal(0.00)
        for proc in ProductCount.objects.filter(transaction=self):
            self.amount += proc.product.price * proc.count
        self.save()

    def touch(self):
        """Update the last modification date of the transaction"""
        self.last_modification_date = timezone.make_aware(datetime.now())

    def validate_transaction(self):
        """set payment_statut to validated"""
        if self.payment_status != TransactionStatus.PENDING:
            if self.payment_status != TransactionStatus.SUCCEEDED:
                logger.warning("Attempted to validate %s in invalid state", self.id)
            return

        self.payment_status = TransactionStatus.SUCCEEDED
        self.last_modification_date = timezone.make_aware(datetime.now())
        self.save()
        logger.info("Transaction %s succeeded", self.id)
        self.run_success_hooks()

    def fail_transaction(self):
        """set payment_statut to failed and update last_modification_date"""
        if self.payment_status != TransactionStatus.PENDING:
            if self.payment_status != TransactionStatus.FAILED:
                logger.warning("Attempted to fail %s in invalid state", self.id)
            return

        self.payment_status = TransactionStatus.FAILED
        self.last_modification_date = timezone.make_aware(datetime.now())
        self.save()
        logger.info("Transaction %s failed", self.id)
        self.run_failure_hooks()

    def get_products(self):
        return self.products

    def get_products_id(self):
        return [product.id for product in self.products]


class ProductCount(models.Model):
    """M2M-Through class to store the amount of a product for a Transaction"""

    class Meta:
        """Meta information"""

        verbose_name = _("Quantité d'un produit")
        verbose_name_plural = _("Quantités de produits")
        constraints = [
            models.UniqueConstraint(
                fields=["transaction", "product"], name="product_count_m2m_through"
            )
        ]

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        editable=False,
        verbose_name=_("Transaction"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        editable=False,
        verbose_name=_("Produit"),
        null=True,
    )
    count = models.IntegerField(default=1, editable=True, verbose_name=_("Quantité"))
