from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

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
    image = models.FileField(
        verbose_name=_("Photo de profil"),
        blank=True,
        null=True,
        upload_to="profile-pictures",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp"])
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