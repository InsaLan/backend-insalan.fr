from typing import Any

from django.core.exceptions import BadRequest
from django.utils.translation import gettext_lazy as _

from drf_yasg.utils import swagger_auto_schema  # type: ignore[import]
from drf_yasg import openapi  # type: ignore[import]

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from insalan.tournament import serializers
from insalan.user.models import User

from ..manage import (
    create_swiss_rounds,
    generate_swiss_round_round,
    launch_match,
    update_match_score,
)
from ..models import MatchStatus, BaseTournament, SwissMatch, validate_match_data


# pylint: disable-next=unsubscriptable-object
class CreateSwissRounds(generics.CreateAPIView[BaseTournament]):
    queryset = BaseTournament.objects.all()
    serializer_class = serializers.CreateSwissRoundsSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pk: int = self.kwargs["pk"]
        request.data["tournament"] = pk

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        create_swiss_rounds(**data.validated_data)

        serialized_data = serializers.SwissRoundField(
            data.validated_data["tournament"].swissround_set.all(),
            many=True,
        ).data

        return Response(serialized_data, status=status.HTTP_201_CREATED)


# pylint: disable-next=unsubscriptable-object
class DeleteSwissRounds(generics.DestroyAPIView[BaseTournament]):
    queryset = BaseTournament.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        tournament = self.get_object()

        if SwissMatch.objects.filter(swiss__tournament=tournament).exclude(
            status=MatchStatus.SCHEDULED,
        ).exists():
            return Response({
                "error": _("Impossible de supprimer les rondes suisses.\
                    Des matchs sont en cours ou déjà terminés.")
            }, status=status.HTTP_400_BAD_REQUEST)

        tournament.swissround_set.all().delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SwissMatchsLaunch(generics.UpdateAPIView[Any]):  # pylint: disable=unsubscriptable-object
    serializer_class = serializers.LaunchMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if kwargs["pk"] != request.data["tournament"]:
            raise BadRequest()

        data = self.get_serializer(data=request.data, type="swiss")
        data.is_valid(raise_exception=True)

        matchs = []

        for match in data.validated_data["matchs"]:
            launch_match(match)
            matchs.append(match.id)

        return Response({
            "matchs": matchs, "warning": data.validated_data["warning"]
        }, status=status.HTTP_200_OK)


# pylint: disable-next=unsubscriptable-object
class GenerateSwissRoundRound(generics.UpdateAPIView[BaseTournament]):
    queryset = BaseTournament.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.GenerateSwissRoundRoundSerializer

    # pylint: disable-next=arguments-differ
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pk: int = self.kwargs["pk"]
        request.data["tournament"] = pk

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        updated_matchs = generate_swiss_round_round(data.validated_data["swiss"],
                                                    data.validated_data["round"])

        updated_matchs_serialized = serializers.SwissMatchSerializer(updated_matchs, many=True)

        return Response(
            {m["id"]: m for m in updated_matchs_serialized.data},
            status=status.HTTP_200_OK,
        )


class SwissMatchPatch(generics.UpdateAPIView[SwissMatch]):  # pylint: disable=unsubscriptable-object
    queryset = SwissMatch.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.SwissMatchSerializer
    lookup_url_kwarg = "match_id"


# pylint: disable-next=unsubscriptable-object
class SwissMatchScore(generics.GenericAPIView[SwissMatch]):
    """Update score of a swiss match"""

    queryset = SwissMatch.objects.all().order_by("id")
    serializer_class = serializers.SwissMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "score": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description=_("Score du match")
                ),
            },
        ),
        responses={
            200: serializer_class,
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "team1_score": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Score de l'équipe 1")
                    ),
                    "team2_score": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Score de l'équipe 2")
                    ),
                }
            ),
            403: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Vous n'êtes pas autorisé à modifier ce match")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Match introuvable")
                    )
                }
            )
        }
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        data = request.data

        try:
            match = SwissMatch.objects.get(pk=kwargs["match_id"],swiss=kwargs["swiss_id"])
        except SwissMatch.DoesNotExist as e:
            raise NotFound() from e

        assert isinstance(user, User), 'User must be authenticated to access this route.'
        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if match.status != MatchStatus.ONGOING:
            return Response({"status" : "Le match n'est pas en cours"},
                            status = status.HTTP_400_BAD_REQUEST)

        error_response = validate_match_data(match, data)
        if error_response is not None:
            return Response({k: _(v) for k, v in error_response.items()},
                            status=status.HTTP_400_BAD_REQUEST)

        update_match_score(match,data)

        serializer = serializers.SwissMatchSerializer(match, context={"request": request})

        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )
