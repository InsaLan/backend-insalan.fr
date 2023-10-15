import logging
import itertools

import uuid

from decimal import Decimal
from datetime import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from insalan.tournament.models import Tournament
from insalan.user.models import User

logger = logging.getLogger(__name__)


class TransactionStatus(models.TextChoices):
    """Information about the current transaction status"""

    FAILED = "FAILED", _("échouée")
    SUCCEEDED = "SUCCEEDED", _("Réussie")
    PENDING = "PENDING", _("En attente")


class ProductCategory(models.TextChoices):
    """Different recognized categories of products"""

    REGISTRATION_PLAYER = "PLAYER_REG", _("Inscription joueur⋅euse")
    REGISTRATION_MANAGER = "MANAGER_REG", _("Inscription manager")
    PIZZA = "PIZZA", _("Pizza")


class Product(models.Model):
    """Object to represent in database anything sellable"""

    price = models.DecimalField(
        null=False, max_digits=5, decimal_places=2, verbose_name=_("prix")
    )
    name = models.CharField(max_length=50, verbose_name=_("intitulé"))
    desc = models.CharField(max_length=50, verbose_name=_("description"))
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
        verbose_name=_("Identifiant de paiement"),
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
        logger.debug(f"in the constructor {data}")
        fields = {}
        fields["creation_date"] = timezone.make_aware(datetime.now())
        fields["last_modification_date"] = fields["creation_date"]
        fields["payer"] = data["payer"]
        transaction = Transaction.objects.create(**fields)
        data["products"].sort(key=lambda x: int(x.id))
        for pid, grouper in itertools.groupby(data["products"]):
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

    def run_prepare_hooks(self):
        """Run the preparation hook on all products"""
        self.product_callback(lambda cls: cls.prepare_transaction)

    def run_success_hooks(self):
        """Run the success hooks on all products"""
        self.product_callback(lambda cls: cls.payment_success)

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

        self.payment_status = TransactionStatus.SUCCEDED
        self.last_modification_date = timezone.make_aware(datetime.now())
        self.save()

    def fail_transaction(self):
        """set payment_statut to failed and update last_modification_date"""
        self.payment_status = TransactionStatus.FAILED
        self.last_modification_date = timezone.make_aware(datetime.now())
        self.save()

    def get_products(self):
        return self.products

    def get_products_id(self):
        return [product.id for product in self.products]


class ProductCount(models.Model):
    """M2M-Through class to store the amount of a product for a Transaction"""

    class Meta:
        """Meta information"""

        verbose_name = _("Nombre d'un produit")
        verbose_name_plural = _("Nombres d'un produit")
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
        Product, on_delete=models.SET_NULL, editable=False, verbose_name=_("Produit"), null=True
    )
    count = models.IntegerField(default=1, editable=True, verbose_name=_("Quantité"))
