from django.db import models
from django.utils.translation import gettext_lazy as _

from insalan.settings import STATIC_URL


class Partner(models.Model):

    class PartnerType(models.TextChoices):
        PARTNER = 'PA', _('Partner')
        SPONSOR = 'SP', _('Sponsor')


    name = models.CharField(max_length=200)
    url = models.URLField()
    logo = models.ImageField(upload_to=f'{STATIC_URL}partners')
    type = models.CharField(
        max_length=2,
        choices=PartnerType.choices,
        default=PartnerType.PARTNER,
    )
