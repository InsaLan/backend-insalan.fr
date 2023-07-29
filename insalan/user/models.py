"""
Module for the definition of models tied to users
"""

from typing import Optional, List
from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError(_('An email is required')) # TODO: translation?
        if not username:
            raise ValueError(_('An username is required'))
        if not password:
            raise ValueError(_('A password is required'))
        user = self.model(
                email=self.normalize_email(email),
                username=username,
                date_joined=date.today()
                )
        user.set_password(password)
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

    email = models.EmailField(verbose_name='email address',
                              max_length=255,
                              unique=True,
                              blank=False)
    email_active = models.BooleanField(verbose_name='Email Activated',
                                       default=False)
    object = UserManager()
