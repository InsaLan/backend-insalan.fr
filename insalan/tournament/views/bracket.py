from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, BadRequest

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

import insalan.tournament.serializers as serializers

from ..models import Bracket, KnockoutMatch, MatchStatus, BracketSet, validate_match_data
from ..manage import update_match_score, update_next_knockout_match

from .permissions import ReadOnly, Patch

from collections import Counter

class BracketMatchScore(generics.UpdateAPIView):
    """Update score of a bracket match"""

    queryset = KnockoutMatch.objects.all().order_by("id")
    serializer_class = serializers.KnockoutMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        try:
            match = KnockoutMatch.objects.get(pk=kwargs["match_id"],bracket=kwargs["bracket_id"])
        except:
            raise NotFound()

        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if not data["bracket_set"] in [member.value for member in BracketSet]:
            raise BadRequest(_("Type de tableau invalide"))
        if data["bracket"] != match.bracket.id:
            raise BadRequest(_("Arbre de tournoi incorrect"))
        if data["id"] != match.id:
            raise BadRequest(_("Mauvais id de match"))

        validate_match_data(match, data)

        update_match_score(match,data)

        if match.round_number != 0:
            update_next_knockout_match(match)

        serializer = serializers.KnockoutMatchSerializer(match, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)