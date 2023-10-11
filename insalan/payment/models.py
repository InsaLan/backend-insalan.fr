from django.db import models
from django.utils.translation import gettext_lazy as _
from insalan.user.models import User
import uuid

class TransactionStatus(models.TextChoices):
    """Information about the current transaction status"""

    FAILED = "FAILED", _("échouée")
    SUCCEDED = "SUCCEEDED", _("Réussie")
    PENDING = "PENDING", _("En attente")


class Product(models.Model):
    """ Object to represent in database anything sellable"""
    price = models.DecimalField(null=False, max_digits=5, decimal_places=2)
    name = models.CharField(max_length=50)
    desc = models.CharField(max_length=50, verbose_name=_("description"))


class Transaction(models.Model):
    """A transaction"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product) # A transaction can be composed of n products
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=TransactionStatus.PENDING,
        choices=TransactionStatus.choices,
        null=False,
        verbose_name=_("Transaction status"),
        )
    date   = models.DateField()
    amount =  models.DecimalField(null=False, default=0.00, max_digits=5, decimal_places=2)

    def get_products_id(self):
        return self.products.id
