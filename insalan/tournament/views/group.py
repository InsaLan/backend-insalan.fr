from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, BadRequest

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

import insalan.tournament.serializers as serializers

from ..models import Group, GroupMatch, MatchStatus, validate_match_data
from ..manage import update_match_score

from .permissions import ReadOnly, Patch

from collections import Counter

class GroupMatchScore(generics.UpdateAPIView):
    """Update score of a group match"""

    queryset = GroupMatch.objects.all().order_by("id")
    serializer_class = serializers.GroupMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        try:
            match = GroupMatch.objects.get(pk=kwargs["match_id"],group=kwargs["group_id"])
        except:
            raise NotFound()

        if not match.is_user_in_match(user):
            raise PermissionDenied()

        if data["group"] != match.group.id:
            raise BadRequest(_("Mauvaise poule"))
        if data["id"] != match.id:
            raise BadRequest(_("Mauvais id de match"))

        validate_match_data(match, data)

        update_match_score(match,data)

        serializer = serializers.GroupMatchSerializer(match, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)