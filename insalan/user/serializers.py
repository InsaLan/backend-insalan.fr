from django.contrib.auth.models import Group, Permission
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)
        # fields = ['url', 'username', 'email', 'groups']

class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    password_validation = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        read_only_fields = ('email',)
        fields = ['username', 'first_name', 'last_name', 'is_active', 'is_staff', 
                  'is_superuser', 'email', 'email_active', 'password', 'password_validation']

    def validate(self, data):
        """
        Validate user registration (password shall be confirmed)
        """
        if data['password'] != data['password_validation']:
            raise serializers.ValidationError(_("Password doesn't match"))
        return data

    def create(self, data):
        user_object = User.object.create_user(**data)
        user_object.save()
        return user_object

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def check_validity(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise ValidationError('user not found')
        return user

class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Permission
        exclude = ('content_type',)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        exclude = ()
        # fields = ['url', 'name']
