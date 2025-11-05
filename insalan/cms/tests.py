"""
This module contains test cases for the models in the insalan.cms app.

The test cases cover the following models:
- Content
- Constant

Each test case verifies the functionality and behavior of the respective model.
"""
from django.db.utils import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.test import APITestCase
from rest_framework import status

from insalan.cms.serializers import FileSerializer
from insalan.cms.models import Constant, Content, File


class ContentTestCase(TestCase):
    """
    Test case for the Content model.
    """
    def test_content_with_constants(self) -> None:
        """test that we can create a content using constant"""
        Constant.objects.create(name="a", value="je suis la valeur a")
        Constant.objects.create(name="b", value="je suis la valeur b")
        Content.objects.create(
            name="content_a", content="j'appelle la constante ${a} et la constante ${b}"
        )

    def test_content_with_unknow_constants(self) -> None:
        """test that a ValidationError is raised in case of unknown constant used in a content"""
        Constant.objects.create(name="a", value="je suis la valeur a")
        Content.objects.create(
            name="content", content="je suis ${a} mais aussi une variable ${random}"
        )
        self.assertRaises(ValidationError)

    def test_display_undefined_constant_list(self) -> None:
        """
        Test that a ValidationError raised by the usage of unknown constants give the correct list
        of undefined constants
        """
        Content.objects.create(
            name="content",
            content="je test ${inconnue} mais aussi une variable ${random}",
        )
        self.assertRaisesMessage(
            ValidationError,
            str(_("Des constantes non définies sont utilisées: inconnue, random")),
        )

    def test_create_two_contents_with_same_name(self) -> None:
        """Test that the name unicity of a content is checked"""
        with self.assertRaises(IntegrityError):
            Content.objects.create(name="content", content="content1")
            Content.objects.create(name="content", content="content2")


class ConstantTestCase(TestCase):
    """
    Test case for the Constant model.
    """
    def test_create_two_constants_with_same_name(self) -> None:
        """Test that the name unicity of a constant is checked"""
        with self.assertRaises(IntegrityError):
            Constant.objects.create(name="const", value="1")
            Constant.objects.create(name="const", value="2")

class FileModelTestCase(TestCase):
    """
    Test the File model
    """

    def setUp(self) -> None:
        self.file = File.objects.create(
            name="Test File",
            file="test_file.txt"
        )

    def test_file_creation(self) -> None:
        """
        Test that a File object is created successfully
        """
        self.assertEqual(self.file.name, "Test File")
        self.assertEqual(self.file.file, "test_file.txt")

    def test_file_str_method(self) -> None:
        """
        Test the __str__ method of the File model
        """
        self.assertEqual(str(self.file), "[File] Test File")

    def test_file_upload_path(self) -> None:
        """
        Test the upload path of the file
        """
        self.assertTrue(self.file.file.url.startswith("/v1/media/"))

class FileFetchTests(APITestCase):
    """
    Test case for the FileFetch view.
    """
    def setUp(self) -> None:
        self.file1 = File.objects.create(name="file1", file="test_file.txt")
        self.file2 = File.objects.create(name="file2", file="test_file.txt")

    def test_get_all_files(self) -> None:
        """Test that we can get all files"""
        url = reverse('file/list')
        response = self.client.get(url)
        files = File.objects.all()
        serializer = FileSerializer(files, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for file_data in response.data:
            file_data['file'] = file_data['file'].replace('http://testserver', '')
        self.assertEqual(response.data, serializer.data)

    def test_get_file_by_name(self) -> None:
        """Test that we can get a file by its name"""
        url = reverse('file/name', kwargs={'name': self.file1.name})
        response = self.client.get(url)
        file = File.objects.get(name=self.file1.name)
        serializer = FileSerializer(file)
        for file_data in response.data:
            file_data['file'] = file_data['file'].replace('http://testserver', '')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [serializer.data])

class FullListTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('full/list')
        self.constant = Constant.objects.create(name="Test Constant", value="Test Value")
        self.content = Content.objects.create(name="Test Content", content="Test Content")
        self.file = File.objects.create(name="Test File", file="test_file.txt")

    def test_full_list(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("constants", response.data)
        self.assertIn("contents", response.data)
        self.assertIn("files", response.data)
        self.assertEqual(len(response.data["constants"]), 1)
        self.assertEqual(len(response.data["contents"]), 1)
        self.assertEqual(len(response.data["files"]), 1)
        self.assertEqual(response.data["constants"][0]["name"], self.constant.name)
        self.assertEqual(response.data["contents"][0]["name"], self.content.name)
        self.assertEqual(response.data["files"][0]["name"], self.file.name)
