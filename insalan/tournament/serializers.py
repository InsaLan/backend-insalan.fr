"""Serializers for our objects"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from rest_framework import serializers

from .models import Event, Tournament, Game, Team, Player, Manager, unique_event_registration, Caster
from insalan.user.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

class CasterSerializer(serializers.ModelSerializer):
    """Serializer for a tournament Caster"""

    class Meta:
        """Meta options for the serializer"""

        model = Caster
        exclude = ["tournament"]

class EventSerializer(serializers.ModelSerializer):
    # pylint: disable=R0903
    """Serializer for the tournament Event"""
    tournaments = serializers.ListField(
        required=False, read_only=True, source="get_tournaments_id"
    )

    class Meta:
        """Serializer meta options"""

        model = Event
        read_only_fields = ("id",)
        fields = [
            "id",
            "name",
            "description",
            "year",
            "month",
            "ongoing",
            "tournaments",
            "logo",
        ]


class GameSerializer(serializers.ModelSerializer):
    """Serializer for the tournament Games"""

    class Meta:
        """Meta options of the serializer"""

        model = Game
        read_only_fields = ("id",)
        fields = "__all__"


class TournamentSerializer(serializers.ModelSerializer):
    """Serializer class for Tournaments"""

    teams = serializers.ListField(required=False, read_only=True, source="get_teams_id")
    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    casters = CasterSerializer(many=True, source="get_casters")

    class Meta:
        """Meta options of the serializer"""

        model = Tournament
        read_only_fields = (
            "id",
            "manager_price_online",
            "manager_price_onsite",
            "player_price_online",
            "player_price_onsite",
        )
        fields = "__all__"

    def to_representation(self, instance):
        """Remove all fields except id and is_announced when is_announced is False"""
        ret = super().to_representation(instance)
        if ret["is_announced"]:
            return ret
        else:
            return {"id": ret["id"], "is_announced": False}


class TeamSerializer(serializers.ModelSerializer):
    """Serializer class for Teams"""

    players = serializers.ListField(required=False, source="get_players_id")
    managers = serializers.ListField(required=False, source="get_managers_id")
    players_pseudos = serializers.ListField(required=False, write_only=True)

    class Meta:
        """Meta options of the team serializer"""

        model = Team
        read_only_fields = ("id",)
        fields = "__all__"
        extra_kwargs = {"password" : {"write_only": True}}

    def validate(self, data):
        for user in data.get("get_players_id", []) + data.get("get_managers_id", []):
            event = Event.objects.get(tournament=data["tournament"])
            if not unique_event_registration(user,event):
                raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )

        if len(data.get("players_pseudos", [])) != len(data.get("get_players_id", [])):
            raise serializers.ValidationError(_("Il manque des pseudos de joueur⋅euses"))

        return data


    def create(self, validated_data):
        """Create a Team from input data"""

        # Catch the players and managers keywords
        players = validated_data.pop("get_players_id", [])
        managers = validated_data.pop("get_managers_id", [])
        players_pseudos = validated_data.pop("players_pseudos", [])

        validated_data["password"] = make_password(validated_data["password"])
        team_obj = Team.objects.create(**validated_data)

        for player, pseudo in zip(players,players_pseudos):
            user_obj = User.objects.get(id=player)
            Player.objects.create(user=user_obj, team=team_obj, pseudo=pseudo)

        for manager in managers:
            user_obj = User.objects.get(id=manager)
            Manager.objects.create(user=user_obj, team=team_obj)

        return team_obj

    def update(self, instance, validated_data):
        """Update a Team from input data"""

        # Catch the players and managers keywords
        if "get_players_id" in validated_data:
            players_pseudos = validated_data.pop("players_pseudos", [])
            players = set(validated_data.pop("get_players_id", []))

            existing = set(instance.get_players_id())
            removed = existing - players
            for uid in removed:
                Player.objects.get(user_id=uid).delete()
            new = players - existing
            for uid in new:
                Player.objects.create(user_id=uid, team=instance)

        if "get_managers_id" in validated_data:
            managers = set(validated_data.pop("get_managers_id", []))
            existing = set(instance.get_managers_id())
            removed = existing - managers
            for uid in removed:
                Manager.objects.get(user_id=uid).delete()
            new = managers - existing
            for uid in new:
                Manager.objects.create(user_id=uid, team=instance)

        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])

        # Update all other fields
        super().update(instance, validated_data)

        return instance


class PlayerSerializer(serializers.ModelSerializer):
    """Serializer for a Player Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = "__all__"

    def validate(self, data):
        event = Event.objects.get(tournament__team=data["team"])
        if not unique_event_registration(data["user"],event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        return data


class PlayerIdSerializer(serializers.Serializer):
    """Serializer to verify a list of player IDs"""

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id


class ManagerSerializer(serializers.ModelSerializer):
    """Serializer for a Manager Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Manager
        fields = "__all__"

    def validate(self, data):
        event = Event.objects.get(tournament__team=data["team"])
        if not unique_event_registration(data["user"],event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        return data


class ManagerIdSerializer(serializers.ModelSerializer):
    """Serializer to verify a list of manager IDs"""

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id
