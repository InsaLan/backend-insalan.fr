from django.test import TestCase
from insalan.user.models import InsalanUser


class UserTestCase(TestCase):
    def setUp(self):
        InsalanUser.objects.create_user(username='randomplayer',
                                        email='randomplayer@gmail.com',
                                        password='IUseAVerySecurePassword',
                                        first_name='Random',
                                        last_name='Player',
                                        )

    def test_get_existing_full_user(self):
        u: InsalanUser = InsalanUser.objects.get(username='randomplayer')
        self.assertEquals(u.get_username(), 'randomplayer')
        self.assertEquals(u.get_short_name(), 'Random')
        self.assertEquals(u.get_full_name(), 'Random Player')
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password('IUseAVerySecurePassword'))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_non_existing_full_user(self):
        with self.assertRaises(InsalanUser.DoesNotExist):
            InsalanUser.objects.get(username='idontexist')
