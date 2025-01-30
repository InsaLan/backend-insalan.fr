"""
This module contains the models for the CMS (Content Management System) of the InsaLan website.

The models include:
- Content: Represents markdown content to be placed on website pages.
- Constant: Stores constant values used on the InsaLan website.
"""

import re
import string

from djongo import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

def constant_definition_validator(content: str):
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
    regex = re.compile(r"\$<(?P<name>[^{}]*)>")
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


class Content(models.Model):
    """
    Represents markdown content to be placed on website pages.
    """

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom du contenu")
    )
    content = models.TextField(
        verbose_name=_("Contenu"), validators=[constant_definition_validator]
    )
    planning = models.BooleanField(
        default=False,
        verbose_name=_("Est-ce que ce contenu est un planning exporté depuis un gsheet ?"),
        help_text=_(
            "Si oui, les couleurs seront modifiées pour correspondre au site web."
        ),
    )

    class Meta:
        """
        Meta class for the Content model.
        """
        verbose_name = _("Contenu")
        verbose_name_plural = _("Contenus")

    def __str__(self) -> str:
        return f"[Content] {self.name}"

    def save(self, *args, **kwargs):
        """
        Override the save method to ensure that the content is valid.

        /!\ ------------------------------------ /!\
        TODO : This code is a temporary method to have working plannings on the website.

        It should be removed for the XIX edition of the InsaLan and replaced by a
        better solution. The best solution would be to use a calendar file (e.g: ics)
        and format it through the front. 

        /!\ ------------------------------------ /!\
        """
        # Apply some operations on the content to make it look better
        if self.planning:
            # Remove the first line of the content (meta tag is not needed)
            if self.content.startswith("<meta"):
                self.content = "\n".join(self.content.split("\n")[1:])
            # Replace background color and text color to match the website
            self.content = self.content.replace(
                "background-color:#f3f3f3", 
                "background-color:#434343"
            )
            self.content = self.content.replace("color:#555555", "color:#000000")
            self.content = self.content.replace(";color:#434343;", ";color:#f3f3f3;")
            self.content = self.content.replace("background-color:#ffffff;", "")
            # Replace border color
            self.content = re.sub(
                r"border-right:1px SOLID #[a-f0-9]*",
                "border-right:1px SOLID #000000",
                self.content
            )

            # Remove the letters in the table headers
            letters = string.ascii_uppercase
            for i in letters:
                # If we haven't reached the end of the columns
                if f">{i}<" in self.content:
                    # Remove the letter
                    self.content = self.content.replace(
                        f">{i}<", "><"
                    )
                else:
                    break

            # Remove the numbers in the table headers
            number = 1
            while True:
                # If we haven't reached the end of the rows
                if f">{number}<" in self.content:
                    # Remove the number
                    self.content = self.content.replace(
                        f">{number}<", "><"
                    )
                else:
                    break
                number += 1

        super().save(*args, **kwargs)


class Constant(models.Model):
    """
    Stores the constant values on the InsaLan website (e.g: date, staff, prices..).
    """

    name = models.CharField(
        max_length=100, unique=True, verbose_name=_("Nom de la constante")
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

class File(models.Model):
    """
    Represents a file to be placed on website pages.
    """

    name = models.CharField(
        max_length=100, verbose_name=_("Nom du fichier")
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
