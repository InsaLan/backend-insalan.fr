from djongo import models
from django.utils.translation import gettext_lazy as _
# Create your models here.
class Content(models.Model):
    """
    markdown content to place on the website pages
    """
    name = models.CharField(max_length=100, verbose_name=_('Nom du contenu'))
    content = models.TextField(verbose_name=_('Contenu'))

    class Meta:
        verbose_name = _("Contenu")
        verbose_name_plural = _("Contenus")

    def __str__(self) -> str:
        return f"[Content] {self.name}"


class Constant(models.Model):
    """
    This model stores the constant values on the insalan's website (e.g: date,
    staff, prices..)
    """
    name = models.CharField(max_length=100, verbose_name=_('Nom de la constante'))
    value = models.CharField(max_length=200, verbose_name=_('Valeur de la constante'))

    class Meta:
        verbose_name = _("Constante")
        verbose_name_plural = _("Constantes")

    def __str__(self) -> str:
        return f"[Constant] {self.name}"


