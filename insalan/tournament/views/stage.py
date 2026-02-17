from typing import Any

from rest_framework import generics, permissions, status
from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.request import Request

from insalan.tournament import serializers

from ..manage import (
    generate_groups,
    create_empty_knockout_matchs,
    create_empty_swiss_matchs,
    auto_fill_first_round
)
from ..models import Bracket, BestofType, Group, Stage, SwissRound
from ..serializers import StageSerializer

# pylint: disable-next=unsubscriptable-object
class CreateStage(CreateAPIView[Stage]):
    """Create new tournament stage"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    permission_classes = [IsAdminUser]

# pylint: disable-next=unsubscriptable-object
class UpdateStage(UpdateAPIView[Stage]):
    """Update tournament stage"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    permission_classes = [IsAdminUser]

# pylint: disable-next=unsubscriptable-object
class DeleteStage(DestroyAPIView[Stage]):
    """Delete tournament stage"""

    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    permission_classes = [IsAdminUser]

# pylint: disable-next=unsubscriptable-object
class StageAddGroups(generics.CreateAPIView[Stage]):
    queryset = Stage.objects.all()
    serializer_class = serializers.GroupsCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        stage = self.get_object()
        request.data["tournament"] = stage.tournament.id

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        auto_fill = data.validated_data.pop("auto_fill")
        if auto_fill:
            generate_groups(**data.validated_data, stage=stage)
        else:
            for i in range(data.validated_data["count"]):
                Group.objects.create(
                    tournament=data.validated_data["tournament"],
                    name=data.validated_data["names"][i],
                    round_count=data.validated_data["round_count"],
                    stage=stage
                )

        serialized_data = serializers.GroupField(
            data.validated_data["tournament"].group_set.all(),
            many=True
        ).data

        return Response(serialized_data, status=status.HTTP_201_CREATED)


# pylint: disable=unsubscriptable-object
class StageAddBracket(generics.CreateAPIView[Stage]):
    queryset = Stage.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.BracketSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        stage = self.get_object()
        request.data["tournament"] = stage.tournament.id

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        bo_type = data.validated_data.pop("bo_type", BestofType.BO1)
        play_all = data.validated_data.pop("play_all", False)

        bracket = Bracket.objects.create(**data.validated_data, stage=stage)

        create_empty_knockout_matchs(bracket, bo_type, play_all)

        return Response(serializers.BracketField(bracket).data, status=status.HTTP_201_CREATED)


# pylint: disable-next=unsubscriptable-object
class StageAddSwissRounds(generics.CreateAPIView[Stage]):
    queryset = Stage.objects.all()
    serializer_class = serializers.CreateSwissRoundsSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        stage = self.get_object()
        request.data["tournament"] = stage.tournament.id

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        validated_data = data.validated_data

        swiss = SwissRound.objects.create(
            tournament=validated_data["tournament"],
            name=validated_data["name"],
            min_score=validated_data["min_score"],
            stage=stage,
            round_count=validated_data["round_count"]
        )

        create_empty_swiss_matchs(
            swiss,
            validated_data["team_count"],
            validated_data["bo_type"],
            validated_data["play_all"]
        )

        if validated_data["auto_fill"]:
            auto_fill_first_round(
                validated_data["tournament"],
                validated_data["use_seeding"],
                swiss,
                validated_data["team_count"]
            )

        serialized_data = serializers.SwissRoundField(
            data.validated_data["tournament"].swissround_set.all(),
            many=True,
        ).data

        return Response(serialized_data, status=status.HTTP_201_CREATED)
