from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import insalan.tournament.serializers as serializers

from ..models import KnockoutMatch, validate_match_data
from ..manage import update_match_score, update_next_knockout_match

class BracketMatchPatch(generics.UpdateAPIView):
    queryset = KnockoutMatch.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = serializers.KnockoutMatchSerializer
    lookup_url_kwarg = "match_id"

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
