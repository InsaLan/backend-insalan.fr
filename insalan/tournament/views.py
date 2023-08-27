"""Views for the tournament module"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.serializers import PrimaryKeyRelatedField

from insalan.user.models import User, Player, Manager
import insalan.tournament.serializers as serializers

from .models import Event, Tournament, Game, Team

class ReadOnly(BasePermission):
    """Read-Only permissions"""
    def has_permission(self, request, _view):
        """Define the permissions for this class"""
        return request.method in SAFE_METHODS

class EventList(generics.ListCreateAPIView):
    """List all of the existing events"""
    pagination_class = None
    queryset = Event.objects.all().order_by('id')
    serializer_class = serializers.EventSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]

class OngoingEventList(generics.ListAPIView):
    """List all of the ongoing events"""
    pagination_class = None
    queryset = Event.objects.filter(ongoing=True).order_by('id')
    serializer_class = serializers.EventSerializer
    permission_classes = [permissions.AllowAny]

class EventDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about an Event"""
    serializer_class = serializers.EventSerializer
    queryset = Event.objects.all().order_by('id')
    permission_classes = [permissions.IsAdminUser|ReadOnly]

# Games
class GameList(generics.ListCreateAPIView):
    """List all known games"""
    pagination_class = None
    queryset = Game.objects.all().order_by('id')
    serializer_class = serializers.GameSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]

class GameDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a game"""
    serializer_class = serializers.GameSerializer
    queryset = Game.objects.all().order_by('id')
    permission_classes = [permissions.IsAdminUser|ReadOnly]

# Tournament
class TournamentList(generics.ListCreateAPIView):
    """List all known tournaments"""
    pagination_class = None
    queryset = Tournament.objects.all().order_by('id')
    serializer_class = serializers.TournamentSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]

class TournamentDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a tournament"""
    queryset = Tournament.objects.all().order_by('id')
    serializer_class = serializers.TournamentSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]

# Teams
class TeamList(generics.ListCreateAPIView):
    """List all known teams"""
    queryset = Team.objects.all().order_by('id')
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]

class TeamDetails(generics.RetrieveUpdateDestroyAPIView):
    """Details about a team"""
    queryset = Team.objects.all().order_by('id')
    serializer_class = serializers.TeamSerializer
    permission_classes = [permissions.IsAdminUser|ReadOnly]

# Registration finders
class PlayerRegistration(generics.RetrieveAPIView):
    """Get the registration of a player"""
    serializer_class = serializers.PlayerSerializer
    queryset = Player.objects.all().order_by('id')

class PlayerRegistrationList(generics.ListAPIView):
    """Get all player registrations"""
    pagination_class = None
    serializer_class = serializers.PlayerSerializer
    queryset = Player.objects.all().order_by('id')

class PlayerRegistrationListId(generics.ListAPIView):
    """Find all player registrations of a user from their ID"""
    pagination_class = None
    serializer_class = serializers.PlayerIdSerializer
    def get_queryset(self):
        """Obtain the queryset fot this view"""
        return Player.objects.filter(user_id=self.kwargs['user_id'])

class PlayerRegistrationListName(generics.ListAPIView):
    """Find all player registrations of a user from their username"""
    pagination_class = None
    serializer_class = serializers.PlayerIdSerializer
    def get_queryset(self):
        """Obtain the queryset fot this view"""
        user = None
        try:
            user = User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist as exc:
            raise NotFound() from exc
        return Player.objects.filter(user=user)

class ManagerRegistration(generics.RetrieveAPIView):
    """Show a manager registration"""
    serializer_class = serializers.ManagerSerializer
    queryset = Manager.objects.all().order_by('id')

class ManagerRegistrationList(generics.ListAPIView):
    """Show all manager registrations"""
    pagination_class = None
    serializer_class = serializers.ManagerSerializer
    queryset = Manager.objects.all().order_by('id')

class ManagerRegistrationListId(generics.ListAPIView):
    """Find all player registrations of a user from their ID"""
    pagination_class = None
    serializer_class = serializers.ManagerIdSerializer
    def get_queryset(self):
        """Obtain the queryset fot this view"""
        return Manager.objects.filter(user_id=self.kwargs['user_id'])

class ManagerRegistrationListName(generics.ListAPIView):
    """Find all player registrations of a user from their username"""
    pagination_class = None
    serializer_class = serializers.ManagerIdSerializer
    def get_queryset(self):
        """Obtain the queryset fot this view"""
        user = None
        try:
            user = User.objects.get(username=self.kwargs['username'])
        except User.DoesNotExist as exc:
            raise NotFound() from exc
        return Manager.objects.filter(user=user)
