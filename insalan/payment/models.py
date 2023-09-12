from django.db import models
from django.utils.translation import gettext_lazy as _
from insalan.user.models import User
import uuid

class TransactionStatus(models.TextChoices):
    """Information about the current transaction status"""

    FAILED = "FAILED", _("Fail")
    SUCCEDED = "SUCCEEDED", _("Success")


class Transaction(models.Model):
    """A transaction"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(null=False)
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=TransactionStatus.FAILED,
        choices=TransactionStatus.choices,
        null=False,
        verbose_name="Transaction status",
    )
    date = models.DateField()

