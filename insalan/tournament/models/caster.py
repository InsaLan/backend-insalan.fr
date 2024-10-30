from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from insalan.components.image_field import ImageField

class Caster(models.Model):
    """
    A Caster is someone that can cast a tournament.
    """
    name = models.CharField(
        max_length=42,
        null=False,
        blank=False,
        verbose_name=_("Nom du casteur")
    )
    image = ImageField(
        verbose_name=_("Photo de profil"),
        blank=True,
        null=True,
        upload_to="profile-pictures",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp", "avif"])
        ],
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    url = models.URLField(
        verbose_name=_("Lien twitch ou autre"),
        blank=True,
        null=True,
    )
