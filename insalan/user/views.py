from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from insalan.user.models import User
from insalan.user.serializers import (
    GroupSerializer,
    PermissionSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
    UserSerializer,
)

# TODO: change permission
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = UserSerializer


# TODO: change permission
class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows permissions to be viewed or edited.
    """

    queryset = Permission.objects.all().order_by("name")
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]


# TODO: change permission
class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


# class UserRegister(APIView):
class UserRegister(APIView):
    """
    API endpoint that allows user creation.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request):
        data = request.data  # TODO: add validation
        serializer = UserRegisterSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.create(data)
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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


class UserLogin(APIView):
    """
    API endpoint that allows user login
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def post(self, request):
        data = request.data
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.check_validity(data)
            login(request, user)
            return Response(serializer.data, status=status.HTTP_200_OK)


class UserLogout(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
