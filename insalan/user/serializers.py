from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from django.core.exceptions import ValidationError

UserModel = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        exclude = ()
        # fields = ['url', 'username', 'email', 'groups']

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = '__all__'
    def create(self, data):
        user_object = UserModel.objects.create_user(email=data['email'],username=data['username'], password=data['password'])
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
