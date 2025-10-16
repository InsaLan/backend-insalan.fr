from django.utils.translation import gettext_lazy as _
from django.core.exceptions import BadRequest

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insalan.tournament import serializers

from ..models import Group, validate_match_data, GroupMatch, MatchStatus, BaseTournament, Match
from ..manage import update_match_score, generate_groups, create_group_matchs, launch_match

from .permissions import ReadOnly

class GroupList(generics.ListCreateAPIView):
    queryset = Group.objects.all().order_by("id")
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAdminUser | ReadOnly]

    def post(self, request, *args, **kwargs):
        data = request.data

        multiple = isinstance(data, list)

        groups = self.get_serializer(self.get_queryset(), data=request.data, many=multiple)

        groups.is_valid(raise_exception=True)

        saved_groups = groups.save()

        return Response(self.get_serializer(saved_groups, many=multiple).data,
                        status=status.HTTP_201_CREATED)

class GroupDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all().order_by("id")
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        group = self.get_object()

        if GroupMatch.objects.filter(group=group).exclude(status=MatchStatus.SCHEDULED).exists():
            return Response({
                "error": _("Impossible de supprimer la poule.\
                    Des matchs sont déjà en cours ou terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        group.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class GenerateGroups(generics.CreateAPIView):
    serializer_class = serializers.GenerateGroupsSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        if kwargs["pk"] != request.data["tournament"]:
            raise BadRequest()

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        generate_groups(**data.validated_data)

        serialized_data = serializers.GroupField(data.validated_data["tournament"].group_set.all(),
                                                 many=True).data

        return Response(serialized_data, status=status.HTTP_201_CREATED)

class DeleteGroups(generics.DestroyAPIView):
    queryset = BaseTournament.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        tournament = self.get_object()

        if GroupMatch.objects.filter(group__tournament=tournament).exclude(
            status=MatchStatus.SCHEDULED,
        ).exists():
            return Response({
                # pylint: disable-next=line-too-long
                "error": _("Impossible de supprimer les poules. Des matchs sont en cours ou déjà terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        tournament.group_set.all().delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class GenerateGroupMatchs(generics.CreateAPIView):
    serializer_class = serializers.GenerateGroupMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        if kwargs["pk"] != request.data["tournament"]:
            raise BadRequest()

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        for group in data.validated_data["groups"]:
            create_group_matchs(group, data.validated_data["bo_type"])

        groups = serializers.GroupField(data.validated_data["tournament"].group_set.all(),
                                        many=True).data

        return Response(groups, status=status.HTTP_201_CREATED)

class DeleteGroupMatchs(generics.DestroyAPIView):
    queryset = BaseTournament.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        tournament = self.get_object()

        matchs = GroupMatch.objects.filter(group__tournament=tournament)

        if matchs.exclude(status=MatchStatus.SCHEDULED).exists():
            return Response({
                # pylint: disable-next=line-too-long
                "error": _("Impossible de supprimer les matchs. Des matchs sont déjà en cours ou terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        matchs.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class GroupMatchsLaunch(generics.UpdateAPIView):
    serializer_class = serializers.LaunchMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, *args, **kwargs):
        if kwargs["pk"] != request.data["tournament"]:
            raise BadRequest()

        data = self.get_serializer(data=request.data, type="group")
        data.is_valid(raise_exception=True)

        matchs = []

        for match in data.validated_data["matchs"]:
            launch_match(match)
            matchs.append(match.id)

        return Response({ "matchs": matchs, "warning": data.validated_data["warning"] },
                        status=status.HTTP_200_OK)

class GroupMatchPatch(generics.UpdateAPIView):
    queryset = GroupMatch.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.GroupMatchSerializer
    lookup_url_kwarg = "match_id"

class GroupMatchScore(generics.UpdateAPIView):
    """Update score of a group match"""

    queryset = GroupMatch.objects.all().order_by("id")
    serializer_class = serializers.GroupMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
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
    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        try:
            match = GroupMatch.objects.get(pk=kwargs["match_id"],group=kwargs["group_id"])
        except GroupMatch.DoesNotExist as e:
            raise NotFound() from e

        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if match.status != Match.MatchStatus.ONGOING:
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
