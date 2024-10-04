"""Data Serializers for the InsaLan User module"""
# pylint: disable=too-few-public-methods

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User
from insalan.mailer import MailManager
from insalan.settings import EMAIL_AUTH


class UserSerializer(serializers.ModelSerializer):
    """Serializer for an User"""

    class Meta:
        """Meta class, used to set parameters"""

        model = User
        exclude = ("password",)
        # fields = ['url', 'username', 'email', 'groups']


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for a register for submission"""

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    first_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    pronouns = serializers.CharField(max_length=20, required=False, allow_blank=True)
    status = serializers.CharField(max_length=100, required=False, allow_blank=True)
    password_validation = serializers.CharField(write_only=True, required=True)
    image = serializers.FileField(
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp", "avif"])
        ],
    )
    name = serializers.CharField(write_only=True, required=False, allow_blank=True) #If this field is filled, something bad happened (bot), purposely ambiguous nament

    class Meta:
        """Meta class, used to set parameters"""

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "email",
            "image",
            "password",
            "name",
            "password_validation",
            "display_name",
            "pronouns",
            "status",
        ]

        read_only_fields = ("is_superuser", "is_active", "is_staff")
        write_only_fields = ("name", "password", "password_validation")

    def validate(self, data):
        """
        Validate user registration (password shall be confirmed)
        """
        if data["password"] != data["password_validation"]:
            raise serializers.ValidationError(_("Les mots de passe diffèrent"))
        if 'name' in data and data['name']:
            raise serializers.ValidationError(_("Inscription non conforme")) # confusing error message to deceive malicious user
        return data

    def create(self, data):
        user_object = User.object.create_user(**data)
        user_object.save()
        MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_email_confirmation(user_object)
        return user_object


class UserLoginSerializer(serializers.Serializer):
    """Serializer for a login form submission"""

    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        """Meta class, used to set parameters"""

        model = User

    def check_validity(self, data):
        """
        Checks thats:
            - Username & Password combination gives a good user
            - The account has not been deactivated
        """
        user = authenticate(username=data["username"], password=data["password"])
        if user is not None:
            if not user.is_active:
                raise serializers.ValidationError(_("Compte supprimé"))
        return user


class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for a django Permission"""

    class Meta:
        """Meta class, used to set parameters"""

        model = Permission
        exclude = ("content_type",)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for a django Group (used with Permissions)"""

    class Meta:
        """Meta class, used to set parameters"""

        model = Group
        exclude = ()
        # fields = ['url', 'name']
