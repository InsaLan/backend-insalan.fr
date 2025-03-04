from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, BadRequest

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .permissions import ReadOnly

from insalan.tournament import serializers

from ..models import Bracket, BestofType, KnockoutMatch, MatchStatus, Tournament, validate_match_data, Match
from ..manage import create_empty_knockout_matchs, update_match_score, update_next_knockout_match, launch_match


class BracketDetails(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bracket.objects.all()
    permission_classes = [permissions.IsAdminUser | ReadOnly]
    serializer_class = serializers.BracketSerializer

    def delete(self, request, *args, **kwargs):
        bracket = self.get_object()

        if KnockoutMatch.objects.filter(bracket=bracket).exclude(status=MatchStatus.SCHEDULED).exists():
            return Response({
                "error": _("Impossible de supprimer l'arbre.\
                    Des matchs sont déjà en cours ou terminés")
            }, status=status.HTTP_400_BAD_REQUEST)

        bracket.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class CreateBracket(generics.CreateAPIView):
    queryset = Tournament.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.BracketSerializer

    def post(self, request, pk, *args, **kwargs):
        request.data["tournament"] = pk

        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)

        bo_type = data.validated_data.pop("bo_type", BestofType.BO1)

        bracket = Bracket.objects.create(**data.validated_data)

        create_empty_knockout_matchs(bracket, bo_type)

        return Response(serializers.BracketField(bracket).data, status=status.HTTP_201_CREATED)

class BracketMatchPatch(generics.UpdateAPIView):
    queryset = KnockoutMatch.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.KnockoutMatchSerializer
    lookup_url_kwarg = "match_id"

    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)

        match = self.get_object()

        if match.status == MatchStatus.COMPLETED and not match.is_last_match():
            update_next_knockout_match(match)

        return response

class BracketMatchsLaunch(generics.UpdateAPIView):
    serializer_class = serializers.LaunchMatchsSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, *args, **kwargs):
        if kwargs["pk"] != request.data["tournament"]:
            raise BadRequest()

        data = self.get_serializer(data=request.data, type="bracket")
        data.is_valid(raise_exception=True)

        matchs = []

        for match in data.validated_data["matchs"]:
            launch_match(match)

            if match.status == MatchStatus.COMPLETED:
                update_next_knockout_match(match)

            matchs.append(match.id)

        return Response({ "matchs": matchs, "warning": data.validated_data["warning"] },status=status.HTTP_200_OK)

class BracketMatchScore(generics.GenericAPIView):
    """Update score of a bracket match"""

    queryset = KnockoutMatch.objects.all().order_by("id")
    serializer_class = serializers.KnockoutMatchSerializer
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
            match = KnockoutMatch.objects.get(pk=kwargs["match_id"],bracket=kwargs["bracket_id"])
        except KnockoutMatch.DoesNotExist as e:
            raise NotFound() from e

        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if match.status != Match.MatchStatus.ONGOING:
            return Response({"status" : "Le match n'est pas en cours"}, status = status.HTTP_400_BAD_REQUEST)

        error_response = validate_match_data(match, data)
        if error_response is not None:
            return Response({k: _(v) for k,v in error_response.items()},status=status.HTTP_400_BAD_REQUEST)

        update_match_score(match,data)

        if match.round_number != 0:
            update_next_knockout_match(match)

        serializer = serializers.KnockoutMatchSerializer(match, context={"request": request})

        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )
