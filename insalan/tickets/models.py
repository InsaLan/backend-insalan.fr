import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from insalan.user.models import User


class Ticket(models.Model):

    class Status(models.TextChoices):

        CANCELLED = 'CA', _('Annulé')
        SCANNED = 'SC', _('Scanné')
        VALID = 'VA', _('Valide')

    token: models.UUIDField = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    status: models.CharField = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.VALID,
    )
