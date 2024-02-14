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

        error_response = validate_match_data(match, data)
        if error_response != None:
            return Response({k: _(v) for k,v in error_response.items()},status=status.HTTP_400_BAD_REQUEST)

        update_match_score(match,data)

        serializer = serializers.GroupMatchSerializer(match, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)