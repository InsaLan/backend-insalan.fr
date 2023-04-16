from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    def __init__(self, *args, **kwargs):
        AbstractUser.__init__(self, *args, **kwargs)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'

    email = models.EmailField(verbose_name='email address',
                              max_length=255,
                              unique=True,
                              blank=False)
    email_active = models.BooleanField(verbose_name='Email Activated',
                                       default=False)
    # Actually only used for super-user CLI tool
    # REQUIRED_FIELDS = [
    #         'email',
    #         'first_name',
    #         'last_name',
    #         ]
