from typing import Dict
from django.test import TestCase
# from django.contrib.auth.models import Permission
# from django.contrib.contenttypes.models import ContentType

from rest_framework.test import APIClient

from insalan.user.models import User


class UserTestCase(TestCase):
    def setUp(self):
        u: User = User.objects.create_user(
                username='staffplayer',
                email='staff@insalan.fr',
                password='^ThisIsAnAdminPassword42$',
                first_name='Iam',
                last_name='Staff',
                )
        u.is_staff = True

        # TODO Actual permission and test it somewhere else
        # content_type = ContentType.objects.get_for_model(User)
        # p: Permission = Permission.objects.create(
        #         codename='can_do_stuff',
        #         name='Can do stuff',
        #         content_type=content_type)
        #
        # u.user_permissions.add(p)
        # u.save()

        User.objects.create_user(username='randomplayer',
                                 email='randomplayer@gmail.com',
                                 password='IUseAVerySecurePassword',
                                 first_name='Random',
                                 last_name='Player',
                                 )
        User.objects.create_user(username='anotherplayer',
                                 password='ThisIsPassword',
                                 )

    def test_get_existing_full_user(self):
        u: User = User.objects.get(username='randomplayer')
        self.assertEquals(u.get_username(), 'randomplayer')
        self.assertEquals(u.get_short_name(), 'Random')
        self.assertEquals(u.get_full_name(), 'Random Player')
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password('IUseAVerySecurePassword'))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_existing_minimal_user(self):
        u: User = User.objects.get(username='anotherplayer')
        self.assertEquals(u.get_username(), 'anotherplayer')
        self.assertEquals(u.get_short_name(), '')
        self.assertEquals(u.get_full_name(), '')
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password('ThisIsPassword'))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_non_existing_user(self):
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='idontexist')


class UserEndToEndTestCase(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()

    def test_register_invalid_data(self):
        def send_invalid_data(data):
            request = self.client.post('/user/register/',
                                       data,
                                       format='json')
            self.assertEquals(request.status_code, 400)

        send_invalid_data({})
        send_invalid_data({'username': 'newuser'})
        send_invalid_data({'username': 'newuser',
                           'password': '1234'})
        send_invalid_data({'username': 'newuser',
                           'email': 'email@example.com'})

    def test_register_valid_account(self):
        def send_valid_data(data, check_fields=[]):
            request = self.client.post('/user/register/',
                                       data,
                                       format='json')

            self.assertEquals(request.status_code, 201)

            created_data: Dict = request.data

            for k, v in check_fields:
                self.assertEquals(created_data[k], v)

        send_valid_data({
                'username': 'newplayer',
                'password': '1111',
                'email': 'email@example.com'
                },
                        [('username', 'newplayer'),
                         ('first_name', ''),
                         ('last_name', ''),
                         ('is_staff', False),
                         ('is_superuser', False),
                         ('is_active', True),
                         ('email_active', False),
                         ('email', 'email@example.com')])

        send_valid_data({
                'username': 'PeachLover3003',
                'password': 'It\'s a me!',
                'email': 'mario@mushroom.kingdom',
                'first_name': 'Mario',
                'last_name': 'Bros'
                },
                        [('username', 'PeachLover3003'),
                         ('first_name', 'Mario'),
                         ('last_name', 'Bros'),
                         ('is_staff', False),
                         ('is_superuser', False),
                         ('is_active', True),
                         ('email_active', False),
                         ('email', 'mario@mushroom.kingdom')])