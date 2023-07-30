import io
import uuid

from django.core import serializers
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from qrcode import make
from qrcode.image.svg import SvgImage
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Ticket
from insalan.user.models import User


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get(request: HttpRequest, username: str, token: str) -> JsonResponse:
    '''Get ticket details for the given username and token.'''
    try:
        token_uuid = uuid.UUID(hex=token)
    except ValueError:
        return JsonResponse({'err': 'Invalid uuid'},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'err': 'User not found'},
                            status=status.HTTP_404_NOT_FOUND)

    try:
        ticket = Ticket.objects.get(token=uuid.UUID(token), user=user)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': 'Ticket not found'},
                            status=status.HTTP_404_NOT_FOUND)

    return JsonResponse({
        'user': user.username,
        'token': ticket.token,
        'status': ticket.status,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def scan(request: HttpRequest, token: str) -> JsonResponse:
    '''Scan the ticket with the token if it's valid.'''
    try:
        token_uuid = uuid.UUID(hex=token)
    except ValueError:
        return JsonResponse({'err': 'Invalid uuid'},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        ticket = Ticket.objects.get(token=token_uuid)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': 'Ticket not found'},
                            status=status.HTTP_404_NOT_FOUND)

    if ticket.status == Ticket.Status.CANCELLED:
        return JsonResponse({'err': 'Ticket cancelled'})

    if ticket.status == Ticket.Status.SCANNED:
        return JsonResponse({'err': 'Ticket already scanned'})

    ticket.status = Ticket.Status.SCANNED
    ticket.save()

    return JsonResponse({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def qrcode(request: HttpRequest, token: str) -> HttpResponse:
    '''Generate a QR code for the ticket with the token.'''
    try:
        token_uuid = uuid.UUID(hex=token)
    except ValueError:
        return JsonResponse({'err': 'Invalid uuid'},
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        ticket = Ticket.objects.get(token=uuid.UUID(token), user=request.user)
    except Ticket.DoesNotExist:
        return JsonResponse({'err': 'Ticket not found'},
                            status=status.HTTP_404_NOT_FOUND)

    assert isinstance(request.user, User)
    url = request.build_absolute_uri(reverse(
        'tickets:get',
        args=[request.user.username, token]
    ))
    ticket_qrcode = make(url, image_factory=SvgImage)
    buffer = io.BytesIO()
    ticket_qrcode.save(buffer)

    return HttpResponse(buffer.getvalue().decode(),
                        content_type='image/svg+xml')
