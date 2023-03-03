import os.path

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from insalan.settings import STATIC_URL


class Partner(models.Model):

    class PartnerType(models.TextChoices):
        PARTNER = 'PA', _('Partenaire')
        SPONSOR = 'SP', _('Sponsor')

    id: int
    name: models.CharField = models.CharField(max_length=200,
                                              verbose_name="Nom")
    url: models.URLField = models.URLField()
    logo: models.FileField = models.FileField(
        upload_to=os.path.join(STATIC_URL, 'partners'),
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg',
                                                               'jpeg', 'svg'])]
    )
    partner_type: models.CharField = models.CharField(
        verbose_name='Type',
        max_length=2,
        choices=PartnerType.choices,
        default=PartnerType.PARTNER,
    )
