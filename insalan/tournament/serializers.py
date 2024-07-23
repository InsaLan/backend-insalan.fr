"""Serializers for our objects"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

from rest_framework import serializers

from insalan.user.models import User

from .models import (Event, Tournament, Game, Team, Player, Manager,
                     Substitute, Caster, Group, GroupMatch, Bracket,
                     KnockoutMatch, SwissRound, SwissMatch, Score, Seat, 
                     SeatSlot)
from .models import (unique_event_registration_validator, tournament_announced,
                     max_players_per_team_reached,
                     tournament_registration_full,
                     max_substitue_per_team_reached, valid_name)

class ScoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Score
        fields = ["team","score"]

class GroupMatchSerializer(serializers.ModelSerializer):
    score = serializers.DictField(required=True,source="get_scores")

    class Meta:
        model = GroupMatch
        fields = "__all__"

class GroupSerializer(serializers.ModelSerializer):
    """Serializer for a group in a tournament"""

    teams = serializers.ListField(required=False,source="get_teams_id")
    matchs = GroupMatchSerializer(many=True,source="get_matchs")
    scores = serializers.DictField(required=False,source="get_scores")

    class Meta:
        """Meta options for the serializer"""

        model = Group
        fields = "__all__"

class KnockoutMatchSerializer(serializers.ModelSerializer):
    score = serializers.DictField(required=True,source="get_scores")

    class Meta:
        model = KnockoutMatch
        fields = "__all__"

class BracketSerializer(serializers.ModelSerializer):
    teams = serializers.ListField(source="get_teams_id")
    matchs = KnockoutMatchSerializer(many=True,source="get_matchs")
    winner = serializers.IntegerField(source="get_winner")
    depth = serializers.IntegerField(required=False,source="get_depth")

    class Meta:
        model = Bracket
        exclude = ["team_count"]

class SwissMatchSerializer(serializers.ModelSerializer):
    score = serializers.DictField(required=True,source="get_scores")

    class Meta:
        model = SwissMatch
        fields = "__all__"

class SwissRoundSerializer(serializers.ModelSerializer):
    teams = serializers.ListField(source="get_teams_id")
    matchs = SwissMatchSerializer(many=True,source="get_matchs")

    class Meta:
        model = SwissRound
        fields = "__all__"

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
        fields = ("id", "name", "short_name", "players_per_team", "substitute_players_per_team", "team_per_match")


class TournamentSerializer(serializers.ModelSerializer):
    """Serializer class for Tournaments"""

    teams = serializers.ListField(required=False, read_only=True, source="get_teams_id")
    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    casters = CasterSerializer(many=True, source="get_casters")
    groups = serializers.ListField(required=False,source="get_groups_id")
    brackets = serializers.ListField(required=False,source="get_brackets_id")
    swissRounds = serializers.ListField(required=False,source="get_swissRounds_id")

    class Meta:
        """Meta options of the serializer"""

        model = Tournament
        read_only_fields = (
            "id",
            "manager_price_online",
            "manager_price_onsite",
            "player_price_online",
            "player_price_onsite",
            "substitute_price_online",
            "substitute_price_onsite",
        )
        fields = "__all__"

    def to_representation(self, instance):
        """Remove all fields except id and is_announced when is_announced is False"""
        ret = super().to_representation(instance)
        if ret["is_announced"]:
            return ret
        return {"id": ret["id"], "is_announced": False}


class TeamSerializer(serializers.ModelSerializer):
    """Serializer class for Teams"""

    players = serializers.ListField(required=False, source="get_players_id")
    managers = serializers.ListField(required=False, source="get_managers_id")
    substitutes = serializers.ListField(required=False, source="get_substitutes_id")
    players_names_in_game = serializers.ListField(required=False, write_only=True)
    substitutes_names_in_game = serializers.ListField(required=False, write_only=True)

    class Meta:
        """Meta options of the team serializer"""

        model = Team
        read_only_fields = ("id",)
        fields = "__all__"
        extra_kwargs = {"password" : {"write_only": True}}

    def validate(self, data):
        if not tournament_announced(data["tournament"]):
            raise serializers.ValidationError(
                _("Ce tournoi n'est pas encore annoncé")
            )
        if tournament_registration_full(data["tournament"]):
            raise serializers.ValidationError(
                _("Ce tournoi est complet")
            )
        for user in data.get("get_players_id", []) + data.get("get_managers_id", []) + data.get("get_substitutes_id", []):
            event = Event.objects.get(tournament=data["tournament"])
            if not unique_event_registration_validator(user,event):
                raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )

        if len(data.get("players_names_in_game", [])) != len(data.get("get_players_id", [])):
            raise serializers.ValidationError(_("Il manque des name_in_games de joueur⋅euses"))

        if len(data.get("substitutes_names_in_game", [])) != len(data.get("get_substitutes_id", [])):
            raise serializers.ValidationError(_("Il manque des name_in_games de remplaçant⋅e⋅s"))

        # Validate the name in game
        for name in data.get("players_names_in_game", []):
            if not valid_name(data["tournament"].game, name):
                raise serializers.ValidationError(
                    _("Le pseudo en jeu n'est pas valide")
                )
        for name in data.get("substitutes_names_in_game", []):
            if not valid_name(data["tournament"].game, name):
                raise serializers.ValidationError(
                    _("Le pseudo en jeu n'est pas valide")
                )

        return data


    def create(self, validated_data):
        """Create a Team from input data"""

        # Catch the players and managers keywords
        players = validated_data.pop("get_players_id", [])
        managers = validated_data.pop("get_managers_id", [])
        substitutes = validated_data.pop("get_substitutes_id", [])
        players_names_in_game = validated_data.pop("players_names_in_game", [])
        substitutes_names_in_game = validated_data.pop("substitutes_names_in_game", [])

        validated_data["password"] = make_password(validated_data["password"])
        team_obj = Team.objects.create(**validated_data)

        for player, name_in_game in zip(players,players_names_in_game):
            user_obj = User.objects.get(id=player)
            Player.objects.create(user=user_obj, team=team_obj,name_in_game=name_in_game)

        for manager in managers:
            user_obj = User.objects.get(id=manager)
            Manager.objects.create(user=user_obj, team=team_obj)

        for sub, name_in_game in zip(substitutes,substitutes_names_in_game):
            user_obj = User.objects.get(id=sub)
            Substitute.objects.create(user=user_obj, team=team_obj, name_in_game=name_in_game)

        return team_obj

    def update(self, instance, validated_data):
        """Update a Team from input data"""

        # Catch the players and managers keywords
        if "get_players_id" in validated_data:
            # pylint: disable=unused-variable
            players_names_in_game = validated_data.pop("players_names_in_game", [])
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

        if "get_substitutes_id" in validated_data:
            substitutes = set(validated_data.pop("get_substitutes_id", []))
            existing = set(instance.get_substitutes_id())
            removed = existing - substitutes
            for uid in removed:
                Substitute.objects.get(user_id=uid).delete()
            new = substitutes - existing
            for uid in new:
                Substitute.objects.create(user_id=uid, team=instance)

        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])

        # Update all other fields
        super().update(instance, validated_data)

        return instance


class TeamMatchsSerializer(serializers.ModelSerializer):
    """Serializer for team matchs"""
    group_matchs = GroupMatchSerializer(many=True, source="get_group_matchs")
    bracket_matchs = KnockoutMatchSerializer(many=True, source="get_knockout_matchs")
    swiss_matchs = SwissMatchSerializer(many=True, source="get_swiss_matchs")

    class Meta:
        model = Team
        fields = ["id","group_matchs","bracket_matchs","swiss_matchs"]

class PlayerSerializer(serializers.ModelSerializer):
    """Serializer for a Player Registration"""
    password = serializers.CharField(write_only=True)

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = "__all__"

    def validate(self, data):
        event = Event.objects.get(tournament__team=data["team"])
        if not unique_event_registration_validator(data["user"],event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        del data["password"]
        if max_players_per_team_reached(data["team"]):
            raise serializers.ValidationError(
                _("Nombre maximum de joueur⋅euses par équipe atteint")
            )
        if not tournament_announced(data["team"].tournament):
            raise serializers.ValidationError(
                _("Ce tournoi n'est pas encore annoncé")
            )
        if not valid_name(data["team"].tournament.game, data["name_in_game"]):
            raise serializers.ValidationError(
                _("Le pseudo en jeu n'est pas valide")
            )

        return data


class PlayerIdSerializer(serializers.Serializer):
    """Serializer to verify a list of player IDs"""

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = "__all__"

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id


class ManagerSerializer(serializers.ModelSerializer):
    """Serializer for a Manager Registration"""
    password = serializers.CharField(write_only=True)

    class Meta:
        """Meta options for the serializer"""

        model = Manager
        fields = "__all__"

    def validate(self, data):
        event = Event.objects.get(tournament__team=data["team"])
        if not unique_event_registration_validator(data["user"],event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        del data["password"]
        if not tournament_announced(data["team"].tournament):
            raise serializers.ValidationError(
                _("Ce tournoi n'est pas encore annoncé")
            )

        return data


class ManagerIdSerializer(serializers.ModelSerializer):
    """Serializer to verify a list of manager IDs"""

    class Meta:
        """Meta options for the serializer"""

        model = Manager
        fields = "__all__"

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id

class SubstituteSerializer(serializers.ModelSerializer):
    """Serializer for a Substitute Registration"""
    password = serializers.CharField(write_only=True)

    class Meta:
        """Meta options for the serializer"""

        model = Substitute
        fields = "__all__"

    def validate(self, data):
        event = Event.objects.get(tournament__team=data["team"])
        if not unique_event_registration_validator(data["user"],event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        del data["password"]
        if not tournament_announced(data["team"].tournament):
            raise serializers.ValidationError(
                _("Ce tournoi n'est pas encore annoncé")
            )
        if max_substitue_per_team_reached(data["team"]):
            raise serializers.ValidationError(
                _("Nombre maximum de remplaçant⋅e⋅s par équipe atteint")
            )
        if not valid_name(data["team"].tournament.game, data["name_in_game"]):
            raise serializers.ValidationError(
                _("Le pseudo en jeu n'est pas valide")
            )

        return data

class SubstituteIdSerializer(serializers.ModelSerializer):
    """Serializer to verify a list of Substitute IDs"""

    class Meta:
        """Meta options for the serializer"""

        model = Substitute
        fields = "__all__"

    def to_representation(self, instance):
        """Turn a Django object into a serialized representation"""
        return instance.id
    
class SeatSlotSerializer(serializers.ModelSerializer):
    """Serializer for a SeatSlot"""

    class Meta:
        """Meta options for the serializer"""

        model = SeatSlot
        fields = "__all__"

class SeatSerializer(serializers.ModelSerializer):
    """Serializer for a Seat"""

    class Meta:
        """Meta options for the serializer"""
        model = Seat
        fields = "__all__"

class FullDerefSwissMatchSerializer(serializers.ModelSerializer):
    """Serializer for a Swiss Match in a tournament"""

    class Meta:
        """Meta options for the serializer"""
        model = SwissMatch
        fields = "__all__"

class FullDerefSwissRoundSerializer(serializers.ModelSerializer):
    """Serializer for a Swiss Round in a tournament"""

    class Meta:
        """Meta options for the serializer"""
        model = SwissRound
        fields = "__all__"

class FullDerefKnockoutMatchSerializer(serializers.ModelSerializer):
    """Serializer for a knockout match in a tournament"""

    class Meta:
        """Meta options for the serializer"""
        model = KnockoutMatch
        fields = "__all__"

class FullDerefBracketSerializer(serializers.ModelSerializer):
    """Serializer for a bracket in a tournament"""

    class Meta:
        """Meta options for the serializer"""
        model = Bracket
        fields = "__all__"

class FullDerefGroupMatchSerializer(serializers.ModelSerializer):
    """Serializer for a group match in a tournament"""

    class Meta:
        """Meta options for the serializer"""
        model = GroupMatch
        fields = "__all__"

class FullDerefGroupSerializer(serializers.ModelSerializer):
    """Serializer for a group in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = Group
        fields = "__all__"


class FullDerefPlayerSerializer(serializers.ModelSerializer):
    """Serializer for a Player Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = ("id", "name_in_game", "payment_status")

class FullDerefManagerSerializer(serializers.ModelSerializer):
    """Serializer for a Manager Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Manager

    def to_representation(self, instance):
        """Remove all fields except id and is_announced when is_announced is False"""
        return instance.user.username

class FullDerefSubstituteSerializer(serializers.ModelSerializer):
    """Serializer for a Substitute Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Substitute
        fields = ("id", "name_in_game", "payment_status")

class FullDerefTeamSerializer(serializers.ModelSerializer):
    """Serializer class for Teams"""

    class Meta:
        """Meta options of the team serializer"""

        model = Team
        read_only_fields = ("id",)
        fields = ("id", "name", "validated", "captain")
