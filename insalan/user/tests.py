"""User Tests Module"""
from typing import Dict
from django.test import TestCase
from rest_framework.test import APIClient
from django.core import mail
from rest_framework import serializers
from insalan.user.models import User
import re


class UserTestCase(TestCase):
    def setUp(self):
        u: User = User.objects.create_user(
            username="staffplayer",
            email="staff@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
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

        User.objects.create_user(
            username="randomplayer",
            email="randomplayer@example.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
        )
        User.objects.create_user(
            username="anotherplayer",
            password="ThisIsPassword",
        )

    def test_get_existing_full_user(self):
        u: User = User.objects.get(username="randomplayer")
        self.assertEquals(u.get_username(), "randomplayer")
        self.assertEquals(u.get_short_name(), "Random")
        self.assertEquals(u.get_full_name(), "Random Player")
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password("IUseAVerySecurePassword"))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_existing_minimal_user(self):
        u: User = User.objects.get(username="anotherplayer")
        self.assertEquals(u.get_username(), "anotherplayer")
        self.assertEquals(u.get_short_name(), "")
        self.assertEquals(u.get_full_name(), "")
        self.assertEquals(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password("ThisIsPassword"))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_non_existing_user(self):
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="idontexist")


class UserEndToEndTestCase(TestCase):
    client: APIClient

    def setUp(self):
        self.client = APIClient()
        User.objects.create_user(
            username="randomplayer",
            email="randomplayer@example.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
            is_active=True,
            email_active=True,
        )

    def test_register_invalid_data(self):
        def send_invalid_data(data):
            request = self.client.post("/v1/user/register/", data, format="json")
            self.assertEquals(request.status_code, 400)

        send_invalid_data({})
        send_invalid_data({"username": "newuser"})
        send_invalid_data({"username": "newuser", "password": "1234"})
        send_invalid_data({"username": "newuser", "email": "email@example.com"})

    def test_register_valid_account(self):
        def send_valid_data(data, check_fields=[]):
            request = self.client.post("/v1/user/register/", data, format="json")

            self.assertEquals(request.status_code, 201)

            created_data: Dict = request.data
            for k, v in check_fields:
                self.assertEquals(created_data[k], v)

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
                "password_validation": "1111qwer!",
                "email": "email@example.com",
            },
            [
                ("username", "newplayer"),
                ("first_name", ""),
                ("last_name", ""),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email_active", False),
                ("email", "email@example.com"),
            ],
        )
        send_valid_data(
            {
                "username": "PeachLover3003",
                "password": "1111qwer!",
                "password_validation": "1111qwer!",
                "email": "mario@mushroom.kingdom",
                "first_name": "Mario",
                "last_name": "Bros",
            },
            [
                ("username", "PeachLover3003"),
                ("first_name", "Mario"),
                ("last_name", "Bros"),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email_active", False),
                ("email", "mario@mushroom.kingdom"),
            ],
        )

    def test_register_read_only_fields(self):
        def send_valid_data(data, check_fields=[]):
            request = self.client.post("/v1/user/register/", data, format="json")

            self.assertEquals(request.status_code, 201)

            created_data: Dict = request.data
            for k, v in check_fields:
                self.assertEquals(created_data[k], v)

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
                "password_validation": "1111qwer!",
                "email": "email@example.com",
                "is_staff": "true",
                "is_superuser": "true",
                "is_active": "false",
            },
            [
                ("username", "newplayer"),
                ("first_name", ""),
                ("last_name", ""),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email_active", False),
                ("email", "email@example.com"),
            ],
        )

        send_valid_data(
            {
                "username": "PeachLover3003",
                "password": "1111qwer!",
                "password_validation": "1111qwer!",
                "email": "mario@mushroom.kingdom",
                "first_name": "Mario",
                "last_name": "Bros",
            },
            [
                ("username", "PeachLover3003"),
                ("first_name", "Mario"),
                ("last_name", "Bros"),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email_active", False),
                ("email", "mario@mushroom.kingdom"),
            ],
        )

    def test_register_email_is_sent(self):
        data = {
            "username": "ILoveMail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        request = self.client.post("/v1/user/register/", data, format="json")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["postman@example.com"])

    def test_register_can_confirm_email(self):
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        request = self.client.post("/v1/user/register/", data, format="json")

        self.assertFalse(User.objects.get(username=data["username"]).email_active)

        match = re.match(
            ".*https?://[^ ]*/(?P<username>[^ /]*)/(?P<token>[^ /]*)",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]

        self.assertEquals(username, data["username"])

        request = self.client.get(f"/v1/user/confirm/{username}/{token}")
        self.assertEquals(request.status_code, 200)

        self.assertTrue(User.objects.get(username=data["username"]).email_active)

    def test_can_confirm_email_only_once(self):
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        self.client.post("/v1/user/register/", data, format="json")
        match = re.match(
            ".*https?://[^ ]*/(?P<username>[^ /]*)/(?P<token>[^ /]*)",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]

        request = self.client.get(f"/v1/user/confirm/{username}/{token}")
        self.assertEquals(request.status_code, 200)

        request = self.client.get(f"/v1/user/confirm/{username}/{token}")
        self.assertEquals(request.status_code, 400)

    def test_confirmation_email_is_token_checked(self):
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        self.client.post("/v1/user/register/", data, format="json")
        match = re.match(
            ".*https?://[^ ]*/(?P<username>[^ /]*)/(?P<token>[^ /]*)",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]
        token = list(token)
        token[-1] = "x"
        token = "".join(token)

        request = self.client.get(f"/v1/user/confirm/{username}/{token}")

        self.assertEquals(request.status_code, 400)

    def test_login_invalid_account(self):
        def send_valid_data(data):
            request = self.client.post("/v1/user/login/", data, format="json")

            self.assertEquals(request.status_code, 404)
            self.assertEquals(request.data["user"][0], "Wrong username or password")

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
            }
        )

    def test_login_not_active_account(self):
        User.objects.create_user(
            username="newplayer", email="test@test.com", password="1111qwer!"
        )

        def send_valid_data(data):
            self.client.post("/v1/user/login/", data, format="json")

            self.assertRaises(serializers.ValidationError)

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
            }
        )

    def test_login_account(self):
        User.objects.create_user(
            username="newplayer",
            email="test@test.com",
            password="1111qwer!",
            is_active=True,
            email_active=True,
        )

        def send_valid_data(data):
            request = self.client.post("/v1/user/login/", data, format="json")

            self.assertTrue("sessionid" in self.client.cookies)

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
            }
        )

    def can_resend_confirmation_email(self):
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        self.client.post("/v1/user/register/", data, format="json")

        self.assertEqual(mail.outbox, 1)

        self.client.post(
            "/v1/user/register/", {"username": "ILoveEmail"}, format="json"
        )

        self.assertEqual(mail.outbox, 2)

        self.client.post(
            "/v1/user/register/", {"username": "ILoveEmail"}, format="json"
        )

        self.assertEqual(mail.outbox, 3)

    def cant_resend_confirmation_if_already_valid(self):
        User.objects.create_user(
            username="newplayer",
            email="test@example.com",
            password="1111qwer!",
            email_active=True,
        )

        request = self.client.post(
            "/v1/user/resend-email/", {"username": "ILoveEmail"}, format="json"
        )

        self.assertEqual(request.status_code, 400)

    def cant_resend_confirmation_if_nonexisting_user(self):
        request = self.client.post(
            "/v1/user/resend-email/", {"username": "IDontExistLol"}, format="json"
        )

        self.assertEqual(request.status_code, 400)

    def dont_crash_resend_confirmation_if_empty(self):
        request = self.client.post("/v1/user/resend-email/", {}, format="json")

        self.assertEqual(request.status_code, 400)

    def test_can_reset_password(self):
        data = {
            "email": "randomplayer@example.com",
        }

        self.client.post("/v1/user/password/reset/ask/", data, format="json")

        match = re.search(
            # "https?://[^ ]*/password/reset/ask[^ ]*",
            ".*https?://[^ ]*/\?user=(?P<username>[^ &]*)&token=(?P<token>[^ /]*)",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]

        # self.assertFalse(User.objects.get(username=data["username"]).email_active)

        # self.assertEquals(username, data["username"])
        data = {
            "user": username,
            "token": token,
            "password": "UwU*nuzzles*621!",
            "password_confirm": "UwU*nuzzles*621!",
        }

        request = self.client.post(
            "/v1/user/password/reset/submit/", data, format="json"
        )
        self.assertEquals(request.status_code, 200)
        self.client.post("/v1/user/logout/", format="json")

        login_data = {
            "username": username,
            "password": "UwU*nuzzles*621!",
        }
        request = self.client.post("/v1/user/login/", login_data, format="json")
        self.assertEquals(request.status_code, 200)
        self.client.post("/v1/user/logout/", format="json")

        login_data = {
            "username": username,
            "password": "IUseAVerySecurePassword",
        }
        request = self.client.post("/v1/user/login/", login_data, format="json")
        self.assertEquals(request.status_code, 404)

    def test_can_reset_password_only_once(self):
        data = {
            "email": "randomplayer@example.com",
        }

        self.client.post("/v1/user/password/reset/ask/", data, format="json")

        match = re.search(
            # "https?://[^ ]*/password/reset/ask[^ ]*",
            ".*https?://[^ ]*/\?user=(?P<username>[^ &]*)&token=(?P<token>[^ /]*)",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]

        data = {
            "user": username,
            "token": token,
            "password": "UwU*nuzzles*621!",
            "password_confirm": "UwU*nuzzles*621!",
        }

        request = self.client.post(
            "/v1/user/password/reset/submit/", data, format="json"
        )
        self.assertEquals(request.status_code, 200)

        data = {
            "user": username,
            "token": token,
            "password": "UwU*nuzzles*926!",
            "password_confirm": "UwU*nuzzles*926!",
        }

        request = self.client.post(
            "/v1/user/password/reset/submit/", data, format="json"
        )
        self.assertEquals(request.status_code, 400)

    def test_password_reset_is_token_checked(self):
        data = {
            "email": "randomplayer@example.com",
        }

        self.client.post("/v1/user/password/reset/ask/", data, format="json")

        match = re.search(
            # "https?://[^ ]*/password/reset/ask[^ ]*",
            ".*https?://[^ ]*/\?user=(?P<username>[^ &]*)&token=(?P<token>[^ /]*)",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]
        token = list(token)
        token[-1] = "x"
        token = "".join(token)

        data = {
            "user": username,
            "token": token,
            "password": "UwU*nuzzles*621!",
            "password_confirm": "UwU*nuzzles*621!",
        }

        request = self.client.post(
            "/v1/user/password/reset/submit/", data, format="json"
        )
        self.assertEquals(request.status_code, 400)
