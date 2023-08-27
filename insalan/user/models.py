"""
Module for the definition of models tied to users
"""

from typing import Optional, List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
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
    # Actually only used for super-user CLI tool
    # REQUIRED_FIELDS = [
    #         'email',
    #         'first_name',
    #         'last_name',
    #         ]

# vim: set tw=80 cc=80:
