import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Partner


def create_partner(name: str, url: str, partner_type: Partner.PartnerType
                   ) -> Partner:
    return Partner.objects.create(name=name, url=url, partner_type=partner_type)


def create_test_img(file_name: str = 'test.png') -> SimpleUploadedFile:
    test_img = io.BytesIO(b"test image")
    test_img.name = file_name
    return SimpleUploadedFile(test_img.name, test_img.getvalue())


class UserTestCase(TestCase):

    def setUp(self) -> None:
        create_partner('Partner', 'http://partner.com',
                       Partner.PartnerType.PARTNER)

    def test_get_existing_partner(self) -> None:
        partner = Partner.objects.get(id=1)
        self.assertEqual(partner.name, 'Partner')
        self.assertEqual(partner.url, 'http://partner.com')
        self.assertEqual(partner.partner_type, 'PA')

    def test_get_non_existing_partner(self) -> None:
        with self.assertRaises(Partner.DoesNotExist):
            Partner.objects.get(name='idontexist')


class PartnerListViewsTest(APITestCase):

    def test_get(self) -> None:
        create_partner('Partner 1', 'https://partner1.com',
                                 Partner.PartnerType.PARTNER)
        create_partner('Partner 2', 'https://partner2.com',
                                 Partner.PartnerType.SPONSOR)

        response = self.client.get(reverse('partners:list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 1,
                    'name': 'Partner 1',
                    'url': 'https://partner1.com',
                    'logo': None,
                    'partner_type': 'PA',
                },
                {
                    'id': 2,
                    'name': 'Partner 2',
                    'url': 'https://partner2.com',
                    'logo': None,
                    'partner_type': 'SP',
                }
            ],
        })

    def test_post(self) -> None:
        response = self.client.post(reverse('partners:list'), data={
            'name': 'New Partner',
            'url': 'https://new-partner.com',
            'logo': create_test_img(),
            'partner_type': Partner.PartnerType.PARTNER,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PartnerDetailViewTest(APITestCase):

    def test_get(self) -> None:
        create_partner('Partner 1', 'http://partner1.com',
                       Partner.PartnerType.PARTNER)
        response = self.client.get(reverse('partners:detail', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'Partner 1',
            'url': 'http://partner1.com',
            'logo': None,
            'partner_type': 'PA',
        })

        create_partner('Partner 2', 'http://partner2.com',
                       Partner.PartnerType.SPONSOR)
        response = self.client.get(reverse('partners:detail', args=[2]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': 2,
            'name': 'Partner 2',
            'url': 'http://partner2.com',
            'logo': None,
            'partner_type': 'SP',
        })

    def test_get_404(self) -> None:
        response = self.client.get(reverse('partners:detail', args=[0]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put(self) -> None:
        create_partner('partner 1', 'http://partner1.com',
                       Partner.PartnerType.PARTNER)
        response = self.client.put(reverse('partners:detail', args=[1]), data={
            'name': 'updated Partner 1',
            'url': 'http://updated-partner1.com',
            'logo': create_test_img('test-put.png'),
            'partner_type': Partner.PartnerType.SPONSOR,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch(self) -> None:
        create_partner('Partner 1', 'http://partner1.com',
                       Partner.PartnerType.PARTNER)
        response = self.client.patch(reverse('partners:detail', args=[1]),
                                     data={'name': 'updated Partner 1'},
                                     format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': 1,
            'name': 'updated Partner 1',
            'url': 'http://partner1.com',
            'logo': None,
            'partner_type': 'PA',
        })

    def test_delete(self) -> None:
        create_partner('Partner 1', 'http://partner1.com',
                       Partner.PartnerType.PARTNER)
        response = self.client.get(reverse('partners:detail', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.delete(reverse('partners:detail', args=[1]))

        response = self.client.get(reverse('partners:detail', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
