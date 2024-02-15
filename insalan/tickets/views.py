"""
This module contains Django views for ticket-related operations.

It includes views for retrieving ticket details, scanning tickets, and generating QR codes for tickets.
"""
import io
import uuid

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from qrcode import make
from qrcode.image.svg import SvgImage

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from insalan.tournament.models import Team, Player, Substitute, Manager, PaymentStatus
from insalan.user.models import User
from .models import Ticket, TicketManager
from insalan.mailer import MailManager
from insalan.settings import EMAIL_AUTH

@api_view(["GET"])
@permission_classes([IsAdminUser])
def get(request: HttpRequest, id: str, token: str) -> JsonResponse:
    """Get ticket details for the given user id and token."""
    try:
        uuid.UUID(hex=token)
    except ValueError:
        return JsonResponse({'err': _("UUID invalide")},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return JsonResponse({'err': _("Utilisateur⋅ice non trouvé⋅e")},
                            status=status.HTTP_404_NOT_FOUND)

    try:
        ticket = Ticket.objects.get(token=uuid.UUID(token), user=user)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': _("Ticket non trouvé")},
                            status=status.HTTP_404_NOT_FOUND)

    # Get the team name for the user
    player = Player.objects.filter(user=user, team__tournament=ticket.tournament)
    if player.exists():
        team = player.first().team.name
    else:
        substitute = Substitute.objects.filter(user=user, team__tournament=ticket.tournament)
        if substitute.exists():
            team = substitute.first().team.name
        else:
            manager = Manager.objects.filter(user=user, team__tournament=ticket.tournament)
            if manager.exists():
                team = manager.first().team.name
            else:
                team = None

    return JsonResponse(
        {
            "user": user.username,
            "identity": user.get_full_name(),
            "token": ticket.token,
            "status": ticket.status,
            "tournament": ticket.tournament.name,
            "team": team,
        }
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def scan(request: HttpRequest, token: str) -> JsonResponse:
    """Scan the ticket with the token if it's valid."""
    try:
        token_uuid = uuid.UUID(hex=token)
    except ValueError:
        return JsonResponse({'err': _("UUID invalide")},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        ticket = Ticket.objects.get(token=token_uuid)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': _("Ticket non trouvé")},
                            status=status.HTTP_404_NOT_FOUND)

    if ticket.status == Ticket.Status.CANCELLED:
        return JsonResponse({'err': _("Ticket annulé")})

    if ticket.status == Ticket.Status.SCANNED:
        return JsonResponse({'err': _("Ticket déjà scanné")})

    ticket.status = Ticket.Status.SCANNED
    ticket.save()

    return JsonResponse({"success": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def qrcode(request: HttpRequest, token: str) -> HttpResponse:
    """Generate a QR code for the ticket with the token."""
    try:
        uuid.UUID(hex=token)
    except ValueError:
        return JsonResponse({'err': _("UUID invalide")},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        Ticket.objects.get(token=uuid.UUID(token), user=request.user)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': _("Ticket non trouvé")},
                            status=status.HTTP_404_NOT_FOUND)

    assert isinstance(request.user, User)
    url = request.build_absolute_uri(
        reverse("tickets:get", args=[request.user.id, token])
    )
    ticket_qrcode = make(url, image_factory=SvgImage)
    buffer = io.BytesIO()
    ticket_qrcode.save(buffer)

    return HttpResponse(buffer.getvalue().decode(), content_type="image/svg+xml")

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def generate_pdf(request: HttpRequest, token: str) -> JsonResponse:
    """Generate a pdf ticket for the given user id."""
    try:
        ticket = Ticket.objects.get(token=uuid.UUID(token))
    except Ticket.DoesNotExist:
        return JsonResponse({'err': _("Ticket non trouvé")},
                            status=status.HTTP_404_NOT_FOUND)

    if ticket.user != request.user:
        return JsonResponse({'err': _("Vous n'avez pas accès à ce ticket")},
                            status=status.HTTP_403_FORBIDDEN)

    pdf = TicketManager.generate_ticket_pdf(ticket)
    return HttpResponse(pdf, content_type='application/pdf')

@api_view(["POST"])
@permission_classes([IsAdminUser])
def pay(request: HttpRequest) -> JsonResponse:
    """
        This view is used to :
        - Mark as paid a registration from it's type and id
        - Create a ticket for the user that paid
        - Send an email to the user with the ticket
    """
    data = request.data
    print(data)
    if 'type' not in data or 'id' not in data:
        return JsonResponse({'err': _("Type ou id manquant")},
                            status=status.HTTP_400_BAD_REQUEST)

    if data['type'] == 'player':
        try:
            player = Player.objects.get(id=data['id'])
        except Player.DoesNotExist:
            return JsonResponse({'err': _("Inscription non trouvée")},
                                status=status.HTTP_404_NOT_FOUND)
        if player.payment_status == PaymentStatus.PAID:
            return JsonResponse({'err': _("Inscription déjà payée")},
                                status=status.HTTP_400_BAD_REQUEST)
        player.payment_status = PaymentStatus.PAID
        player.save()
        ticket = Ticket.objects.create(user=player.user, tournament=player.team.tournament)
        MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_ticket_mail(player.user, ticket)
        return JsonResponse({'success': True})
    elif data['type'] == 'substitute':
        try:
            substitute = Substitute.objects.get(id=data['id'])
        except Substitute.DoesNotExist:
            return JsonResponse({'err': _("Remplaçant⋅e non trouvé⋅e")},
                                status=status.HTTP_404_NOT_FOUND)
        if substitute.payment_status == PaymentStatus.PAID:
            return JsonResponse({'err': _("Remplaçant⋅e déjà payé⋅e")},
                                status=status.HTTP_400_BAD_REQUEST)
        substitute.payment_status = PaymentStatus.PAID
        substitute.save()
        ticket = Ticket.objects.create(user=substitute.user, tournament=substitute.team.tournament)
        MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_ticket_mail(substitute.user, ticket)
        return JsonResponse({'success': True})
    elif data['type'] == 'manager':
        try:
            manager = Manager.objects.get(id=data['id'])
        except Manager.DoesNotExist:
            return JsonResponse({'err': _("Manager non trouvé")},
                                status=status.HTTP_404_NOT_FOUND)
        if manager.payment_status == PaymentStatus.PAID:
            return JsonResponse({'err': _("Manager déjà payé")},
                                status=status.HTTP_400_BAD_REQUEST)
        manager.payment_status = PaymentStatus.PAID
        manager.save()
        ticket = Ticket.objects.create(user=manager.user, tournament=manager.team.tournament)
        MailManager.get_mailer(EMAIL_AUTH["contact"]["from"]).send_ticket_mail(manager.user, ticket)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'err': _("Type invalide")},
                            status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def unpaid(request: HttpRequest) -> JsonResponse:
    """
        This view is used to get all the unpaid registrations
    """
    # Get all the registrations that are not paid
    players = Player.objects.filter(
        team__validated=True, 
        team__tournament__event__ongoing=True
    ).exclude(payment_status=PaymentStatus.PAID)
    substitutes = Substitute.objects.filter(
        team__validated=True,
        team__tournament__event__ongoing=True
    ).exclude(payment_status=PaymentStatus.PAID)
    managers = Manager.objects.filter(
        team__validated=True,
        team__tournament__event__ongoing=True
    ).exclude(payment_status=PaymentStatus.PAID)

    return JsonResponse([
        {
            'id': reg.id,
            'type': 'player',
            'user': reg.user.username,
            'team': reg.team.name,
        } for reg in players
    ] + [
        {
            'id': reg.id,
            'type': 'substitute',
            'user': reg.user.username,
            'team': reg.team.name,
        } for reg in substitutes
    ] + [
        {
            'id': reg.id,
            'type': 'manager',
            'user': reg.user.username,
            'team': reg.team.name,
        } for reg in managers
    ], safe=False)
