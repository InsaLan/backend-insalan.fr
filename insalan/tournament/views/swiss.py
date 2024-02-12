from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, BadRequest

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

import insalan.tournament.serializers as serializers

from ..models import SwissRound, SwissMatch, MatchStatus, validate_match_data
from ..manage import update_match_score, update_next_knockout_match

from .permissions import ReadOnly, Patch

from collections import Counter

class SwissMatchScore(generics.UpdateAPIView):
    """Update score of a swiss match"""

    queryset = SwissMatch.objects.all().order_by("id")
    serializer_class = serializers.SwissMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        try:
            match = SwissMatch.objects.get(pk=kwargs["match_id"],swiss=kwargs["swiss_id"])
        except:
            raise NotFound()

        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if data["swiss"] != match.swiss.id:
            raise BadRequest(_("Mauvaise rounde suisse"))
        if data["id"] != match.id:
            raise BadRequest(_("Mauvais id de match"))

        validate_match_data(match, data)

        update_match_score(match,data)

        serializer = serializers.SwissMatchSerializer(match, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)