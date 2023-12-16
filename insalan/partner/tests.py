"""
This module contains test cases for the Partner model and its related views.

The test cases include:
- Creating a partner
- Retrieving an existing partner
- Retrieving a non-existing partner
- Listing partners
- Creating a new partner
- Retrieving a partner detail
- Updating a partner
- Deleting a partner
"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from insalan.user.models import User

from .models import Partner


def create_partner(name: str, url: str, partner_type: Partner.PartnerType) -> Partner:
    """
    Create a partner with the given name, url and type.
    """
    return Partner.objects.create(name=name, url=url, partner_type=partner_type)


def create_test_img(file_name: str = "test.png") -> SimpleUploadedFile:
    """
    Create a test image file.
    """
    test_img = io.BytesIO(b"test image")
    test_img.name = file_name
    return SimpleUploadedFile(test_img.name, test_img.getvalue())


class UserTestCase(TestCase):
    """
    Test case for the User model.
    """
    def setUp(self) -> None:
        """
        Create a test user.
        """
        create_partner("Partner", "http://partner.com", Partner.PartnerType.PARTNER)

    def test_get_existing_partner(self) -> None:
        """
        Test that we can retrieve an existing partner.
        """
        prtn = create_partner(
            "Partner", "http://partner.com", Partner.PartnerType.PARTNER
        )
        partner = Partner.objects.get(id=prtn.id)
        self.assertEqual(partner.name, "Partner")
        self.assertEqual(partner.url, "http://partner.com")
        self.assertEqual(partner.partner_type, "PA")

    def test_get_non_existing_partner(self) -> None:
        """
        Test that we can't retrieve a non-existing partner.
        """
        with self.assertRaises(Partner.DoesNotExist):
            Partner.objects.get(name="idontexist")


class PartnerListViewsTest(APITestCase):
    """
    Test case for the Partner list views.
    """
    def test_get(self) -> None:
        """
        Test that we can retrieve the list of partners.
        """
        prtn_one = create_partner(
            "Partner 1", "https://partner1.com", Partner.PartnerType.PARTNER
        )
        prtn_two = create_partner(
            "Partner 2", "https://partner2.com", Partner.PartnerType.SPONSOR
        )

        response = self.client.get(reverse("partners:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": prtn_one.id,
                    "name": "Partner 1",
                    "url": "https://partner1.com",
                    "logo": None,
                    "partner_type": "PA",
                },
                {
                    "id": prtn_two.id,
                    "name": "Partner 2",
                    "url": "https://partner2.com",
                    "logo": None,
                    "partner_type": "SP",
                },
            ],
        )

    def test_post(self) -> None:
        """
        Test that we can create a new partner.
        """
        User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.client.force_authenticate(user=User.objects.get(username="admin"))

        response = self.client.post(
            reverse("partners:list"),
            data={
                "name": "New Partner",
                "url": "https://new-partner.com",
                "logo": create_test_img(),
                "partner_type": Partner.PartnerType.PARTNER,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=None)


class PartnerDetailViewTest(APITestCase):
    """
    Test case for the Partner detail views.
    """
    def test_get(self) -> None:
        """
        Test that we can retrieve an existing partner.
        """
        prtn = create_partner(
            "Partner 1", "http://partner1.com", Partner.PartnerType.PARTNER
        )
        response = self.client.get(reverse("partners:detail", args=[prtn.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": prtn.id,
                "name": "Partner 1",
                "url": "http://partner1.com",
                "logo": None,
                "partner_type": "PA",
            },
        )

        prtn = create_partner(
            "Partner 2", "http://partner2.com", Partner.PartnerType.SPONSOR
        )
        response = self.client.get(reverse("partners:detail", args=[prtn.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": prtn.id,
                "name": "Partner 2",
                "url": "http://partner2.com",
                "logo": None,
                "partner_type": "SP",
            },
        )

    def test_get_404(self) -> None:
        """
        Test that we can't retrieve a non-existing partner.
        """
        # Find an ID that probably nobody has
        ids = Partner.objects.all().values_list(flat=True)
        max_id = max(ids) + 10 if len(ids) > 0 else 10
        response = self.client.get(reverse("partners:detail", args=[max_id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put(self) -> None:
        """
        Test that we can update an existing partner.
        """
        prtn = create_partner(
            "partner 1", "http://partner1.com", Partner.PartnerType.PARTNER
        )

        User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.client.force_authenticate(user=User.objects.get(username="admin"))

        response = self.client.put(
            reverse("partners:detail", args=[prtn.id]),
            data={
                "name": "updated Partner 1",
                "url": "http://updated-partner1.com",
                "logo": create_test_img("test-put.png"),
                "partner_type": Partner.PartnerType.SPONSOR,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)

    def test_patch(self) -> None:
        """
        Test that we can partially update an existing partner.
        """
        prtn = create_partner(
            "Partner 1", "http://partner1.com", Partner.PartnerType.PARTNER
        )

        User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.client.force_authenticate(user=User.objects.get(username="admin"))

        response = self.client.patch(
            reverse("partners:detail", args=[prtn.id]),
            data={"name": "updated Partner 1"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data,
            {
                "id": prtn.id,
                "name": "updated Partner 1",
                "url": "http://partner1.com",
                "logo": None,
                "partner_type": "PA",
            },
        )

        self.client.force_authenticate(user=None)

    def test_delete(self) -> None:
        """
        Test that we can delete an existing partner.
        """
        prtn = create_partner(
            "Partner 1", "http://partner1.com", Partner.PartnerType.PARTNER
        )
        prtn_id = prtn.id

        response = self.client.get(reverse("partners:detail", args=[prtn_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        User.objects.create(username="admin", is_superuser=True, is_staff=True)
        self.client.force_authenticate(user=User.objects.get(username="admin"))

        response = self.client.delete(reverse("partners:detail", args=[prtn_id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("partners:detail", args=[prtn_id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
