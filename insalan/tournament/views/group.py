from django.core.exceptions import PermissionDenied, BadRequest
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
from django.http import QueryDict
from django.contrib.auth.hashers import make_password

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication

from insalan.user.models import User, UserMailer
import insalan.tournament.serializers as serializers

from ..models import Player, Manager, Substitute, Event, Tournament, Game, Team, PaymentStatus, Group
from .permissions import ReadOnly, Patch

class GroupList(generics.ListCreateAPIView):
    """List of all groups or create a new group for a tournament"""

    pagination_class = None
    queryset = Group.objects.all().order_by("id")
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

class GroupDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a Group"""

    serializer_class = serializers.GroupSerializer
    queryset = Group.objects.all().order_by("id")
    permission_classes = [permissions.IsAdminUser | ReadOnly]