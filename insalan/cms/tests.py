from django.db.utils import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from insalan.cms.models import Constant, Content


class ContentTestCase(TestCase):
    def test_content_with_constants(self):
        """test that we can create a content using constant"""
        Constant.objects.create(name="a", value="je suis la valeur a")
        Constant.objects.create(name="b", value="je suis la valeur b")
        Content.objects.create(
            name="content_a", content="j'appelle la constante ${a} et la constante ${b}"
        )

    def test_content_with_unknow_constants(self):
        """test that a ValidationError is raised in case of unknown constant used in a content"""
        Constant.objects.create(name="a", value="je suis la valeur a")
        Content.objects.create(
            name="content", content="je suis ${a} mais aussi une variable ${random}"
        )
        self.assertRaises(ValidationError)

    def test_display_undefined_constant_list(self):
        """
        Test that a ValidationError raised by the usage of unknown constants give the correct list of undefined constants
        """
        Content.objects.create(
            name="content",
            content="je test ${inconnue} mais aussi une variable ${random}",
        )
        self.assertRaisesMessage(
            ValidationError,
            _("Des constantes non définies sont utilisées: inconnue, random"),
        )

    def test_create_two_contents_with_same_name(self) -> None:
        """Test that the name unicity of a content is checked"""
        with self.assertRaises(IntegrityError):
            Content.objects.create(name="content", content="content1")
            Content.objects.create(name="content", content="content2")


class ConstantTestCase(TestCase):
    def test_create_two_constants_with_same_name(self) -> None:
        """Test that the name unicity of a constant is checked"""
        with self.assertRaises(IntegrityError):
            Constant.objects.create(name="const", value="1")
            Constant.objects.create(name="const", value="2")
