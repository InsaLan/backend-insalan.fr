"""
This module contains the views for the Langate app.

LangateUserView is an API endpoint used by the langate to authenticate and verify a user's data.
It handles retrieving and checking user data, and provides a response containing 
all the necessary information for the langate to identify the user.
"""
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from insalan.tournament.models import Event, Player, PaymentStatus, Manager, Substitute
from insalan.user.models import User

from .models import LangateReply, TournamentRegistration
from .serializers import ReplySerializer

from insalan.user.serializers import UserLoginSerializer

class LangateUserView(CreateAPIView):
    """
    API endpoint used by the langate to authenticate and verify a user's data
    """
    authentication_classes = [SessionAuthentication]
    serializer_class = ReplySerializer

    def post(self, request, *args, **kwargs):
        """
        Function to handle retrieving and checking user data

        In the old langate, this check is done with an HTTP POST. It may have no
        data, but when it does, the data provided is a simple JSON object with
        a single field "tournaments" that contains a comma-separated list of the
        tournaments the user is supposed to be registered for. In practice, it
        is never used.

        In this API, we need exactly one parameter: `event_id`. If there is
        exactly one ongoing event, its ID is taken. Otherwise, it must be
        provided and correspond to one ongoing event.

        Our response is lengthier, and should contain all of the information
        necessary for the langate to identify the user.
        """
        # authenticate the user
        data = request.data
        serializer = UserLoginSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            user = serializer.check_validity(data)
            if user is None:
                return Response(
                    {"user": [_("Nom d'utilisateur·rice ou mot de passe incorrect")]},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # If we reached here, they are authenticated correctly, so now we
        # fetch their data
        gate_user = data.get("username")

        # Attempt to determine what the event id is
        # How many ongoing events are there?
        ongoing_events = Event.get_ongoing_ids()
        if len(ongoing_events) == 0:
            return Response(
                {"err": _("Pas d'évènement en cours")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Get the event
        ev_obj = Event.objects.get(id=ongoing_events[0])
        if not ev_obj.ongoing:
            return Response(
                {"err": _("Évènement non en cours")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find a registration
        user_obj = User.objects.get(username=gate_user)
        regs_pl = Player.objects.filter(user=user_obj, team__tournament__event=ev_obj)
        regs_man = Manager.objects.filter(user=user_obj, team__tournament__event=ev_obj)
        regs_sub = Substitute.objects.filter(user=user_obj, team__tournament__event=ev_obj)
        regs = list(regs_pl) + list(regs_man) + list(regs_sub)

        found_count = len(regs)

        # This will be our reply
        reply_object = LangateReply.new(user_obj)

        if found_count == 0:
            reply_object.err = LangateReply.RegistrationStatus.NOT_REGISTERED
            return Response(
                ReplySerializer(reply_object).data, status=status.HTTP_404_NOT_FOUND
            )

        # Now we have our registrations
        reply_object = LangateReply.new(user_obj)

        err_not_paid = False

        for regis in regs:
            tourney = TournamentRegistration()
            game = regis.team.tournament.game

            tourney.shortname = game.short_name
            tourney.game_name = game.name
            tourney.team = regis.team.name

            tourney.manager = isinstance(regis, Manager)

            tourney.has_paid = regis.payment_status == PaymentStatus.PAID
            err_not_paid = err_not_paid or not tourney.has_paid

            reply_object.tournaments.append(tourney)

        reply_object.err = (
            LangateReply.RegistrationStatus.NOT_PAID
            if err_not_paid
            else None
        )

        ret = ReplySerializer(reply_object)
        return Response(ret.data, status=status.HTTP_200_OK)
