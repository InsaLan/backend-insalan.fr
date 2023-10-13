from django.db import models
from django.utils.translation import gettext_lazy as _
from insalan.user.models import User
from datetime import datetime
import uuid
from django.utils import timezone
import logging
from decimal import Decimal
logger = logging.getLogger(__name__)
class TransactionStatus(models.TextChoices):
    """Information about the current transaction status"""

    FAILED = "FAILED", _("échouée")
    SUCCEDED = "SUCCEEDED", _("Réussie")
    PENDING = "PENDING", _("En attente")


class Product(models.Model):
    """ Object to represent in database anything sellable"""
    price = models.DecimalField(null=False, max_digits=5, decimal_places=2, verbose_name=_("prix"))
    name = models.CharField(max_length=50, verbose_name=_("intitulé"))
    desc = models.CharField(max_length=50, verbose_name=_("description"))


class Transaction(models.Model):
    """A transaction is a record from helloasso intent. A transaction cannot exist alone and should be used only to reflect helloasso payment"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,verbose_name=_("Utilisateur"))
    products = models.ManyToManyField(Product) # A transaction can be composed of n products
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=TransactionStatus.PENDING,
        choices=TransactionStatus.choices,
        null=False,
        verbose_name=_("État de la Transaction"),
        )
    creation_date = models.DateTimeField(verbose_name=_("Date de creation"))
    last_modification_date = models.DateTimeField(verbose_name=_("Date de dernière modification"))
    amount = models.DecimalField(null=False, default=0.00, max_digits=5, decimal_places=2, verbose_name=_("Montant"))

    @staticmethod
    def new(**data):
        """ create a new transaction based on products id list and a payer """
        logger.debug(f"in the constructor {data}")
        fields = {}
        fields['creation_date'] = timezone.make_aware(datetime.now())
        fields['last_modification_date'] = fields['creation_date']
        fields['payer'] = data['payer']
        transaction = Transaction.objects.create(**fields)
        transaction.products.set(data['products'])
        transaction.synchronize_amount()
        return transaction

    def validate_transaction(self):
        """ set payment_statut to validated """

        self.payment_status = TransactionStatus.SUCCEDED
        self.last_modification_date = timezone.make_aware(datetime.now())
        self.save()

    def fail_transaction(self):
        """ set payment_statut to failed and update last_modification_date """
        self.payment_status = TransactionStatus.FAILED
        self.last_modification_date = timezone.make_aware(datetime.now())
        self.save()

    def get_products(self):
        return self.products

    def get_products_id(self):
        return [product.id for product in self.products]
