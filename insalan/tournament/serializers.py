"""Serializers for our objects"""

from __future__ import annotations

import sys
from collections import Counter
from math import ceil
from typing import Any, Type

from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

from rest_framework import serializers
from rest_framework.serializers import PrimaryKeyRelatedField, SlugRelatedField

from insalan.user.models import User

from .models import (
    Event,
    BaseTournament,
    EventTournament,
    PrivateTournament,
    Game,
    Team,
    Player,
    Manager,
    Substitute,
    Caster,
    Group,
    GroupMatch,
    Bracket,
    KnockoutMatch,
    SwissRound,
    SwissMatch,
    Score,
    Seat,
    SeatSlot,
    Seeding,
    GroupTiebreakScore,
    MatchStatus,
    BestofType,
    Match,
)
from .models import (
    unique_event_registration_validator,
    tournament_announced,
    max_players_per_team_reached,
    tournament_registration_full,
    private_tournament_password_matching,
    max_substitue_per_team_reached,
    valid_name,
)


class ScoreSerializer(serializers.ModelSerializer[Score]):
    """Serializer for Score objects"""

    class Meta:
        model = Score
        fields = ["team", "score"]


class MatchSerializer(serializers.ModelSerializer[Match]):
    """Generic Match object serializer"""

    score = serializers.DictField(required=True, source="get_scores")
    teams = PrimaryKeyRelatedField(
        queryset=Team.objects.all(), label="Liste des équipes", many=True
    )

    class Meta:
        model = Match
        fields = "__all__"

    def validate(self, data: Any) -> Any:
        data["score"] = data.pop("get_scores", {})
        if data["status"] == MatchStatus.COMPLETED:
            bo_type = data["bo_type"]
            team_count = len(data["teams"])
            max_score = 0
            winning_score = 0
            total_max_score = 0
            winner_count = 0

            if bo_type == BestofType.RANKING:
                max_score = team_count
                winning_score = ceil(team_count / 2)
                total_max_score = (team_count * (team_count + 1)) // 2
            else:
                total_max_score = bo_type
                max_score = ceil(total_max_score / 2)
                winning_score = max_score

            if Counter(map(int, data["score"].keys())) != Counter(
                [team.id for team in data["teams"]]
            ):
                raise serializers.ValidationError(
                    _("La liste des équipes et celle des scores sont incompatibles.")
                )

            if sum(data["score"].values()) > total_max_score:
                raise serializers.ValidationError(
                    _("Scores invalides, le score total cummulé est trop grand.")
                )

            for score in data["score"].values():
                if score > max_score:
                    raise serializers.ValidationError(_("Le score d'une équipe est trop grand"))

                if score < 0:
                    raise serializers.ValidationError(
                        _("Le score d'une équipe ne peut pas être négatif.")
                    )

                if bo_type == BestofType.RANKING and score <= winning_score:
                    winner_count += 1
                elif bo_type != BestofType.RANKING and score >= winning_score:
                    winner_count += 1

            if (bo_type == BestofType.RANKING and winner_count != ceil(team_count / 2)) or (
                bo_type != BestofType.RANKING and winner_count != 1
            ):
                raise serializers.ValidationError(
                    _("Scores incomplets, il y a trop ou pas assez de gagnants.")
                )

        return data

    def update(self, instance: Match, validated_data: Any) -> Match:
        scores = validated_data.pop("score", {})

        super().update(instance, validated_data)

        assert isinstance(self.instance, Match)
        if self.instance.status == MatchStatus.COMPLETED:
            for team, score in scores.items():
                score_obj = Score.objects.get(team=team, match=instance)
                score_obj.score = score
                score_obj.save()

        return instance


class GroupMatchSerializer(MatchSerializer):
    """Serializer for a group match"""

    class Meta:
        model = GroupMatch
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer[Group]):
    """Serializer for a group in a tournament"""

    teams = serializers.ListField(required=False, source="get_teams_id")
    matchs = GroupMatchSerializer(read_only=True, many=True, source="get_matchs")
    scores = serializers.DictField(read_only=True, source="get_leaderboard")
    tiebreak_scores = serializers.DictField(required=False, source="get_tiebreaks")
    round_count = serializers.IntegerField(read_only=True, source="get_round_count")
    seeding = serializers.DictField(source="get_teams_seeding_by_id")

    class Meta:
        """Meta options for the serializer"""

        model = Group
        fields = "__all__"

    def validate_seeding(self, value: dict[Any, Any]) -> dict[Any, Any]:
        for seed in value.values():
            if not isinstance(seed, int):
                raise serializers.ValidationError(_("Les seeds doivent être des nombres entiers."))

        return value

    def validate_tiebreak_scores(self, value: dict[Any, Any]) -> dict[Any, Any]:
        for tiebreak in value.values():
            if not isinstance(tiebreak, int):
                raise serializers.ValidationError(_("Les scores de tiebreak\
                    doivent être des nombres entiers."))

        return value

    def validate(self, data: Any) -> Any:
        teams: list[int] = data.pop("get_teams_id", [])
        seeding: dict[str, int] = data.pop("get_teams_seeding_by_id", {})
        tiebreak_scores: dict[str, int] = data.pop("get_tiebreaks", {})

        for team in teams:
            if Seeding.objects.filter(team=team).exclude(group=self.instance).exists():
                raise serializers.ValidationError(_(f"L'équipe {Team.objects.get(pk=team).name}\
                    est déjà dans une autre poule."))

        if Counter(map(int, seeding.keys())) != Counter(teams):
            raise serializers.ValidationError(_("Incompatibilité entre\
                la liste des équipes et les équipes du seeding."))

        if Counter(map(int, tiebreak_scores.keys())) != Counter(teams):
            raise serializers.ValidationError(_("Incompatibilité entre\
                la liste des équipes et les équipes des scores de tiebreak."))

        non_zero_seed = list(filter(lambda x: x != 0, seeding.values()))
        if len(set(non_zero_seed)) != len(non_zero_seed):
            raise serializers.ValidationError(_("Les seeds doivent être unique."))

        if max(seeding.values()) > len(teams):
            raise serializers.ValidationError(
                _(f"Le seed maximum ne peut pas être supérieur à {len(teams)}.")
            )

        data["teams"] = teams
        data["seeding"] = { int(k): v for k,v in seeding.items() }
        data["tiebreak_scores"] = { int(k): v for k,v in tiebreak_scores.items() }

        return data

    def update(self, instance: Group, validated_data: Any) -> Group:
        tiebreak_scores: dict[int, int] = validated_data.pop("tiebreak_scores", {})
        seeding: dict[int, int] = validated_data.pop("seeding", {})
        teams = validated_data.pop("teams", [])

        super().update(instance, validated_data)

        for team_id in teams:
            team = Team.objects.get(pk=team_id)
            Seeding.objects.update_or_create(
                team=team, group=instance, defaults={"seeding": seeding[team_id]}
            )
            GroupTiebreakScore.objects.update_or_create(
                team=team, group=instance, defaults={"score": tiebreak_scores[team_id]}
            )

        for old_seed in Seeding.objects.filter(group=instance).exclude(team__in=teams):
            old_seed.delete()

        for old_tiebreak in GroupTiebreakScore.objects.filter(group=instance).exclude(
            team__in=teams,
        ):
            old_tiebreak.delete()

        return instance


class GenerateGroupsSerializer(serializers.Serializer[Any]):
    """Serializer for data used to generate tournament groups"""

    # pylint: disable-next=unsubscriptable-object
    tournament: PrimaryKeyRelatedField[BaseTournament] = PrimaryKeyRelatedField(
        queryset=BaseTournament.objects.all(),
    )
    count = serializers.IntegerField(min_value=1)
    team_per_group = serializers.IntegerField(min_value=2)
    names = serializers.ListField()
    use_seeding = serializers.BooleanField()

    def validate(self, data: Any) -> Any:
        tournament: BaseTournament = data["tournament"]

        if tournament.group_set.exists():
            raise serializers.ValidationError(_("Des poules existent déjà."))

        count: int = data["count"]
        team_per_group: int = data["team_per_group"]
        validated_teams = tournament.get_validated_teams()

        if len(data["names"]) != count:
            raise serializers.ValidationError(
                _(
                    f"Le nombre de noms de poules ({len(data['names'])})\
                    ne correspond pas au nombre de poules demandées ({count})."
                )
            )

        if count * 2 > validated_teams or (count - 1) * team_per_group >= validated_teams:
            raise serializers.ValidationError(
                _(
                    f"{count} poules de {team_per_group} équipes permet d'accueillir\
                    entre {count * 2} et {count * team_per_group} équipes, or il n'y a que\
                    {tournament.get_validated_teams()} équipes inscritent à ce tournoi.\
                    Veuillez revoir le nombre de poules et/ou le nombre d'équipes par poule."
                )
            )

        if count * team_per_group > tournament.get_max_team():
            raise serializers.ValidationError(
                _(
                    f"{count} poules de {team_per_group} équipes permet d'accueillir\
                    {count * team_per_group} équipes au maximum, or il peut y avoir\
                    au plus {tournament.get_max_team()} équipes inscrites.\
                    Veuillez revoir le nombre de poules et/ou le nombre d'équipes par poule."
                )
            )

        return data


class GenerateGroupMatchsSerializer(serializers.Serializer[Any]):
    """Serializer for data used to generate all groups' matchs of a tournament"""

    # pylint: disable-next=unsubscriptable-object
    tournament: PrimaryKeyRelatedField[BaseTournament] = PrimaryKeyRelatedField(
        queryset=BaseTournament.objects.all().prefetch_related("group_set")
    )
    groups = PrimaryKeyRelatedField(
        queryset=Group.objects.all().prefetch_related("groupmatch_set"), many=True
    )
    bo_type = serializers.ChoiceField(BestofType)

    def validate(self, data: Any) -> Any:
        tournament: BaseTournament = data["tournament"]
        groups: list[Group] = data["groups"]

        if not all(tournament.group_set.contains(group) for group in groups):
            raise serializers.ValidationError(
                _(
                    "Certaines poules ne font pas parti de ce tournoi\
                    ou il manque des poules dans la liste."
                )
            )

        for group in groups:
            if group.groupmatch_set.filter(
                status__in=[MatchStatus.ONGOING, MatchStatus.COMPLETED]
            ).exists():
                raise serializers.ValidationError(
                    _(
                        "Impossible de créer les matchs, des matchs existent\
                        déjà et sont en cours ou terminés."
                    )
                )

        return data


class LaunchMatchsSerializer(serializers.Serializer[Any]):
    """Generic serializer for launching matchs"""

    # pylint: disable-next=unsubscriptable-object
    tournament: PrimaryKeyRelatedField[BaseTournament] = PrimaryKeyRelatedField(
        queryset=BaseTournament.objects.all(),
    )
    round = serializers.IntegerField(required=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.match_type = kwargs.pop("type", "")

        self.match_class: Type[GroupMatch] | Type[KnockoutMatch] | Type[SwissMatch]
        if self.match_type == "group":
            self.match_class = GroupMatch
        elif self.match_type == "swiss":
            self.match_class = SwissMatch
        elif self.match_type == "bracket":
            self.match_class = KnockoutMatch

        super().__init__(*args, **kwargs)

        self.fields["matchs"] = PrimaryKeyRelatedField(
            queryset=self.match_class.objects.all(), many=True, required=False
        )

    def validate(self, data: Any) -> Any:
        round_id = data.pop("round", 0)
        matchs = data.pop("matchs", [])
        data["warning"] = False
        tournament = {f"{self.match_type}__tournament": data["tournament"]}

        if round_id:
            if self.match_type == "bracket":
                raise serializers.ValidationError(
                    _("Le lancement de matchs par tour n'est pas supporté pour les arbres.")
                )

            if (
                self.match_class.objects.filter(round_number__lt=round_id, **tournament)
                .exclude(status=MatchStatus.COMPLETED)
                .exists()
            ):
                raise serializers.ValidationError(
                    _(
                        "Des matchs des tours précédents sont\
                        encore en cours ou ne sont pas terminés."
                    )
                )

            scheduled_matchs = self.match_class.objects.filter(
                round_number=round_id, **tournament, status=MatchStatus.SCHEDULED
            )

            if not scheduled_matchs.exists():
                raise serializers.ValidationError(
                    _("Tous les matchs sont déjà en cours ou bien terminés.")
                )

            data["matchs"] = scheduled_matchs
        else:
            data["matchs"] = []

            for match in matchs:
                ongoing_teams_matchs = self.match_class.objects.filter(
                    teams__in=match.teams.all(), status=MatchStatus.ONGOING
                ).exclude(pk=match.pk)

                if not ongoing_teams_matchs.exists() and match.teams.all().exists():
                    data["matchs"].append(match)
                else:
                    data["warning"] = True

        return data


class KnockoutMatchSerializer(MatchSerializer):
    """Serialiser for knockout's match"""

    class Meta:
        model = KnockoutMatch
        fields = "__all__"


class BracketSerializer(serializers.ModelSerializer[Bracket]):
    """Serializer for bracket"""

    teams = serializers.ListField(required=False, source="get_teams_id")
    matchs = KnockoutMatchSerializer(required=False, many=True, source="get_matchs")
    winner = serializers.IntegerField(required=False, source="get_winner")
    depth = serializers.IntegerField(required=False, source="get_depth")
    bo_type = serializers.ChoiceField(BestofType, required=False, write_only=True)

    class Meta:
        model = Bracket
        fields = "__all__"
        extra_kwargs = {"team_count": {"write_only": True}}

    def validate(self, data: Any) -> Any:
        tournament = data["tournament"]
        team_count = data["team_count"]

        if team_count > tournament.get_max_team():
            raise serializers.ValidationError(
                _(
                    "Le nombre d'équipes demandé est supérieur\
                    au nombre maximum d'équipes inscrites dans le tournoi."
                )
            )

        return data


class SwissMatchSerializer(MatchSerializer):
    """Serializer for swiss's match"""

    class Meta:
        model = SwissMatch
        fields = "__all__"


class SwissRoundSerializer(serializers.ModelSerializer[SwissRound]):
    """Serializer for swiss round"""

    teams = serializers.ListField(source="get_teams_id")
    matchs = SwissMatchSerializer(many=True, source="get_matchs")

    class Meta:
        model = SwissRound
        fields = "__all__"


class CreateSwissRoundsSerializer(serializers.Serializer[SwissRound]):
    """Serializer for data used to create a tournament swiss round"""

    # pylint: disable-next=unsubscriptable-object
    tournament: PrimaryKeyRelatedField[BaseTournament] = PrimaryKeyRelatedField(
        queryset=BaseTournament.objects.all(),
    )
    min_score = serializers.IntegerField(min_value=1)
    use_seeding = serializers.BooleanField()
    bo_type = serializers.ChoiceField(BestofType)


class GenerateSwissRoundRoundSerializer(serializers.Serializer[Any]):
    """Serializer for data used to generate a round of matchs of a swiss round"""

    # pylint: disable-next=unsubscriptable-object
    tournament: PrimaryKeyRelatedField[BaseTournament] = PrimaryKeyRelatedField(
        queryset=BaseTournament.objects.all(),
    )
    swiss = PrimaryKeyRelatedField(queryset=SwissRound.objects.all())
    round = serializers.IntegerField(min_value=2)

    def validate(self, data: Any) -> Any:
        tournament = data["tournament"]
        swiss = data["swiss"]
        round_idx = data["round"]

        if not tournament.swissround_set.contains(swiss):
            raise serializers.ValidationError(
                _("La ronde suisse ne fait pas partie de ce tournoi.")
            )

        if round_idx > 2 * swiss.min_score - 1:
            raise serializers.ValidationError(
                _("Le tour demandé ne fait pas partie de cette ronde suisse.")
            )

        if (
            SwissMatch.objects.filter(swiss=swiss, round_number=round_idx)
            .exclude(status=MatchStatus.SCHEDULED)
            .exists()
        ):
            raise serializers.ValidationError(
                _("Des matchs existent déjà et sont en cours ou terminés.")
            )

        if (
            SwissMatch.objects.filter(swiss=swiss, round_number=round_idx - 1)
            .exclude(status=MatchStatus.COMPLETED)
            .exists()
        ):
            raise serializers.ValidationError(
                _(
                    "Des matchs du tour précédant n'ont pas encore\
                    commencés ou ne sont pas terminés."
                )
            )

        return data


class CasterSerializer(serializers.ModelSerializer[Caster]):
    """Serializer for a tournament Caster"""

    class Meta:
        """Meta options for the serializer"""

        model = Caster
        exclude = ["tournament"]


class EventSerializer(serializers.ModelSerializer[Event]):
    """Serializer for the tournament Event"""

    tournaments = serializers.ListField(required=False, read_only=True, source="get_tournaments_id")

    class Meta:
        """Serializer meta options"""

        model = Event
        read_only_fields = ("id",)
        fields = [
            "id",
            "name",
            "description",
            "date_start",
            "date_end",
            "ongoing",
            "tournaments",
            "logo",
            "poster",
            "planning_file",
        ]


class GameSerializer(serializers.ModelSerializer[Game]):
    """Serializer for the tournament Games"""

    class Meta:
        """Meta options of the serializer"""

        model = Game
        read_only_fields = ("id",)
        fields = (
            "id",
            "name",
            "short_name",
            "players_per_team",
            "substitute_players_per_team",
            "team_per_match",
        )

class EventTournamentSerializer(serializers.ModelSerializer[EventTournament]):
    """Serializer class for Tournaments"""

    teams = serializers.ListField(required=False, read_only=True, source="get_teams_id")
    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    casters = CasterSerializer(many=True, source="get_casters")
    groups = serializers.ListField(required=False, source="get_groups_id")
    brackets = serializers.ListField(required=False, source="get_brackets_id")
    swissRounds = serializers.ListField(required=False, source="get_swiss_rounds_id")

    class Meta:
        """Meta options of the serializer"""

        model = EventTournament
        read_only_fields = (
            "id",
            "manager_price_online",
            "manager_price_onsite",
            "player_price_online",
            "player_price_onsite",
            "substitute_price_online",
            "substitute_price_onsite",
        )
        exclude = ["polymorphic_ctype"]

    def to_representation(self, instance: EventTournament) -> Any:
        """Remove all fields except id and is_announced when is_announced is False"""
        ret = super().to_representation(instance)
        if ret["is_announced"]:
            return ret
        return {"id": ret["id"], "is_announced": False}


class BaseTournamentSerializer(serializers.ModelSerializer[BaseTournament]):
    """Serializer class for Tournaments"""

    teams = serializers.ListField(required=False, read_only=True, source="get_teams_id")
    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    groups = serializers.ListField(required=False, source="get_groups_id")
    brackets = serializers.ListField(required=False, source="get_brackets_id")
    swissRounds = serializers.ListField(required=False, source="get_swiss_rounds_id")

    class Meta:
        """Meta options of the serializer"""

        model = BaseTournament
        read_only_fields = (
            "id",
            "manager_price_online",
            "manager_price_onsite",
            "player_price_online",
            "player_price_onsite",
            "substitute_price_online",
            "substitute_price_onsite",
        )
        exclude = ["polymorphic_ctype"]

    def to_representation(self, instance: BaseTournament) -> Any:
        """Remove all fields except id and is_announced when is_announced is False"""
        ret = super().to_representation(instance)
        if "is_announced" in ret and not ret["is_announced"]:
            return {"id": ret["id"], "is_announced": False}
        return ret


class TeamSerializer(serializers.ModelSerializer[Team]):
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
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def validate(self, data: Any) -> Any:
        if not tournament_announced(data["tournament"]):
            raise serializers.ValidationError(_("Ce tournoi n'est pas encore annoncé"))
        if tournament_registration_full(data["tournament"]):
            raise serializers.ValidationError(_("Ce tournoi est complet"))
        if ("password" in data and
            not private_tournament_password_matching(data["tournament"], data["password"])):
            raise serializers.ValidationError(
                _("Le mot de passe ne correspond pas au mot de passe du tournoi")
            )
        for user in (
            data.get("get_players_id", [])
            + data.get("get_managers_id", [])
            + data.get("get_substitutes_id", [])
        ):
            tournament = BaseTournament.objects.get(id=data["tournament"].id)
            if isinstance(tournament, EventTournament):
                event = Event.objects.get(eventtournament=data["tournament"])
                if not unique_event_registration_validator(user, event):
                    raise serializers.ValidationError(
                        _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
                    )

        if len(data.get("players_names_in_game", [])) != len(data.get("get_players_id", [])):
            raise serializers.ValidationError(_("Il manque des name_in_games de joueur⋅euses"))

        if len(data.get("substitutes_names_in_game", [])) != len(
            data.get("get_substitutes_id", [])
        ):
            raise serializers.ValidationError(_("Il manque des name_in_games de remplaçant⋅e⋅s"))

        # prevent payloard injection
        data["_validated_players"] = []
        data["_validated_substitutes"] = []

        # Validate the name in game
        for name in data.get("players_names_in_game", []):
            info = valid_name(data["tournament"].game, name)
            if info is None:
                raise serializers.ValidationError(_("Le pseudo en jeu n'est pas valide"))
            data["_validated_players"].append(info)
        for name in data.get("substitutes_names_in_game", []):
            info = valid_name(data["tournament"].game, name)
            if info is None:
                raise serializers.ValidationError(_("Le pseudo en jeu n'est pas valide"))
            data["_validated_substitutes"].append(info)

        return data

    def create(self, validated_data: Any) -> Team:
        """Create a Team from input data"""

        # Catch the players and managers keywords
        players = validated_data.pop("get_players_id", [])
        managers = validated_data.pop("get_managers_id", [])
        substitutes = validated_data.pop("get_substitutes_id", [])
        players_names_in_game = validated_data.pop("players_names_in_game", [])
        substitutes_names_in_game = validated_data.pop("substitutes_names_in_game", [])
        data_players = validated_data.pop("_validated_players", [])
        data_substitutes = validated_data.pop("_validated_substitutes", [])

        validated_data["password"] = make_password(validated_data.get("password", ""))
        team_obj = Team.objects.create(**validated_data)

        for player, name_in_game, data in zip(players, players_names_in_game, data_players):
            user_obj = User.objects.get(id=player)
            Player.objects.create(
                user=user_obj, team=team_obj, name_in_game=name_in_game, validator_data=data
            )

        for manager in managers:
            user_obj = User.objects.get(id=manager)
            Manager.objects.create(user=user_obj, team=team_obj)

        for sub, name_in_game, data in zip(
            substitutes, substitutes_names_in_game, data_substitutes
        ):
            user_obj = User.objects.get(id=sub)
            Substitute.objects.create(
                user=user_obj, team=team_obj, name_in_game=name_in_game, validator_data=data
            )

        return team_obj

    def update(self, instance: Team, validated_data: Any) -> Team:
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


class TeamMatchsSerializer(serializers.ModelSerializer[Team]):
    """Serializer for team matchs"""

    group_matchs = GroupMatchSerializer(many=True, source="get_group_matchs")
    bracket_matchs = KnockoutMatchSerializer(many=True, source="get_knockout_matchs")
    swiss_matchs = SwissMatchSerializer(many=True, source="get_swiss_matchs")

    class Meta:
        model = Team
        fields = ["id", "group_matchs", "bracket_matchs", "swiss_matchs"]


class PlayerSerializer(serializers.ModelSerializer[Player]):
    """Serializer for a Player Registration"""

    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = "__all__"

    def validate(self, data: Any) -> Any:
        if isinstance(data["team"].tournament, EventTournament):
            event = data["team"].tournament.event
            if not unique_event_registration_validator(data["user"], event):
                raise serializers.ValidationError(
                    _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
                )
        if "password" in data:
            del data["password"]
        if max_players_per_team_reached(data["team"]):
            raise serializers.ValidationError(
                _("Nombre maximum de joueur⋅euse⋅s par équipe atteint")
            )
        if not tournament_announced(data["team"].tournament):
            raise serializers.ValidationError(_("Ce tournoi n'est pas encore annoncé"))

        # prevent payload injection
        data["validator_data"] = {}

        info = valid_name(data["team"].tournament.game, data["name_in_game"])
        if info is None:
            raise serializers.ValidationError(_("Le pseudo en jeu n'est pas valide"))
        data["validator_data"] = info

        return data


class PlayerIdSerializer(serializers.Serializer[Player]):
    """Serializer to verify a list of player IDs"""

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = "__all__"

    def to_representation(self, instance: Player) -> int:
        """Turn a Django object into a serialized representation"""
        return instance.id


class ManagerSerializer(serializers.ModelSerializer[Manager]):
    """Serializer for a Manager Registration"""

    password = serializers.CharField(write_only=True)

    class Meta:
        """Meta options for the serializer"""

        model = Manager
        fields = "__all__"

    def validate(self, data: Any) -> Any:
        event = data["team"].tournament.event
        if not unique_event_registration_validator(data["user"], event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        del data["password"]
        if not tournament_announced(data["team"].tournament):
            raise serializers.ValidationError(_("Ce tournoi n'est pas encore annoncé"))

        return data


class ManagerIdSerializer(serializers.ModelSerializer[Manager]):
    """Serializer to verify a list of manager IDs"""

    class Meta:
        """Meta options for the serializer"""

        model = Manager
        fields = "__all__"

    def to_representation(self, instance: Manager) -> int:
        """Turn a Django object into a serialized representation"""
        return instance.id


class SubstituteSerializer(serializers.ModelSerializer[Substitute]):
    """Serializer for a Substitute Registration"""

    password = serializers.CharField(write_only=True)

    class Meta:
        """Meta options for the serializer"""

        model = Substitute
        fields = "__all__"

    def validate(self, data: Any) -> Any:
        event = data["team"].tournament.event
        if not unique_event_registration_validator(data["user"], event):
            raise serializers.ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        del data["password"]
        if not tournament_announced(data["team"].tournament):
            raise serializers.ValidationError(_("Ce tournoi n'est pas encore annoncé"))
        if max_substitue_per_team_reached(data["team"]):
            raise serializers.ValidationError(
                _("Nombre maximum de remplaçant⋅e⋅s par équipe atteint")
            )

        # prevent payload injection
        data["validator_data"] = {}

        info = valid_name(data["team"].tournament.game, data["name_in_game"])
        if info is None:
            raise serializers.ValidationError(_("Le pseudo en jeu n'est pas valide"))
        data["validator_data"] = info

        return data


class SubstituteIdSerializer(serializers.ModelSerializer[Substitute]):
    """Serializer to verify a list of Substitute IDs"""

    class Meta:
        """Meta options for the serializer"""

        model = Substitute
        fields = "__all__"

    def to_representation(self, instance: Substitute) -> int:
        """Turn a Django object into a serialized representation"""
        return instance.id


class SeatSlotSerializer(serializers.ModelSerializer[SeatSlot]):
    """Serializer for a SeatSlot"""

    class Meta:
        """Meta options for the serializer"""

        model = SeatSlot
        fields = "__all__"


class SeatSerializer(serializers.ModelSerializer[Seat]):
    """Serializer for a Seat"""

    class Meta:
        """Meta options for the serializer"""

        model = Seat
        fields = "__all__"


class FullDerefSwissMatchSerializer(serializers.ModelSerializer[SwissMatch]):
    """Serializer for a Swiss Match in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = SwissMatch
        fields = "__all__"


class FullDerefSwissRoundSerializer(serializers.ModelSerializer[SwissRound]):
    """Serializer for a Swiss Round in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = SwissRound
        fields = "__all__"


class FullDerefKnockoutMatchSerializer(serializers.ModelSerializer[KnockoutMatch]):
    """Serializer for a knockout match in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = KnockoutMatch
        fields = "__all__"


class FullDerefBracketSerializer(serializers.ModelSerializer[Bracket]):
    """Serializer for a bracket in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = Bracket
        fields = "__all__"


class FullDerefGroupMatchSerializer(serializers.ModelSerializer[GroupMatch]):
    """Serializer for a group match in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = GroupMatch
        fields = "__all__"


class FullDerefGroupSerializer(serializers.ModelSerializer[Group]):
    """Serializer for a group in a tournament"""

    class Meta:
        """Meta options for the serializer"""

        model = Group
        fields = "__all__"


class FullDerefPlayerSerializer(serializers.ModelSerializer[Player]):
    """Serializer for a Player Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Player
        fields = ("id", "name_in_game", "payment_status")


class FullDerefManagerSerializer(serializers.ModelSerializer[Manager]):
    """Serializer for a Manager Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Manager

    def to_representation(self, instance: Manager) -> str:
        """Remove all fields except id and is_announced when is_announced is False"""
        return instance.user.username


class FullDerefSubstituteSerializer(serializers.ModelSerializer[Substitute]):
    """Serializer for a Substitute Registration"""

    class Meta:
        """Meta options for the serializer"""

        model = Substitute
        fields = ("id", "name_in_game", "payment_status")


class FullDerefTeamSerializer(serializers.ModelSerializer[Team]):
    """Serializer class for Teams"""

    class Meta:
        """Meta options of the team serializer"""

        model = Team
        read_only_fields = ("id",)
        fields = ("id", "name", "validated", "captain")


class FullDerefTeamSerializer2(serializers.ModelSerializer[Team]):
    """Serializer class for Teams"""

    players = FullDerefPlayerSerializer(many=True, source="player_set")
    substitutes = FullDerefSubstituteSerializer(many=True, source="substitute_set")
    managers = FullDerefManagerSerializer(many=True, source="manager_set", read_only=True)
    # pylint: disable-next=unsubscriptable-object
    captain: SlugRelatedField[Player] = SlugRelatedField(slug_field="name_in_game", read_only=True)

    class Meta:
        """Meta options of the team serializer"""

        model = Team
        read_only_fields = ("id",)
        exclude = ["tournament", "password"]


class GroupField(serializers.ModelSerializer[Group]):
    """Serializer for a group in a tournament"""

    teams = serializers.ListField(required=False, source="get_teams_id")
    matchs = GroupMatchSerializer(many=True, source="get_matchs")
    scores = serializers.DictField(required=False, source="get_leaderboard")
    tiebreak_scores = serializers.DictField(required=False, source="get_tiebreaks")
    round_count = serializers.IntegerField(source="get_round_count")
    seeding = serializers.DictField(source="get_teams_seeding_by_id")

    class Meta:
        """Meta options for the serializer"""

        model = Group
        exclude = ["tournament"]


class BracketField(serializers.ModelSerializer[Bracket]):
    """Serializer for a bracket when used as a field in another serializer"""

    teams = serializers.ListField(source="get_teams_id")
    matchs = KnockoutMatchSerializer(many=True, source="get_matchs")
    winner = serializers.IntegerField(source="get_winner")
    depth = serializers.IntegerField(required=False, source="get_depth")

    class Meta:
        model = Bracket
        exclude = ["team_count", "tournament"]


class SwissRoundField(serializers.ModelSerializer[SwissRound]):
    """Serializer for a swiss round when used as a field in another serializer"""

    teams = serializers.ListField(source="get_teams_id")
    matchs = SwissMatchSerializer(many=True, source="get_matchs")

    class Meta:
        model = SwissRound
        exclude = ["tournament"]


# pylint: disable-next=unsubscriptable-object
class FullDerefEventSeatField(serializers.RelatedField[Seat, Any, tuple[int, int]]):
    """Serializer for an event's seat when used as a field in another serializer"""

    def to_representation(self, instance: Seat) -> tuple[int, int]:
        return instance.x, instance.y


class FullDerefSeatSerializer(serializers.ModelSerializer[Seat]):
    """Serializer for a Seat"""

    class Meta:
        """Meta options for the serializer"""

        model = Seat
        exclude = ["event"]


class FullDerefSeatSlotSerializer(serializers.ModelSerializer[SeatSlot]):
    """Serializer for a SeatSlot"""

    seats = FullDerefSeatSerializer(many=True)

    class Meta:
        """Meta options for the serializer"""

        model = SeatSlot
        exclude = ["tournament"]


class FullDerefEventSerializer(serializers.ModelSerializer[Event]):
    """Serializer for an Event with all fields"""

    seats = FullDerefEventSeatField(many=True, source="seat_set", read_only=True)

    class Meta:
        model = Event
        fields = "__all__"


class FullDerefEventTournamentSerializer(serializers.ModelSerializer[EventTournament]):
    """Serializer for a Tournament with all fields serialized"""

    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    casters = CasterSerializer(many=True, source="get_casters")
    teams = FullDerefTeamSerializer2(many=True)
    groups = GroupField(many=True, source="group_set")
    brackets = BracketField(many=True, source="bracket_set")
    swissRounds = SwissRoundField(many=True, source="swissround_set")
    event = FullDerefEventSerializer()
    game = GameSerializer()
    seatslots = FullDerefSeatSlotSerializer(many=True, source="seatslot_set")

    class Meta:
        model = EventTournament
        exclude = ["polymorphic_ctype"]

    def to_representation(self, value: EventTournament) -> Any:
        if value.is_announced:
            return super().to_representation(value)
        return {"id": value.id, "is_announced": False}


class PrivateTournamentSerializer(serializers.ModelSerializer[PrivateTournament]):
    """Serializer for the tournament PrivateTournament"""

    validated_teams = serializers.IntegerField(read_only=True, source="get_validated_teams")
    teams = FullDerefTeamSerializer2(many=True)
    groups = GroupField(many=True, source="group_set")
    brackets = BracketField(many=True, source="bracket_set")
    swissRounds = SwissRoundField(many=True, source="swissround_set")
    game = GameSerializer()
    password = serializers.BooleanField(read_only=True)

    class Meta:
        """Meta options of the serializer"""

        model = PrivateTournament
        read_only_fields = (
            "id",
        )
        exclude = ["polymorphic_ctype"]


class TeamSeedListSerializer(serializers.ListSerializer[Any]):
    """Serializer for updating multiple teams' seed"""

    child: TeamSeedingSerializer  # pylint: disable=used-before-assignment

    def update(self, teams: QuerySet[Team], validated_data: Any) -> list[Team]:
        data_mapping = {item["id"]: item for item in validated_data}

        ret = []
        for team_id, seed in data_mapping.items():
            try:
                team = teams.get(id=team_id)
                ret.append(self.child.update(team, seed))
            except Exception as exception:  # pylint: disable=broad-exception-caught
                print(exception, file=sys.stderr)

        return ret


class TeamSeedingSerializer(serializers.ModelSerializer[Team]):
    """Serializer for updating team's seed"""

    id = serializers.IntegerField()

    class Meta:
        model = Team
        fields = ["id", "seed"]
        list_serializer_class = TeamSeedListSerializer
