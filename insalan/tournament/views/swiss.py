from typing import Any

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
    generate_swiss_round_round,
    launch_match,
    update_match_score,
)
from ..models import MatchStatus, BaseTournament, SwissMatch, SwissRound, validate_match_data
from ..models.game_processor import get_processor


# pylint: disable-next=unsubscriptable-object
class SwissRoundsDetails(generics.DestroyAPIView[SwissRound]):
    queryset = SwissRound.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        swiss = self.get_object()

        if SwissMatch.objects.filter(swiss=swiss).exclude(
            status=MatchStatus.SCHEDULED,
        ).exists():
            return Response({
                "error": _("Impossible de supprimer les rondes suisses.\
                    Des matchs sont en cours ou déjà terminés.")
            }, status=status.HTTP_400_BAD_REQUEST)

        swiss.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SwissMatchsLaunch(generics.UpdateAPIView[SwissMatch]):  # pylint: disable=unsubscriptable-object
    serializer_class = serializers.LaunchMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = self.get_serializer(data=request.data, type="swiss", many=True)
        data.is_valid(raise_exception=True)

        matchs = []

        for swiss in data.validated_data:
            for match in swiss["matchs"]:
                launch_match(match)
                matchs.append(match.id)

        return Response({
            "matchs": matchs, "warning": any(s["warning"] for s in data.validated_data)
        }, status=status.HTTP_200_OK)


# pylint: disable-next=unsubscriptable-object
class SwissFillRound(generics.UpdateAPIView[SwissRound]):
    queryset = SwissRound.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.SwissFillRoundSerializer

    # pylint: disable-next=arguments-differ
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        request.data["swiss"] = self.kwargs["pk"]

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


class SwissMatchResult(generics.GenericAPIView[SwissMatch]):  # pylint: disable=unsubscriptable-object
    """Process match result from external API callback (e.g., Riot Games)"""

    queryset = SwissMatch.objects.all().order_by("id")
    serializer_class = serializers.SwissMatchSerializer
    permission_classes = [permissions.AllowAny]  # Allow external API callbacks
    lookup_url_kwarg = "match_id"

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description=_("Payload from external API callback")
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "status": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Status message")
                    )
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "err": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description=_("Match not found")
                    )
                }
            ),
        },
    )
    def post(self, request: Request, swiss_id: int, match_id: int) -> Response:
        """Process the result payload from an external API"""
        try:
            match = SwissMatch.objects.get(id=match_id, swiss_id=swiss_id)
        except SwissMatch.DoesNotExist:
            return Response(
                {"err": _("Match introuvable")},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the game processor for this match's tournament
        tournament = match.swiss.tournament
        game = tournament.game
        processor_class = get_processor(game.game_processor)

        if processor_class is None:
            return Response(
                {"err": _("Aucun processeur de jeu configuré")},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process the result using the game processor
        payload = request.data
        result_data = processor_class.process_result_match(match, payload)

        if result_data is not None:
            match.api_data = result_data
            match.save(update_fields=["api_data"])

            return Response(
                {"status": _("Résultat traité avec succès")},
                status=status.HTTP_200_OK
            )

        return Response(
            {"err": _("Échec du traitement du résultat")},
            status=status.HTTP_400_BAD_REQUEST
        )
