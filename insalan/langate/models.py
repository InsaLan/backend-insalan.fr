"""Langate models"""

from django.db import models

from insalan.user.models import User


class SimplifiedUserData:
    """
    Simplified Representation of User Data

    This class holds data that represents a minimal representation of a user's
    identity that is sufficient for the langate to create an account without
    tournament data.
    """

    username = models.CharField(max_length=100, blank=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(verbose_name="email address", max_length=255, blank=False)
    is_staff = models.BooleanField()
    is_admin = models.BooleanField()

    @classmethod
    def new(cls, user: User):
        # pylint: disable=line-too-long
        """
        Create a simplified version of a user's information

        See:
         - https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#django.contrib.auth.models.AbstractBaseUser
        """
        # pylint: enable=line-too-long
        s_user_data = cls()
        s_user_data.username = user.get_username()
        s_user_data.first_name = user.first_name
        s_user_data.last_name = user.last_name
        s_user_data.email = user.email
        s_user_data.is_staff = user.is_staff
        s_user_data.is_admin = user.is_superuser

        return s_user_data

class TournamentRegistration:
    """
    Tournament Registration for a User
    """

    shortname = models.CharField(max_length=50, blank=False)
    game_name = models.CharField(max_length=25, blank=False)
    team = models.CharField(max_length=25, blank=False)
    manager = models.BooleanField()
    has_paid = models.BooleanField()
    email = models.EmailField(verbose_name="email address", max_length=255, blank=False)


class LangateReply:
    """
    A reply to the Langate containing information issued after a user was
    authenticated. That information will help the langate create an account that
    can mirror the one found on the website.
    """

    class RegistrationStatus(models.TextChoices):
        """
        All possible "err" labels for langate reply information.
        """
        OK = ""
        NOT_PAID = "no_paid_place"
        NOT_REGISTERED = "registration_not_found"
        NOT_EXIST = "user_does_not_exist"

    user = SimplifiedUserData()
    err = models.CharField(max_length=25, choices=RegistrationStatus.choices)
    tournaments = list

    @classmethod
    def new(cls, user: User):
        """
        Create a new and very empty LangateReply

        The API already handled the concept of many/no user existing (it is not
        possible, it should not be possible, but we should be prepared for it
        to happen).
        """
        reply = LangateReply()

        reply.user = SimplifiedUserData.new(user)
        reply.tournaments = []

        return reply
