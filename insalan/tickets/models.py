"""
Module for defining the Ticket model.
"""
from __future__ import annotations

import uuid
from io import BytesIO
from os import path
from typing import TYPE_CHECKING

import qrcode
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image
from qrcode.image.pil import PilImage
from reportlab.lib import utils
from reportlab.pdfgen import canvas

from insalan import settings
from insalan.user.models import User
from insalan.cms.models import Content

if TYPE_CHECKING:
    from django.db.models import Combinable

class Ticket(models.Model):
    """
    Model representing a ticket.
    """

    class Status(models.TextChoices):
        """
        Enum for the ticket status.
        """
        CANCELLED = "CA", _("Annulé")
        SCANNED = "SC", _("Scanné")
        VALID = "VA", _("Valide")

    class Meta:
        """Meta options"""

        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")

    token = models.UUIDField(
        verbose_name=_("UUID"), unique=True, default=uuid.uuid4, editable=False
    )
    user: models.ForeignKey[User | Combinable, User] = models.ForeignKey(
        User, verbose_name=_("Utilisateur⋅ice"), on_delete=models.CASCADE
    )
    status = models.CharField(
        verbose_name=_("Statut"),
        max_length=2,
        choices=Status.choices,
        default=Status.VALID,
    )
    tournament = models.ForeignKey(
        "tournament.EventTournament", verbose_name=_("Tournoi"),
        on_delete=models.CASCADE, blank=False, null=False
    )

class TicketManager(models.Manager[Ticket]):
    """
    Manager for the Ticket model.
    """

    @staticmethod
    def generate_ticket_pdf(ticket: Ticket) -> bytes:
        """
        Generate a PDF file for a ticket.
        """
        page_width = 612
        page_height = 850

        # prevent unloadable models
        # pylint: disable-next=import-outside-toplevel
        from insalan.tournament.models import Player, Manager, Substitute

        # create the pdf
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # get and resize (to reduce the size of the pdf) the tournament image
        image = Image.open(path.join(settings.MEDIA_ROOT, str(ticket.tournament.logo)))
        image.thumbnail((int(page_width * 1.5), int(page_height * 1.5)), Image.Resampling.BILINEAR)
        img = utils.ImageReader(image)
        iw, ih = img.getSize()
        aspect = ih / float(iw)

        # draw the image (full height or centered if the image is too tall)
        image_y = max( page_height - (page_width * aspect), 0.64 * page_height )
        p.drawImage(img, 0, image_y + 0.058 * page_height, page_width, page_width * aspect)

        # draw a square with color #D9D9D9
        p.setFillColorRGB(217 / 255, 217 / 255, 217 / 255)
        p.rect(0, 0, page_width, 0.82 * page_height, fill=True, stroke=False)

        # draw a square with color #2C292D
        p.setFillColorRGB(44 / 255, 41 / 255, 45 / 255)
        p.rect(0, 0, page_width, 0.8 * page_height, fill=True, stroke=False)

        # draw a square with color #FFFFFF
        p.setFillColorRGB(255 / 255, 255 / 255, 255 / 255)
        p.rect(0, 0, page_width, 0.47 * page_height, fill=True, stroke=False)

        # draw a square with color #2C292D
        p.setFillColorRGB(44 / 255, 41 / 255, 45 / 255)
        p.rect(0, 0, page_width, 0.117 * page_height, fill=True, stroke=False)

        # encode the url in a qr code
        qr_buffer = BytesIO()
        url = settings.PROTOCOL + "://" + settings.WEBSITE_HOST + \
              reverse("tickets:get", args=[ticket.user.id, ticket.token])
        qrcode_img: PilImage = qrcode.make(url)
        qrcode_img.save(qr_buffer)
        qr = utils.ImageReader(qr_buffer)
        qr_size = 300/850 * page_height
        p.drawImage(qr, page_width/4, 0.117 * page_height, qr_size, qr_size)

        # add the logo from static
        logo = Image.open(path.join(settings.STATIC_ROOT, "images/logo.png"))
        img = utils.ImageReader(logo)
        im_size = 150/850 * page_height
        p.drawImage(img, 0.08 * page_width, 0.588 * page_height, im_size, im_size, mask='auto')

        # get the color of the logo
        logo_img = logo.copy()
        logo_img = logo_img.convert("RGBA")
        logo_img = logo_img.resize((1, 1), resample=0)
        color = logo_img.getpixel((0, 0))

        # add rectangles to qr code corners with the color of the logo
        p.setFillColorRGB(color[0] / 255, color[1] / 255, color[2] / 255)
        rect_size = 0.0176 * page_height
        rect_lenght = 0.1176 * page_height

        p.rect(page_width/4, 0.117 * page_height, rect_lenght, rect_size, fill=True, stroke=False)
        p.rect(page_width/4, 0.117 * page_height, rect_size, rect_lenght, fill=True, stroke=False)

        p.rect(page_width/4 + 0.49 * page_width, 0.117 * page_height, -rect_lenght, rect_size,
               fill=True, stroke=False)
        p.rect(page_width/4 + 0.49 * page_width, 0.117 * page_height, -rect_size, rect_lenght,
               fill=True, stroke=False)

        p.rect(page_width/4, 0.47 * page_height, rect_lenght, -rect_size, fill=True, stroke=False)
        p.rect(page_width/4, 0.47 * page_height, rect_size, -rect_lenght, fill=True, stroke=False)

        p.rect(page_width/4 + 0.49 * page_width, 0.47 * page_height, -rect_lenght, -rect_size,
               fill=True, stroke=False)
        p.rect(page_width/4 + 0.49 * page_width, 0.47 * page_height, -rect_size, -rect_lenght,
               fill=True, stroke=False)

        # write event name
        p.setFont("Helvetica", 0.049 * page_width)
        p.setFillColorRGB(255 / 255, 255 / 255, 255 / 255)
        p.drawCentredString(2.5 * page_width/4, 0.74 * page_height, ticket.tournament.event.name)

        # if ticket is related to a player
        player = Player.objects.filter(user=ticket.user, team__tournament=ticket.tournament).first()
        if player:
            p.setFont("Helvetica", 0.033 * page_width)
            p.setFillColorRGB(255 / 255, 255 / 255, 255 / 255)
            p.drawCentredString(2.5 * page_width/4, 0.706 * page_height, "Joueur⋅euse")

            # draw the team name
            team_name = player.team.name
            if len(team_name) > 20:
                team_name = team_name[:20] + "..."
            p.drawCentredString(2.5 * page_width/4, 0.67 * page_height, team_name)

            # draw the player name
            user_name = player.name_in_game
            if len(user_name) > 20:
                user_name = user_name[:20] + "..."
            p.drawCentredString(2.5 * page_width/4, 0.588 * page_height, user_name)

            p.drawCentredString(2.5 * page_width/4, 0.553 * page_height,
                                player.user.first_name + " " + player.user.last_name)
        # if ticket is related to a manager
        manager = Manager.objects.filter(user=ticket.user,
                                         team__tournament=ticket.tournament).first()
        if manager:
            p.setFont("Helvetica", 0.033 * page_width)
            p.setFillColorRGB(255 / 255, 255 / 255, 255 / 255)
            p.drawCentredString(1.5 * page_width/4 + page_width/4, 0.706 * page_height, "Manager")

            # draw the team name
            team_name = manager.team.name
            if len(team_name) > 20:
                team_name = team_name[:20] + "..."
            p.drawCentredString(2.5 * page_width/4, 0.671 * page_height, team_name)

            p.drawCentredString(2.5 * page_width/4, 0.553 * page_height,
                                manager.user.first_name + " " + manager.user.last_name)
        # if ticket is related to a substitute
        substitute = Substitute.objects.filter(user=ticket.user,
                                               team__tournament=ticket.tournament).first()
        if substitute:
            p.setFont("Helvetica", 0.033 * page_width)
            p.setFillColorRGB(255 / 255, 255 / 255, 255 / 255)
            p.drawCentredString(2.5 * page_width/4, 0.706 * page_height, "Remplaçant⋅e")

            # draw the team name
            team_name = substitute.team.name
            if len(team_name) > 20:
                team_name = team_name[:20] + "..."
            p.drawCentredString(2.5 * page_width/4, 0.670 * page_height, team_name)

            # draw the player name
            user_name = substitute.name_in_game
            if len(user_name) > 20:
                user_name = user_name[:20] + "..."
            p.drawCentredString(2.5 * page_width/4, 0.588 * page_height, user_name)

            p.drawCentredString(2.5 * page_width/4, 0.553 * page_height,
                                substitute.user.first_name + " " + substitute.user.last_name)

        # write conditions of use in the footer
        p.setFont("Helvetica", 0.02 * page_width)
        p.setFillColorRGB(255 / 255, 255 / 255, 255 / 255)

        # split the string in multiple lines
        n = 105
        cgv = Content.objects.filter(name="ticket_CGV")
        if cgv:
            parts: list[str] = []
            for i in cgv.first().content.split(" "):
                if len(parts) == 0 or len(parts[-1]) + 1 + len(i) > n:
                    parts.append(i)
                else:
                    parts[-1] += " " + i

            # write the lines
            for i, part in enumerate(parts):
                p.drawCentredString(page_width/2,
                                    0.094 * page_height - i * 0.0141 * page_height, part)

        p.showPage()
        p.save()
        return buffer.getvalue()

    @staticmethod
    def create_pdf_name(ticket: Ticket) -> str:
        """
        Create the name of the pdf file for a ticket.
        """
        # we only keep alphanumeric characters and spaces
        username = ''.join(
            c for c in ticket.user.username if c.isalnum() or c == " "
        ).replace(' ', '-')
        event_name = ''.join(
            c for c in ticket.tournament.event.name if c.isalnum() or c == " "
        ).replace(' ', '-')

        return f"billet-{username}-{event_name}.pdf"
