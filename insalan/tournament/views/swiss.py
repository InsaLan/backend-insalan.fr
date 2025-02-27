from django.utils.translation import gettext_lazy as _
from django.core.exceptions import BadRequest

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import insalan.tournament.serializers as serializers

from ..models import MatchStatus, Tournament, SwissMatch, SwissRound, validate_match_data, Match
from ..manage import update_match_score, create_swiss_rounds, launch_match, generate_swiss_round_round

class CreateSwissRounds(generics.CreateAPIView):
    queryset = Tournament.objects.all()
    serializer_class = serializers.CreateSwissRoundsSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        request.data["tournament"] = pk

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        create_swiss_rounds(**data.validated_data)

        serialized_data = serializers.SwissRoundField(data.validated_data["tournament"].swissround_set.all(), many=True).data

        return Response(serialized_data, status=status.HTTP_201_CREATED)

class DeleteSwissRounds(generics.DestroyAPIView):
    queryset = Tournament.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, *args, **kwargs):
        tournament = self.get_object()

        if SwissMatch.objects.filter(swiss__tournament=tournament).exclude(status=MatchStatus.SCHEDULED).exists():
            return Response({
                "error": _("Impossible de supprimer les rondes suisses. Des matchs sont en cours ou déjà terminés.")
            }, status=status.HTTP_400_BAD_REQUEST)

        tournament.swissround_set.all().delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class SwissMatchsLaunch(generics.UpdateAPIView):
    serializer_class = serializers.LaunchMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, *args, **kwargs):
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

class GenerateSwissRoundRound(generics.UpdateAPIView):
    queryset = Tournament.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.GenerateSwissRoundRoundSerializer

    def patch(self, request, pk, *args, **kargs):
        request.data["tournament"] = pk

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        updated_matchs = generate_swiss_round_round(data.validated_data["swiss"], data.validated_data["round"])

        updated_matchs_serialized = serializers.SwissMatchSerializer(updated_matchs, many=True)

        updated_matchs_serialized = {m["id"]: m for m in updated_matchs_serialized.data}

        return Response(updated_matchs_serialized, status=status.HTTP_200_OK)

class SwissMatchPatch(generics.UpdateAPIView):
    queryset = SwissMatch.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.SwissMatchSerializer
    lookup_url_kwarg = "match_id"

class SwissMatchScore(generics.GenericAPIView):
    """Update score of a swiss match"""

    queryset = SwissMatch.objects.all().order_by("id")
    serializer_class = serializers.SwissMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
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
    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        try:
            match = SwissMatch.objects.get(pk=kwargs["match_id"],swiss=kwargs["swiss_id"])
        except SwissMatch.DoesNotExist as e:
            raise NotFound() from e

        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if match.status != Match.MatchStatus.ONGOING:
            return Return({"status" : "Le match n'est pas en cours"}, status = status.HTTP_400_BAD_REQUEST)

        error_response = validate_match_data(match, data)
        if error_response is not None:
            return Response({k: _(v) for k,v in error_response.items()},status=status.HTTP_400_BAD_REQUEST)

        update_match_score(match,data)

        serializer = serializers.SwissMatchSerializer(match, context={"request": request})

        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )
