from django.db import models
from django.utils.translation import gettext_lazy as _

class PaymentStatus(models.TextChoices):
    """Information about the current payment status of a Player/Manager"""

    NOT_PAID = "NOTPAID", _("Pas payé")
    PAID = "PAID", _("Payé")
    PAY_LATER = "LATER", _("Payera sur place")