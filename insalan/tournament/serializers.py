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
                     SeatSlot, GroupTiebreakScore, MatchStatus,
                     BestofType)
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
    teams = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(),label="Liste des équipes", many=True)

    class Meta:
        model = GroupMatch
        fields = "__all__"

class GroupSerializer(serializers.ModelSerializer):
    """Serializer for a group in a tournament"""

    teams = serializers.ListField(required=False,source="get_teams_id")
    matchs = GroupMatchSerializer(required=False,many=True,source="get_matchs")
    scores = serializers.DictField(required=False,source="get_leaderboard")
    tiebreak_scores = serializers.DictField(required=False,source="get_tiebreaks")
    round_count = serializers.IntegerField(source="get_round_count")

    class Meta:
        """Meta options for the serializer"""

        model = Group
        fields = "__all__"

    def validate_tiebreak_scores(self, value: dict[str, int]):
        validated_data = value.copy()

        for team in value.keys():
            try:
                Team.objects.get(pk=team)
            except:
                del validated_data[team]

        return validated_data

    def update(self, instance, validated_data):
        tiebreak_scores: dict[str, int] = validated_data.pop("get_tiebreaks", {})

        for team_id, score in tiebreak_scores.items():
            team = Team.objects.get(pk=team_id)
            tiebreak_score, _ = GroupTiebreakScore.objects.update_or_create(team=team, group=instance, defaults={"score": score})
            tiebreak_score.save()
        
        super().update(instance, validated_data)

        return instance

class GenerateGroupsSerializer(serializers.Serializer):
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all())
    count = serializers.IntegerField(min_value=1)
    team_per_group = serializers.IntegerField(min_value=2)
    names = serializers.ListField()
    use_seeding = serializers.BooleanField()

    def validate(self, data):
        tournament: Tournament = data["tournament"]

        if tournament.group_set.exists():
            raise serializers.ValidationError(_("Des poules existent déjà."))

        count: int = data["count"]
        team_per_group: int = data["team_per_group"]
        validated_teams = tournament.get_validated_teams()

        if len(data["names"]) != count:
            raise serializers.ValidationError(_(f"Le nombre de noms de poules ({len(data['names'])}) ne correspond pas au nombre de poules demandées ({count})."))

        if count*2 > validated_teams or (count-1)*team_per_group >= validated_teams:
            raise serializers.ValidationError(_(f"{count} poules de {team_per_group} équipes permet d'accueillir entre {count*2} et {count*team_per_group} équipes, or il n'y a que {tournament.get_validated_teams()} équipes inscritent à ce tournoi. Veuillez revoir le nombre de poules et/ou le nombre d'équipes par poule."))

        if count*team_per_group > tournament.maxTeam:
            raise serializers.ValidationError(_(f"{count} poules de {team_per_group} équipes permet d'accueillir {count*team_per_group} équipes au maximum, or il peut y avoir au plus {tournament.maxTeam} équipes inscrites. Veuillez revoir le nombre de poules et/ou le nombre d'équipes par poule."))

        return data

class GenerateGroupMatchsSerializer(serializers.Serializer):
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all().prefetch_related("group_set"))
    groups = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all().prefetch_related("groupmatch_set"), many=True)
    bo_type = serializers.ChoiceField(BestofType)

    def validate(self, data):
        tournament: Tournament = data["tournament"]
        groups: List[Group] = data["groups"]

        if not all([tournament.group_set.contains(group) for group in groups]):
            raise serializers.ValidationError(_("Certaines poules ne font pas parti de ce tournoi ou il manque des poules dans la liste."))

        for group in groups:
            if group.groupmatch_set.filter(status__in=[MatchStatus.ONGOING, MatchStatus.COMPLETED]).exists():
                raise serializers.ValidationError(_("Impossible de créer les matchs, des matchs existent déjà et sont en cours ou terminés."))

        return data

class LaunchMatchsSerializer(serializers.Serializer):
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all())
    round = serializers.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        self.match_type = kwargs.pop("type", "")

        if self.match_type == "group":
            self.match_class = GroupMatch
        elif self.match_type == "swiss":
            self.match_class = SwissMatch
        elif self.match_type == "bracket":
            self.match_class = KnockoutMatch

        super().__init__(*args, **kwargs)

        self.fields["matchs"] = serializers.PrimaryKeyRelatedField(queryset=self.match_class.objects.all(), many=True, required=False)

    def validate(self, data):
        round = data.pop("round", 0)
        matchs = data.pop("matchs", [])
        data["warning"] = False

        if round:
            tournament = {f"{self.match_type}__tournament": data["tournament"]}
            if self.match_class.objects.filter(round_number__lt=round, **tournament).exclude(status=MatchStatus.COMPLETED).exists():
                raise serializers.ValidationError(_("Des matchs des round précédent sont encore en cours ou ne sont pas terminés."))

            scheduled_matchs = self.match_class.objects.filter(round_number=round, **tournament, status=MatchStatus.SCHEDULED)

            if not scheduled_matchs.exists():
                raise serializers.ValidationError(_("Tous les matchs sont déjà en cours ou bien terminés."))

            data["matchs"] = scheduled_matchs
        else:
            data["matchs"] = []

            for match in matchs:
                ongoing_teams_matchs = self.match_class.objects.filter(teams__in=match.teams.all()).exclude(pk=match.pk).filter(status=MatchStatus.ONGOING)

                if not ongoing_teams_matchs.exists():
                    data["matchs"].append(match)
                else:
                    data["warning"] = True

        return data

class KnockoutMatchSerializer(serializers.ModelSerializer):
    score = serializers.DictField(required=True,source="get_scores")
    teams = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(),label="Liste des équipes", many=True)

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
    teams = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(),label="Liste des équipes", many=True)

    class Meta:
        model = SwissMatch
        fields = "__all__"

class SwissRoundSerializer(serializers.ModelSerializer):
    teams = serializers.ListField(source="get_teams_id")
    matchs = SwissMatchSerializer(many=True,source="get_matchs")

    class Meta:
        model = SwissRound
        fields = "__all__"

class CreateSwissRoundsSerializer(serializers.Serializer):
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all())
    min_score = serializers.IntegerField(min_value=1)
    use_seeding = serializers.BooleanField()
    bo_type = serializers.ChoiceField(BestofType)

class GenerateSwissRoundRoundSerializer(serializers.Serializer):
    tournament = serializers.PrimaryKeyRelatedField(queryset=Tournament.objects.all())
    swiss = serializers.PrimaryKeyRelatedField(queryset=SwissRound.objects.all())
    round = serializers.IntegerField(min_value=2)

    def validate(self, data):
        tournament = data["tournament"]
        swiss = data["swiss"]
        round_idx = data["round"]

        if not tournament.swissround_set.contains(swiss):
            raise serializers.ValidationError(_("La ronde suisse ne fait pas partie de ce tournoi."))

        if round_idx > 2*swiss.min_score - 1:
            raise serializers.ValidationError(_("Le tour demandé ne fait pas partie de cette ronde suisse."))

        if SwissMatch.objects.filter(swiss=swiss, round_number=round_idx).exclude(status=MatchStatus.SCHEDULED).exists():
            raise serializers.ValidationError(_("Des matchs existent déjà et sont en cours ou terminés."))

        if SwissMatch.objects.filter(swiss=swiss, round_number=round_idx-1).exclude(status=MatchStatus.COMPLETED).exists():
            raise serializers.ValidationError(_("Des matchs du tour précédant n'ont pas encore commencés ou ne sont pas terminés."))

        return data


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
            "poster",
            "planning_file",
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
    # seat_slot = serializers.IntegerField(required=False, source="get_seat_slot_id")

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
        event = data["team"].tournament.event
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
        event = data["team"].tournament.event
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
        event = data["team"].tournament.event
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

class FullDerefTeamSerializer2(serializers.ModelSerializer):
    """Serializer class for Teams"""

    players = FullDerefPlayerSerializer(many=True,source="player_set")
    substitutes = FullDerefSubstituteSerializer(many=True,source="substitute_set")
    managers = FullDerefManagerSerializer(many=True,source="manager_set",read_only=True)
    captain = serializers.SlugRelatedField(slug_field="name_in_game",read_only=True)

    class Meta:
        """Meta options of the team serializer"""

        model = Team
        read_only_fields = ("id",)
        exclude = ["tournament", "password"]

class GroupField(serializers.ModelSerializer):
    """Serializer for a group in a tournament"""

    teams = serializers.ListField(required=False,source="get_teams_id")
    matchs = GroupMatchSerializer(many=True,source="get_matchs")
    scores = serializers.DictField(required=False,source="get_leaderboard")
    tiebreak_scores = serializers.DictField(required=False,source="get_tiebreaks")
    round_count = serializers.IntegerField(source="get_round_count")
    # seeding = serializers.DictField(source="get_teams_seeding")

    class Meta:
        """Meta options for the serializer"""

        model = Group
        exclude = ["tournament"]

class BracketField(serializers.ModelSerializer):
    teams = serializers.ListField(source="get_teams_id")
    matchs = KnockoutMatchSerializer(many=True,source="get_matchs")
    winner = serializers.IntegerField(source="get_winner")
    depth = serializers.IntegerField(required=False,source="get_depth")

    class Meta:
        model = Bracket
        exclude = ["team_count", "tournament"]

class SwissRoundField(serializers.ModelSerializer):
    teams = serializers.ListField(source="get_teams_id")
    matchs = SwissMatchSerializer(many=True,source="get_matchs")

    class Meta:
        model = SwissRound
        exclude = ["tournament"]

class FullDerefEventSeatField(serializers.RelatedField):
    def to_representation(self, value):
        return (value.x, value.y)

class FullDerefSeatSerializer(serializers.ModelSerializer):
    """Serializer for a Seat"""

    class Meta:
        """Meta options for the serializer"""
        model = Seat
        exclude = ["event"]

class FullDerefSeatSlotSerializer(serializers.ModelSerializer):
    """Serializer for a SeatSlot"""
    seats = FullDerefSeatSerializer(many=True)

    class Meta:
        """Meta options for the serializer"""

        model = SeatSlot
        exclude = ["tournament"]

class FullDerefEventSerializer(serializers.ModelSerializer):
    seats = FullDerefEventSeatField(many=True,source="seat_set",read_only=True)

    class Meta:
        model = Event
        fields = "__all__"

class FullDerefTournamentSerializer(serializers.ModelSerializer):
    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    casters = CasterSerializer(many=True, source="get_casters")
    teams = FullDerefTeamSerializer2(many=True)
    groups = GroupField(many=True,source="group_set")
    brackets = BracketField(many=True,source="bracket_set")
    swissRounds = SwissRoundField(many=True,source="swissround_set")
    event = FullDerefEventSerializer()
    game = GameSerializer()
    seatslots = FullDerefSeatSlotSerializer(many=True,source="seatslot_set")

    class Meta:
        model = Tournament
        fields = "__all__"

    def to_representation(self, value):
        if value.is_announced:
            return super().to_representation(value)
        return {"id": value.id, "is_announced": False}

class TeamSeedListSerializer(serializers.ListSerializer):
    def update(self, teams, validated_data):
        data_mapping = {item["id"]: item for item in validated_data}

        ret = []
        for team_id, seed in data_mapping.items():
            try:
                team = teams.get(id=team_id)
                ret.append(self.child.update(team, seed))
            except:
                pass

        return ret

class TeamSeedingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    
    class Meta:
        model = Team
        fields = ["id", "seed"]
        list_serializer_class = TeamSeedListSerializer
