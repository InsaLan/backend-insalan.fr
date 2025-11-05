"""
This module contains the models for the CMS (Content Management System) of the InsaLan website.

The models include:
- Content: Represents markdown content to be placed on website pages.
- Constant: Stores constant values used on the InsaLan website.
"""

import re

from djongo import models  # type: ignore[import]
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

def constant_definition_validator(content: str) -> None:
    """
    Validator to ensure that any used constant in content is defined.
    """
    # validate that all constants used in the content are defined
    regex = re.compile(r"\${(?P<name>[^{}]*)}")
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
                f"Des constantes non définies sont utilisées: {', '.join(sorted(excess_constants))}"
            )
        )

    # validate that all files used in the content are defined
    regex = re.compile(r"\$\[(?P<name>[^\[\]]*)\]")
    file_list = set(
        re.findall(regex, content)
    )  # get the file names in the content
    p_files = set(
        file.name for file in File.objects.all()
    )  # retrieve every file names

    excess_files = file_list - p_files.intersection(
        file_list
    )  # Get the files in the content but not defined

    if len(excess_files) > 0:
        raise ValidationError(
            _(
                f"Des fichiers non définis sont utilisés: {', '.join(sorted(excess_files))}"
            )
        )


# Ignore type error because djongo doesn't have types stubs.
class Content(models.Model):  # type: ignore[misc]
    """
    Represents markdown content to be placed on website pages.
    """

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom du contenu")
    )
    content = models.TextField(
        verbose_name=_("Contenu"), validators=[constant_definition_validator]
    )

    class Meta:
        """
        Meta class for the Content model.
        """
        verbose_name = _("Contenu")
        verbose_name_plural = _("Contenus")

    def __str__(self) -> str:
        return f"[Content] {self.name}"


# Ignore type error because djongo doesn't have types stubs.
class Constant(models.Model):  # type: ignore[misc]
    """
    Stores the constant values on the InsaLan website (e.g: date, staff, prices..).
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nom de la constante"),
        validators=[
            RegexValidator(
                regex=r'^[^{}]*$',
                message=_("Le nom de la constante ne doit pas contenir les symboles { et }")
            )
        ]
    )
    value = models.CharField(max_length=200, verbose_name=_("Valeur de la constante"))

    class Meta:
        """
        Meta class for the Constant model.
        """
        verbose_name = _("Constante")
        verbose_name_plural = _("Constantes")

    def __str__(self) -> str:
        return f"[Constant] {self.name}"


# Ignore type error because djongo doesn't have types stubs.
class File(models.Model):  # type: ignore[misc]
    """
    Represents a file to be placed on website pages.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nom du fichier"),
        validators=[
            RegexValidator(
                regex=r'^[^[\]]*$',
                message=_("Le nom du fichier ne doit pas contenir les symboles [ et ]")
            )
        ]
    )
    file = models.FileField(
        verbose_name=_("Fichier"),
        upload_to="files/",
    )

    class Meta:
        """
        Meta class for the File model.
        """
        verbose_name = _("Fichier")
        verbose_name_plural = _("Fichiers")

    def __str__(self) -> str:
        return f"[File] {self.name}"
