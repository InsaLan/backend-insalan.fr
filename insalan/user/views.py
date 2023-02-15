from django.contrib.auth.models import Group, Permission

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from insalan.user.models import User
from insalan.user.serializers import UserSerializer, \
    GroupSerializer, \
    PermissionSerializer


# TODO: change permission
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


# TODO: change permission
class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows permissions to be viewed or edited.
    """
    queryset = Permission.objects.all().order_by('name')
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]


# TODO: change permission
class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


# class UserRegister(APIView):
class UserRegister(CreateAPIView):
    """
    API endpoint that allows user creation.

    Don't forget the final `/` !
    """
    serializer_class = UserSerializer
    # def post(self, request, format=None):
    #     # TODO: Use another serializer ?
    #     # TODO: Check data validity
    #     serializer = UserSerializer(data=request.data,
    #                                 context={'request': request})
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     # u: User = User.objects.create_user()
    #
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
