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

from insalan.user.models import User
from .models import Ticket, TicketManager

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

    return JsonResponse(
        {
            "user": user.username,
            "token": ticket.token,
            "status": ticket.status,
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
def generate_pdf(request: HttpRequest, id: str) -> JsonResponse:
    """Generate a pdf ticket for the given user id."""
    try:
        ticket = Ticket.objects.get(id=id)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': _("Ticket non trouvé")},
                            status=status.HTTP_404_NOT_FOUND)

    if ticket.user != request.user:
        return JsonResponse({'err': _("Vous n'avez pas accès à ce ticket")},
                            status=status.HTTP_403_FORBIDDEN)

    pdf = TicketManager.generate_ticket_pdf(ticket)
    return HttpResponse(pdf, content_type='application/pdf')
