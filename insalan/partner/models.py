import os.path

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from insalan.settings import STATIC_URL


class Partner(models.Model):
    class PartnerType(models.TextChoices):
        """There are two types of sponsors"""

        PARTNER = "PA", _("Partenaire")
        SPONSOR = "SP", _("Sponsor")

    class Meta:
        """Meta options"""

        verbose_name = _("Partenaire")
        verbose_name_plural = _("Partenaires")

    id: int
    name: models.CharField = models.CharField(
        max_length=200, verbose_name=_("Nom du partenaire/sponsor")
    )
    url: models.URLField = models.URLField(verbose_name=_("URL"))
    logo: models.FileField = models.FileField(
        verbose_name=_("Logo"),
        upload_to=os.path.join(STATIC_URL, "partners"),
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg"])
        ],
    )
    partner_type: models.CharField = models.CharField(
        verbose_name=_("Type de partenariat"),
        max_length=2,
        choices=PartnerType.choices,
        default=PartnerType.PARTNER,
    )
