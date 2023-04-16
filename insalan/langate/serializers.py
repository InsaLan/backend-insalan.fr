"""
Serializers for classes in the langate module.
"""

from rest_framework import serializers

class SimplifiedUserDataSerializer(serializers.Serializer):
    """
    Serializer class for SimplifiedUserData
    """
    username = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=255)

class TournamentRegistrationSerializer(serializers.Serializer):
    """
    Serializer for a TournamentRegistration
    """
    shortname = serializers.CharField(max_length=50)
    game_name = serializers.CharField(max_length=25)
    team = serializers.CharField(max_length=25)
    manager = serializers.BooleanField()
    has_paid = serializers.BooleanField()

class ReplySerializer(serializers.Serializer):
    """
    Serialize for LangateReplies
    """
    user = SimplifiedUserDataSerializer()
    err = serializers.CharField(max_length=25)
    tournaments = TournamentRegistrationSerializer(many=True)
