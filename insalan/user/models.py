"""
Module for the definition of models tied to users
"""
from datetime import datetime

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin, Permission

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from insalan.components.image_field import ImageField

class UserManager(BaseUserManager):
    """
    Managers the User objects (kind of like a serializer but not quite that)
    """

    # pylint: disable-next=unused-argument
    def create_user(self, email, username, password, password_validation=None, **extra_fields):
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
        # pylint: disable=attribute-defined-outside-init
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        # pylint: enable=attribute-defined-outside-init
        user.user_permissions.add(Permission.objects.get(codename="email_active"))
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

    image = ImageField(
        verbose_name=_("photo de profil"),
        blank=True,
        null=True,
        upload_to="profile-pictures",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp", "avif"])
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
        """
        Check if the user has the email_active permission
        """
        return self.has_perm("user.email_active")

    def set_email_active(self, active=True):
        """
        Set the email_active permission
        """
        if active:
            self.user_permissions.add(Permission.objects.get(codename="email_active"))
        else:
            self.user_permissions.remove(
                Permission.objects.get(codename="email_active")
            )
        self.save()


# vim: set tw=80 cc=80:
