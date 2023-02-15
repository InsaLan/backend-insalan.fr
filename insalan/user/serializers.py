from django.contrib.auth.models import Group, Permission
from insalan.user.models import User
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        exclude = ()
        # fields = ['url', 'username', 'email', 'groups']


class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Permission
        exclude = ('content_type',)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        exclude = ()
        # fields = ['url', 'name']
