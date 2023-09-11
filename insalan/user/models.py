"""
Module for the definition of models tied to users
"""

from os import getenv
from datetime import datetime

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Managers the User objects (kind of like a serializer but not quite that)
    """

    def create_user(
        self, email, username, password, password_validation=None, **extra_fields
    ):
        """
        check that all required fields are present and create an user
        """
        if not email:
            raise ValueError(_("An email is required"))
        if not username:
            raise ValueError(_("An username is required"))
        if not password:
            raise ValueError(_("A password is required"))
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            date_joined=timezone.make_aware(datetime.now()),
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
            self, email, username, password, **extra_fields
            ):
        if password is None:
            raise TypeError('Superusers must have a password.')
        user = self.create_user(email, username, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.email_active = True
        user.is_active = True
        user.save()

        return user

class User(AbstractUser, PermissionsMixin):
    """
    A user is simply our own abstraction defined above the standard Django User
    class.
    """

    def __init__(self, *args, **kwargs):
        AbstractUser.__init__(self, *args, **kwargs)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

    email = models.EmailField(
        verbose_name="email address", max_length=255, unique=True, blank=False
    )
    email_active = models.BooleanField(verbose_name="Email Activated", default=False)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    is_staff = models.BooleanField(
        verbose_name="Part of the insalan team", default=False
    )
    is_superuser = models.BooleanField(
        verbose_name="Admin of the insalan team", default=False
    )
    is_active = models.BooleanField(default=True)
    object = UserManager()


class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generate an email confirmation token.
    It's just a PasswordResetTokenGenerator with a different salt.

    (NB: the django app secret is also used as a salt)
    """

    def __init__(self):
        super().__init__()
        self.key_salt = "IWontLaunch8TwitchStreamsWhenConnectionIsAlreadyBad"


class UserMailer:
    """
    Send emails.
    """

    @staticmethod
    def send_email_confirmation(user_object: User):
        """
        Send an e-mail confirmation token to the user registring.
        """
        token = EmailConfirmationTokenGenerator().make_token(user_object)
        user = user_object.username
        # TODO Give a frontend page instead of direct API link
        send_mail(
            _("Confirmez votre e-mail"),
            _("Confirmez votre adresse e-mail en cliquant sur ")
            + "http://api."
            + getenv("WEBSITE_HOST", "localhost")
            + reverse("confirm-email", kwargs={"user": user, "token": token}),
            None,  # Django falls back to default of settings.py
            [user_object.email],
            fail_silently=False,
        )

    def send_password_reset(user_object: User):
        """
        Send a password reset token.
        """
        token = default_token_generator.make_token(user_object)
        user = user_object.username
        # TODO Give a frontend page instead of direct API link
        send_mail(
            _("Demande de ré-initialisation de mot de passe"),
            _(
                "Une demande de ré-initialisation de mot de passe a été effectuée"
                "pour votre compte. Si vous êtes à l'origine de cette demande,"
                "vous pouvez cliquer sur le lien suivant: "
            )
            + "http://api."
            + getenv("WEBSITE_HOST", "localhost")
            + reverse("reset-password")
            + "?"
            + urlencode(
                {
                    "user": user,
                    "token": token,
                }
            ),
            None,  # Django falls back to default of settings.py
            [user_object.email],
            fail_silently=False,
        )


# vim: set tw=80 cc=80:
