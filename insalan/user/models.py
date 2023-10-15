"""
Module for the definition of models tied to users
"""
from os import getenv
from datetime import datetime

import insalan.settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin, Permission
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator


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
            raise ValueError(_("Un courriel est requis"))
        if not username:
            raise ValueError(_("Un nom d'utilisateur·rice est requis"))
        if not password:
            raise ValueError(_("Un mot de passe est requis"))
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            image=None,
            date_joined=timezone.make_aware(datetime.now()),
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, username, password, **extra_fields):
        """
        Check that all required fields are present and create a superuser
        """
        if password is None:
            raise TypeError(_("Les superutilisateur·rices requièrent un mot de passe"))
        user = self.create_user(email, username, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        return user


class User(AbstractUser, PermissionsMixin):
    """
    A user is simply our own abstraction defined above the standard Django User
    class.
    """

    class Meta:
        """Meta options"""

        verbose_name = _("Utilisateur⋅rice")
        verbose_name_plural = _("Utilisateur⋅ices")
        permissions = [("email_active", _("L'utilisateur⋅ice a activé son courriel"))]

    def __init__(self, *args, **kwargs):
        AbstractUser.__init__(self, *args, **kwargs)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

    image = models.FileField(
        verbose_name=_("photo de profil"),
        blank=True,
        null=True,
        upload_to="profile-pictures",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg"])
        ],
    )

    email = models.EmailField(
        verbose_name=_("Courriel"), max_length=255, unique=True, blank=False
    )
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    display_name = models.CharField(max_length=50, blank=True)
    pronouns = models.CharField(max_length=20, blank=True, null=False, default="")
    status = models.CharField(max_length=100, blank=True, null=False, default="")
    is_staff = models.BooleanField(
        verbose_name="Part of the insalan team", default=False
    )
    is_superuser = models.BooleanField(
        verbose_name="Admin of the insalan team", default=False
    )
    is_active = models.BooleanField(default=True)
    object = UserManager()

    def is_email_active(self):
        return self.has_perm("user.email_active")

    def set_email_active(self, active=True):
        if active:
            self.user_permissions.add(Permission.objects.get(codename="email_active"))
        else:
            self.user_permissions.remove(
                Permission.objects.get(codename="email_active")
            )
        self.save()


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
            _("Confirmez votre courriel"),
            _("Confirmez votre adresse de courriel en cliquant sur ")
            + insalan.settings.PROTOCOL 
            + "://"
            + insalan.settings.WEBSITE_HOST
            + "/verification/"
            + user
            + "/"
            + token,
            None,  # Django falls back to default of settings.py
            [user_object.email],
            fail_silently=False,
        )

    @staticmethod
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
            + insalan.settings.PROTOCOL
            + "://"
            + insalan.settings.WEBSITE_HOST
            + "/reset-password/"
            + user
            + "/"
            + token,
            None,  # Django falls back to default of settings.py
            [user_object.email],
            fail_silently=False,
        )


# vim: set tw=80 cc=80:
