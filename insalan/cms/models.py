from djongo import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import re


def constant_definition_validator(content: str):
    """
    validator to ensure that any used constant in content is defined
    """
    regex = re.compile("\$\{(?P<name>[^\{\}]*)\}")
    constant_list = set(
        re.findall(regex, content)
    )  # get the constant names in the content
    p_constants = set(
        constant.name for constant in Constant.objects.all()
    )  # retrieve every constant names

    excess_constants = constant_list - p_constants.intersection(
        constant_list
    )  # Get the constants in the content but not defined

    if len(excess_constants) > 0:
        raise ValidationError(
            _(
                "Des constantes non définies sont utilisées: {}".format(', '.join(sorted(excess_constants)))
            )
        )


class Content(models.Model):
    """
    markdown content to place on the website pages
    """

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom du contenu")
    )
    content = models.TextField(
        verbose_name=_("Contenu"), validators=[constant_definition_validator]
    )

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

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom de la constante")
    )
    value = models.CharField(max_length=200, verbose_name=_("Valeur de la constante"))

    class Meta:
        verbose_name = _("Constante")
        verbose_name_plural = _("Constantes")

    def __str__(self) -> str:
        return f"[Constant] {self.name}"
