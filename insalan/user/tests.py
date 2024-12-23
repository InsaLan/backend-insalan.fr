"""User Tests Module"""
import json
import re

from typing import Dict
from django.test import TestCase
from django.core import mail
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission

from rest_framework.test import APIClient
from rest_framework import serializers

from insalan.user.models import User


class UserTestCase(TestCase):
    """
    Tests of the User model
    """

    def setUp(self):
        """
        Create some base users to do operations on
        """
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
        """
        Test getting all the fields of an already created user
        """
        u: User = User.objects.get(username="randomplayer")
        self.assertEqual(u.get_username(), "randomplayer")
        self.assertEqual(u.get_short_name(), "Random")
        self.assertEqual(u.get_full_name(), "Random Player")
        self.assertEqual(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password("IUseAVerySecurePassword"))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_existing_minimal_user(self):
        """
        Test getting all the fields of an user created with only the required fields
        """
        u: User = User.objects.get(username="anotherplayer")
        self.assertEqual(u.get_username(), "anotherplayer")
        self.assertEqual(u.get_short_name(), "")
        self.assertEqual(u.get_full_name(), "")
        self.assertEqual(u.get_user_permissions(), set())
        self.assertTrue(u.has_usable_password())
        self.assertTrue(u.check_password("ThisIsPassword"))
        self.assertTrue(u.is_active)
        self.assertFalse(u.is_staff)

    def test_get_non_existing_user(self):
        """
        Test that getting an user which does not exist throws an `User.DoesNotExist` error
        """
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="idontexist")

    def test_emojis_in_status(self):
        """
        Test if the user can put emojis in their status
        """
        user: User = User.objects.get(username="anotherplayer")
        user.status = "👾"
        user.save()
        self.assertEqual(User.objects.get(username="anotherplayer").status, "👾")


class UserEndToEndTestCase(TestCase):
    """
    Test cases of the API endpoints and workflows related to user model
    """

    client: APIClient

    def setUp(self):
        """
        Create a player to test getters
        """
        self.client = APIClient()
        user = User.objects.create_user(
            username="randomplayer",
            email="randomplayer@example.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
            is_active=True,
        )
        user.user_permissions.add(Permission.objects.get(codename="email_active"))


    def test_register_invalid_data(self):
        """
        Test trying to register a few invalid users
        """

        def send_invalid_data(data):
            request = self.client.post("/v1/user/register/", data, format="json")
            self.assertEqual(request.status_code, 400)
        send_invalid_data({})
        send_invalid_data({"username": "newuser"})
        send_invalid_data({"username": "newuser", "password": "1234"})
        send_invalid_data({"username": "newuser", "email": "email@example.com"})

    def test_register_valid_account(self):
        """
        Test registering valid users
        """

        def send_valid_data(data, check_fields=[]):
            """
            Helper function that will request a register and check its output
            """
            request = self.client.post("/v1/user/register/", data, format="json")

            self.assertEqual(request.status_code, 201)

            created_data: Dict = request.data
            for k, v in check_fields:
                self.assertEqual(created_data[k], v)

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
                "display_name" : "MARIO",
                "pronouns" : "he/him",
                "status" : "YAHOO!🍄",
            },
            [
                ("username", "PeachLover3003"),
                ("first_name", "Mario"),
                ("last_name", "Bros"),
                ("display_name", "MARIO"),
                ("pronouns", "he/him"),
                ("status", "YAHOO!🍄"),
                ("is_staff", False),
                ("is_superuser", False),
                ("is_active", True),
                ("email", "mario@mushroom.kingdom"),
            ],
        )

    def test_register_bot_account(self):
        """
        Test registering valid users
        """

        def send_bot_data(data):
            """
            Helper function that will request a register and check its output
            """
            request = self.client.post("/v1/user/register/", data, format="json")

            self.assertEqual(request.status_code, 400)
            self.assertRaises(serializers.ValidationError)

        send_bot_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
                "password_validation": "1111qwer!",
                "email": "email@example.com",
                "name": "je suis un bot"
            })

    def test_register_read_only_fields(self):
        """
        Test that the read-only register fields are indeed read-only
        """

        def send_valid_data(data, check_fields=[]):
            request = self.client.post("/v1/user/register/", data, format="json")

            self.assertEqual(request.status_code, 201)

            created_data: Dict = request.data
            for k, v in check_fields:
                self.assertEqual(created_data[k], v)

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
                ("email", "mario@mushroom.kingdom"),
            ],
        )

    def test_register_email_is_sent(self):
        """
        Test that an email is sent upon registration
        """
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
        """
        Test that an user can confirm their email with the link they received
        """
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        request = self.client.post("/v1/user/register/", data, format="json")
        user_pk = str(User.objects.get(username=data["username"]).pk)

        self.assertFalse(User.objects.get(username=data["username"]).is_email_active())
        match = re.match(
            ".*https?://[^ ]*/(?P<user_pk>[^ /]*)/(?P<token>[^ /]*)/",
            mail.outbox[0].body,
        )

        match_user_pk = match["user_pk"]
        token = match["token"]

        self.assertEqual(match_user_pk, user_pk)

        request = self.client.get(f"/v1/user/confirm/{match_user_pk}/{token}/")
        self.assertEqual(request.status_code, 200)

        self.assertTrue(User.objects.get(username=data["username"]).is_email_active())

    def test_can_confirm_email_only_once(self):
        """
        Test that an user can confirm their email only once
        """
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        self.client.post("/v1/user/register/", data, format="json")
        user_pk = User.objects.get(username=data["username"]).pk
        match = re.match(
            ".*https?://[^ ]*/(?P<user_pk>[^ /]*)/(?P<token>[^ /]*)/",
            mail.outbox[0].body,
        )

        match_user_pk = match["user_pk"]
        token = match["token"]

        request = self.client.get(f"/v1/user/confirm/{match_user_pk}/{token}/")
        self.assertEqual(request.status_code, 200)

        request = self.client.get(f"/v1/user/confirm/{match_user_pk}/{token}/")
        self.assertEqual(request.status_code, 400)

    def test_confirmation_email_is_token_checked(self):
        """
        Test that the token sent to an user for their email confirmation is really checked
        """
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
            ".*https?://[^ ]*/(?P<username>[^ /]*)/(?P<token>[^ /]*)/",
            mail.outbox[0].body,
        )

        username = match["username"]
        token = match["token"]
        token = list(token)
        token[-1] = "x"
        token = "".join(token)

        request = self.client.get(f"/v1/user/confirm/{username}/{token}/")

        self.assertEqual(request.status_code, 400)

    def test_login_invalid_account(self):
        """
        Try to login with invalid requests
        """

        def send_valid_data(data):
            request = self.client.post("/v1/user/login/", data, format="json")

            self.assertEqual(request.status_code, 404)
            self.assertEqual(
                request.data["user"][0],
                _("Nom d'utilisateur·rice ou mot de passe incorrect"),
            )

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
            }
        )

    def test_login_not_active_account(self):
        """
        Test trying to login to an account which email is not already activated
        """
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

    def test_login_email_not_confirmed_account(self):
        """
        Test trying to login to an account which email is not already activated
        """
        User.objects.create_user(
            username="newplayer",
            email="test@test.com",
            password="1111qwer!",
            is_active=True,
        )

        def send_valid_data(data):
            request = self.client.post("/v1/user/login/", data, format="json")

            self.assertEqual(request.status_code, 403)

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
            }
        )

    def test_login_account(self):
        """
        Test that when everything is ok, an user is able to login
        """
        user = User.objects.create_user(
            username="newplayer",
            email="test@test.com",
            password="1111qwer!",
            is_active=True,
        )
        user.user_permissions.add(Permission.objects.get(codename="email_active"))


        def send_valid_data(data):
            request = self.client.post("/v1/user/login/", data, format="json")

            self.assertTrue("sessionid" in self.client.cookies)

        send_valid_data(
            {
                "username": "newplayer",
                "password": "1111qwer!",
            }
        )

    def test_can_resend_confirmation_email(self):
        """
        Test that an user can request another confirmation email when
        requesting the right route
        """
        data = {
            "username": "ILoveEmail",
            "password": "1111qwer!",
            "password_validation": "1111qwer!",
            "email": "postman@example.com",
            "first_name": "Postman",
            "last_name": "Chronopost",
        }

        self.client.post("/v1/user/register/", data, format="json")

        self.assertEqual(len(mail.outbox), 1)

        self.client.post(
            "/v1/user/resend-email/", {"username": "ILoveEmail"}, format="json"
        )

        self.assertEqual(len(mail.outbox), 2)

        self.client.post(
            "/v1/user/resend-email/", {"username": "ILoveEmail"}, format="json"
        )

        self.assertEqual(len(mail.outbox), 3)

    def test_cant_resend_confirmation_if_already_valid(self):
        """
        Test that an user cannot resend a confirmation email if they already
        confirmed their email
        """
        user_object = User.objects.create_user(
            username="newplayer",
            email="test@example.com",
            password="1111qwer!",
        )
        user_object.set_email_active()
        user_object.save()

        request = self.client.post(
            "/v1/user/resend-email/", {"username": "ILoveEmail"}, format="json"
        )

        self.assertEqual(request.status_code, 400)

    def test_cant_resend_confirmation_if_nonexisting_user(self):
        """
        Test that we cannot resend a confirmation email for a non existing user
        without crashing the server
        """
        request = self.client.post(
            "/v1/user/resend-email/", {"username": "IDontExistLol"}, format="json"
        )

        self.assertEqual(request.status_code, 400)

    def test_dont_crash_resend_confirmation_if_empty(self):
        """
        Test that server doesn't crash if ask to resend an email without any
        valid data in request
        """
        request = self.client.post("/v1/user/resend-email/", {}, format="json")

        self.assertEqual(request.status_code, 400)

    def test_can_reset_password(self):
        """
        Test that an user can reset their password (full workflow)
        """
        data = {
            "email": "randomplayer@example.com",
        }

        self.client.post("/v1/user/password-reset/ask/", data, format="json")

        match = re.search(
            # "https?://[^ ]*/password-reset/ask[^ ]*",
            ".*https?://[^ ]*/(?P<user_pk>[^ &]*)/(?P<token>[^ /]*)/",
            mail.outbox[0].body,
        )

        user_pk = match["user_pk"]
        token = match["token"]
        username = User.objects.get(pk=user_pk).username

        data = {
            "user": user_pk,
            "token": token,
            "password": "UwU*nuzzles*621!",
            "password_confirm": "UwU*nuzzles*621!",
        }

        request = self.client.post(
            "/v1/user/password-reset/submit/", data, format="json"
        )
        self.assertEqual(request.status_code, 200)
        self.client.post("/v1/user/logout/", format="json")

        login_data = {
            "username": username,
            "password": "UwU*nuzzles*621!",
        }
        request = self.client.post("/v1/user/login/", login_data, format="json")
        self.assertEqual(request.status_code, 200)
        self.client.post("/v1/user/logout/", format="json")

        login_data = {
            "username": username,
            "password": "IUseAVerySecurePassword",
        }
        request = self.client.post("/v1/user/login/", login_data, format="json")
        self.assertEqual(request.status_code, 404)

    def test_can_reset_password_only_once(self):
        """
        Test that an user can reset their password only once with a token
        """
        data = {
            "email": "randomplayer@example.com",
        }

        self.client.post("/v1/user/password-reset/ask/", data, format="json")

        match = re.search(
            # "https?://[^ ]*/password-reset/ask[^ ]*",
            ".*https?://[^ ]*/(?P<user_pk>[^ &]*)/(?P<token>[^ /]*)/",
            mail.outbox[0].body,
        )

        user_pk = match["user_pk"]
        token = match["token"]

        data = {
            "user": user_pk,
            "token": token,
            "password": "UwU*nuzzles*621!",
            "password_confirm": "UwU*nuzzles*621!",
        }

        request = self.client.post(
            "/v1/user/password-reset/submit/", data, format="json"
        )
        self.assertEqual(request.status_code, 200)

        data = {
            "user": user_pk,
            "token": token,
            "password": "UwU*nuzzles*926!",
            "password_confirm": "UwU*nuzzles*926!",
        }

        request = self.client.post(
            "/v1/user/password-reset/submit/", data, format="json"
        )
        self.assertEqual(request.status_code, 400)

    def test_password_reset_is_token_checked(self):
        """
        Test that the password reset token is actually checked
        """
        data = {
            "email": "randomplayer@example.com",
        }

        self.client.post("/v1/user/password-reset/ask/", data, format="json")

        match = re.search(
            ".*https?://[^ ]*/(?P<user_pk>[^ &]*)/(?P<token>[^ /]*)/",
            mail.outbox[0].body,
        )

        user_pk = match["user_pk"]
        token = match["token"]
        token = list(token)
        token[-1] = "x"
        token = "".join(token)

        data = {
            "user": user_pk,
            "token": token,
            "password": "UwU*nuzzles*621!",
            "password_confirm": "UwU*nuzzles*621!",
        }

        request = self.client.post(
            "/v1/user/password-reset/submit/", data, format="json"
        )
        self.assertEqual(request.status_code, 400)

    def test_cant_edit_user_if_not_connected(self):
        """
        Test that we can't edit any field if we are not connected
        """
        request = self.client.patch(
            "/v1/user/me/",
            data={
                "current_password": "IUseAVerySecurePassword",
                "new_password": "AsDf!621$",
                "password_validation": "AsDf!621$",
            },
        )
        self.assertEqual(request.status_code, 403)

        request = self.client.patch(
            "/v1/user/me/",
            data={
                "email": "kevin@example.com",
            },
        )
        self.assertEqual(request.status_code, 403)

        request = self.client.patch(
            "/v1/user/me/",
            data={
                "last_name": "LesMaths",
            },
        )
        self.assertEqual(request.status_code, 403)

        request = self.client.patch(
            "/v1/user/me/",
            data={
                "first_name": "Kevin",
            },
        )
        self.assertEqual(request.status_code, 403)

    def test_cant_edit_other_user(self):
        """
        Test we can't edit any field of another user
        """
        c = APIClient()

        c.login(username="anotherplayer", password="ThisIsPassword")

        request = c.patch(
            "/v1/user/me/",
            data={
                "current_password": "IUseAVerySecurePassword",
                "new_password": "AsDf!621$",
                "password_validation": "AsDf!621$",
            },
        )
        self.assertEqual(request.status_code, 403)

        request = c.patch(
            "/v1/user/me/",
            data={
                "email": "kevin@example.com",
            },
        )
        self.assertEqual(request.status_code, 403)

        request = c.patch(
            "/v1/user/me/",
            data={
                "last_name": "LesMaths",
            },
        )
        self.assertEqual(request.status_code, 403)

        request = c.patch(
            "/v1/user/me/",
            data={
                "first_name": "Kevin",
            },
        )
        self.assertEqual(request.status_code, 403)

    def test_can_edit_self_single_field(self):
        """
        Test that we can edit our own fields individually
        """
        c = APIClient()

        c.login(username="randomplayer", password="IUseAVerySecurePassword")

        request = c.patch(
            "/v1/user/me/",
            data={
                "current_password": "IUseAVerySecurePassword",
                "new_password": "AsDf!621$",
                "password_validation": "AsDf!621$",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertTrue(
            User.objects.get(username="randomplayer").check_password("AsDf!621$")
        )

        c.login(username="randomplayer", password="AsDf!621$")

        request = c.patch(
            "/v1/user/me/",
            data={
                "email": "kevin@example.com",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            User.objects.get(username="randomplayer").email, "kevin@example.com"
        )

        request = c.patch(
            "/v1/user/me/",
            data={
                "last_name": "Les Maths",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            User.objects.get(username="randomplayer").last_name, "Les Maths"
        )

        request = c.patch(
            "/v1/user/me/",
            data={
                "first_name": "Kevin",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(User.objects.get(username="randomplayer").first_name, "Kevin")

        request = c.patch(
            "/v1/user/me/",
            data={
                "display_name": "Bornibus",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(User.objects.get(username="randomplayer").display_name, "Bornibus")

        request = c.patch(
            "/v1/user/me/",
            data={
                "pronouns": "he/him",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(User.objects.get(username="randomplayer").pronouns, "he/him")

        request = c.patch(
            "/v1/user/me/",
            data={
                "status": "Je suis un fournisseur de la base de donnée épicerie",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(User.objects.get(username="randomplayer").status, "Je suis un fournisseur de la base de donnée épicerie")


    def test_password_validation_error_are_caught(self):
        """
        Test that password validation errors does not crashes the server but sends a bad request instead
        """
        c = APIClient()

        c.login(username="randomplayer", password="IUseAVerySecurePassword")

        request = c.patch(
            "/v1/user/me/",
            data={
                "current_password": "IUseAVerySecurePassword",
                "new_password": "1234",
                "password_validation": "1234",
            },
        )
        self.assertEqual(request.status_code, 400)
        self.assertEqual(
            set(json.loads(request.content)["user"]),
            {
                "Ce mot de passe est trop court. Il doit contenir au minimum 8 caractères.",
                "Ce mot de passe est trop courant.",
                "Ce mot de passe est entièrement numérique.",
            },
        )
        # self.assertTrue(
        #     User.objects.get(username="randomplayer").check_password("AsDf!621$")
        # )

    def test_can_edit_several_fields_at_once(self):
        """
        Test that we can edit our own fields individually
        """
        c = APIClient()

        c.login(username="randomplayer", password="IUseAVerySecurePassword")

        request = c.patch(
            "/v1/user/me/",
            data={
                "current_password": "IUseAVerySecurePassword",
                "new_password": "AsDf!621$",
                "password_validation": "AsDf!621$",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertTrue(
            User.objects.get(username="randomplayer").check_password("AsDf!621$")
        )

        c.login(username="randomplayer", password="AsDf!621$")

        request = c.patch(
            "/v1/user/me/",
            data={
                "email": "kevin@example.com",
                "first_name": "Kevin",
                "last_name": "Les Maths",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            User.objects.get(username="randomplayer").email, "kevin@example.com"
        )
        self.assertEqual(
            User.objects.get(username="randomplayer").last_name, "Les Maths"
        )
        self.assertEqual(User.objects.get(username="randomplayer").first_name, "Kevin")

    def test_is_user_logged_out_on_password_change(self):
        """
        Test that when we change our password, we are logged out
        """
        c = APIClient()

        c.login(username="randomplayer", password="IUseAVerySecurePassword")

        request = c.patch(
            "/v1/user/me/",
            data={
                "current_password": "IUseAVerySecurePassword",
                "new_password": "AsDf!621$",
                "password_validation": "AsDf!621$",
            },
        )
        self.assertEqual(request.status_code, 200)
        self.assertTrue(
            User.objects.get(username="randomplayer").check_password("AsDf!621$")
        )

        self.assertEqual(c.cookies["sessionid"].value, "")
        self.assertEqual(
            json.loads(request.content),
            {
                "logout": [
                    _(
                        "Votre mot de passe a bien été changé. Merci de vous re-connecter"
                    )
                ]
            },
        )

    def test_permission_is_removed_when_changing_email(self):
        """
        Test that the email is no-longer considered as confirmed when we change it
        """
        c = APIClient()

        c.login(username="randomplayer", password="IUseAVerySecurePassword")

        request = c.patch(
            "/v1/user/me/",
            data={
                "email": "kevin@example.com",
            },
        )

        self.assertFalse(
            User.objects.get(username="randomplayer").has_perm("user.email_active")
        )
