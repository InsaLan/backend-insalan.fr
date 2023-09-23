"""Data Serializers for the InsaLan User module"""

from django.contrib.auth.models import Group, Permission
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User

# pylint: disable=too-few-public-methods


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
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    password_validation = serializers.CharField(write_only=True, required=True)

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
            "email_active",
            "password",
            "password_validation",
        ]
        read_only_fields = ("is_superuser", "is_active", "is_staff")
        write_only_fields = ("password", "password_validation")

    def validate(self, data):
        """
        Validate user registration (password shall be confirmed)
        """
        if data["password"] != data["password_validation"]:
            raise serializers.ValidationError(_("Password doesn't match"))
        return data

    def create(self, data):
        user_object = User.object.create_user(**data)
        user_object.save()
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
        user = authenticate(username=data["username"],
                            password=data["password"])
        if user is not None:
            if not user.is_active or not user.email_active:
                raise serializers.ValidationError(_("Account not actived"))
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
