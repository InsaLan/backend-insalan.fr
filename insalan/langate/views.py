from django.shortcuts import render

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from insalan.user.models import User

from .models import LangateReply
from .serializers import ReplySerializer


class LangateUserView(CreateAPIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    """
    API endpoint used by the langate to authenticate and verify a user's data
    """

    def post(self, request, format=None):
        """
        Function to handle retrieving and checking user data

        Per the langate, this check is done with an HTTP POST. It may have no
        data, but when it does, the data provided is a simple JSON object with
        a single field "tournaments" that contains a comma-separated list of the
        tournaments the user is supposed to be registered for. In practice, it
        is never used.

        Our response is lengthier, and should contain all of the information
        necessary for the langate to identify the user.
        """
        # Name of the user
        # If we reached here, they are authenticated correctly, so now we
        # fetch their data
        gate_user = request.user
        print(f'Performing authentication for user "{gate_user}"')

        # Try and retrieve the user
        # See https://docs.djangoproject.com/en/4.1/topics/db/queries/#retrieving-objects
        site_users = User.objects.filter(username=gate_user)
        found_count = len(site_users)

        if found_count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if found_count > 1:
            # We need to have an HTTP code that is like
            # "5XX - we have no idea how we messed up this bad"
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Now we have *one* user
        reply_object = LangateReply.new(site_users[0])
        ret = ReplySerializer(reply_object)
        return Response(ret.data, status=status.HTTP_200_OK)
