from typing import Any

from django.utils.translation import gettext_lazy as _

from drf_yasg.utils import swagger_auto_schema  # type: ignore[import]
from drf_yasg import openapi  # type: ignore[import]

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied

from insalan.tournament import serializers
from insalan.user.models import User

from ..models import Group, validate_match_data, GroupMatch, MatchStatus
from ..manage import update_match_score, create_group_matchs, launch_match
from ..models.game_processor import get_processor

from .permissions import ReadOnly


class GroupList(generics.ListCreateAPIView[Group]):  # pylint: disable=unsubscriptable-object
    queryset = Group.objects.all().order_by("id")
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data

        multiple = isinstance(data, list)

        groups = self.get_serializer(self.get_queryset(), data=request.data, many=multiple)

        groups.is_valid(raise_exception=True)

        saved_groups = groups.save()

        return Response(self.get_serializer(saved_groups, many=multiple).data,
                        status=status.HTTP_201_CREATED)


# pylint: disable-next=unsubscriptable-object
class GroupDetails(generics.RetrieveUpdateDestroyAPIView[Group]):
    queryset = Group.objects.all().order_by("id")
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        group = self.get_object()

        if GroupMatch.objects.filter(group=group).exclude(status=MatchStatus.SCHEDULED).exists():
            return Response({
                "error": _("Impossible de supprimer la poule.\
                    Des matchs sont déjà en cours ou terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        group.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# pylint: disable-next=unsubscriptable-object
class GroupsDelete(generics.GenericAPIView[Group]):
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        groups = request.data

        if (GroupMatch
            .objects
            .filter(group__in=groups)
            .exclude(status=MatchStatus.SCHEDULED)
            .exists()
        ):
            return Response({
                # pylint: disable-next=line-too-long
                "error": _("Impossible de supprimer les poules. Des matchs sont en cours ou déjà terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        Group.objects.filter(id__in=groups).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# pylint: disable-next=unsubscriptable-object
class GroupsMatchsCreate(generics.CreateAPIView[Any]):
    serializer_class = serializers.GroupsMatchsCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        for group in data.validated_data["groups"]:
            create_group_matchs(
                group,
                data.validated_data["bo_type"],
                data.validated_data["play_all"]
            )

        tournament = data.validated_data["groups"][0].tournament
        groups = serializers.GroupField(
            tournament.group_set.all(),
            many=True
        ).data

        return Response(groups, status=status.HTTP_201_CREATED)


# pylint: disable-next=unsubscriptable-object
class GroupsMatchsDelete(generics.GenericAPIView[Group]):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        groups = request.data
        matchs = GroupMatch.objects.filter(group__in=groups)

        if matchs.exclude(status=MatchStatus.SCHEDULED).exists():
            return Response({
                # pylint: disable-next=line-too-long
                "error": _("Impossible de supprimer les matchs. Des matchs sont déjà en cours ou terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        matchs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupsMatchsLaunch(generics.UpdateAPIView[Any]): # pylint: disable=unsubscriptable-object
    serializer_class = serializers.LaunchMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = self.get_serializer(data=request.data, type="group", many=True)
        data.is_valid(raise_exception=True)

        matchs = []

        for group in data.validated_data:
            for match in group["matchs"]:
                launch_match(match)
                matchs.append(match.id)

        return Response(
            {
                "matchs": matchs,
                "warning": any(g["warning"] for g in data.validated_data)
            },
            status=status.HTTP_200_OK
        )


class GroupMatchPatch(generics.UpdateAPIView[GroupMatch]):  # pylint: disable=unsubscriptable-object
    queryset = GroupMatch.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.GroupMatchSerializer
    lookup_url_kwarg = "match_id"


class GroupMatchScore(generics.UpdateAPIView[GroupMatch]):  # pylint: disable=unsubscriptable-object
    """Update score of a group match"""

    queryset = GroupMatch.objects.all().order_by("id")
    serializer_class = serializers.GroupMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    # The decorator is missing types stubs.
    @swagger_auto_schema(  # type: ignore[misc]
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "team1_score": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("Score de l'équipe 1")
                ),
                "team2_score": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=_("Score de l'équipe 2")
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
            match = GroupMatch.objects.get(pk=kwargs["match_id"],group=kwargs["group_id"])
        except GroupMatch.DoesNotExist as e:
            raise NotFound() from e

        assert isinstance(user, User), 'User must be authenticated to access this route.'
        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if match.status != MatchStatus.ONGOING:
            return Response({"status" : "Le match n'est pas en cours"},
                            status=status.HTTP_400_BAD_REQUEST)

        error_response = validate_match_data(match, data)
        if error_response is not None:
            return Response({k: _(v) for k,v in error_response.items()},
                            status=status.HTTP_400_BAD_REQUEST)

        update_match_score(match,data)

        serializer = serializers.GroupMatchSerializer(match, context={"request": request})

        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )


class GroupMatchResult(generics.GenericAPIView[GroupMatch]):  # pylint: disable=unsubscriptable-object
    """Process match result from external API callback (e.g., Riot Games)"""

    queryset = GroupMatch.objects.all().order_by("id")
    serializer_class = serializers.GroupMatchSerializer
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
    def post(self, request: Request, group_id: int, match_id: int) -> Response:
        """Process the result payload from an external API"""
        try:
            match = GroupMatch.objects.get(id=match_id, group_id=group_id)
        except GroupMatch.DoesNotExist:
            return Response(
                {"err": _("Match introuvable")},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the game processor for this match's tournament
        tournament = match.group.tournament
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
