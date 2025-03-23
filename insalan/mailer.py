import logging
import sys
from typing import cast

import django_stubs_ext

from django.contrib.auth.models import Permission
from django.core.files import File
from django.core.mail import EmailMessage, get_connection
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.utils.translation import gettext_lazy as _

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import]

from insalan import settings
from insalan.user.models import User
from insalan.tickets.models import Ticket, TicketManager
from insalan.scheduler import scheduler


django_stubs_ext.monkeypatch(extra_classes=[File])


class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generate an email confirmation token.
    It's just a PasswordResetTokenGenerator with a different salt.

    (NB: the django app secret is also used as a salt)
    """

    def __init__(self) -> None:
        super().__init__()
        self.key_salt = "IWontLaunch8TwitchStreamsWhenConnectionIsAlreadyBad"


class UserMailer:
    """
    Send emails.
    """
    def __init__(self, mail_host: str, mail_port: str, mail_from: str, mail_pass: str,
                 mail_ssl: bool, test: bool = False) -> None:
        self.mail_host = mail_host
        self.mail_port = mail_port
        self.mail_ssl = mail_ssl
        self.mail_from = mail_from
        self.mail_pass = mail_pass
        self.test = test
        self.queue: list[EmailMessage] = []

    def send_email_confirmation(self, user_object: User) -> None:
        """
        Send an e-mail confirmation token to the user registring.
        """
        # remove email confirmation permission
        user_object.user_permissions.remove(
            Permission.objects.get(codename="email_active")
        )
        token = EmailConfirmationTokenGenerator().make_token(user_object)
        user = user_object.pk

        connection = get_connection(
            host=self.mail_host,
            port=self.mail_port,
            password=self.mail_pass,
            fail_silently=False,
            use_ssl=self.mail_ssl,
            username=self.mail_from,
        )
        email = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + _("Confirmez votre courriel"),
            _("Confirmez votre adresse de courriel en cliquant sur ") +
            f"{settings.PROTOCOL}://{settings.WEBSITE_HOST}/verification/{user}/{token}/",
            self.mail_from,
            [user_object.email],
            connection=connection,
        )
        if self.test:
            email.send()
        else:
            self.queue.append(email)

    def send_password_reset(self, user_object: User) -> None:
        """
        Send a password reset token.
        """
        token = default_token_generator.make_token(user_object)
        user = user_object.pk

        connection = get_connection(
            fail_silently=False,
            username=self.mail_from,
            password=self.mail_pass,
            host=self.mail_host,
            port=self.mail_port,
            use_ssl=self.mail_ssl,
        )
        email = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + _("Demande de ré-initialisation de mot de passe"),
            _(
                "Une demande de ré-initialisation de mot de passe a été effectuée "
                "pour votre compte. Si vous êtes à l'origine de cette demande, "
                "vous pouvez cliquer sur le lien suivant: "
            ) +
            f"{settings.PROTOCOL}://{settings.WEBSITE_HOST}/reset-password/{user}/{token}/",
            self.mail_from,
            [user_object.email],
            connection=connection,
        )
        if self.test:
            email.send()
        else:
            self.queue.append(email)

    def send_kick_mail(self, user_object: User, team_name: str) -> None:
        """
        Send a mail to a user that has been kicked.
        """
        connection = get_connection(
            fail_silently=False,
            username=self.mail_from,
            password=self.mail_pass,
            host=self.mail_host,
            port=self.mail_port,
            use_ssl=self.mail_ssl,
        )
        email = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + _("Vous avez été exclu.e de votre équipe"),
            _("Vous avez été exclu.e de l'équipe %s.") % team_name,
            self.mail_from,
            [user_object.email],
            connection=connection,
        )
        if self.test:
            email.send()
        else:
            self.queue.append(email)

    def send_ticket_mail(self, user_object: User, ticket: Ticket) -> None:
        """
        Send a mail with the ticket in attachment.
        """

        ticket_pdf = TicketManager.generate_ticket_pdf(ticket)

        connection = get_connection(
            fail_silently=False,
            username=self.mail_from,
            password=self.mail_pass,
            host=self.mail_host,
            port=self.mail_port,
            use_ssl=self.mail_ssl,
        )
        email = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + _("Votre billet pour l'InsaLan"),
            # pylint: disable-next=line-too-long
            cast(str, _("Votre inscription pour l'Insalan a été payée. Votre billet est disponible en pièce jointe. Vous pouvez retrouver davantages d'informations sur l'évènement sur le site internet de l'InsaLan.")),
            self.mail_from,
            [user_object.email],
            connection=connection,
        )
        email.attach(
            TicketManager.create_pdf_name(ticket),
            ticket_pdf,
            "application/pdf"
        )

        if self.test:
            email.send()
        else:
            self.queue.append(email)

    def send_tournament_mail(
        self,
        user_object: User,
        title: str,
        content: str,
        attachment: File[bytes] | None,  # pylint: disable=unsubscriptable-object
    ) -> None:
        """Send a mail."""
        connection = get_connection(
            fail_silently=False,
            username=self.mail_from,
            password=self.mail_pass,
            host=self.mail_host,
            port=self.mail_port,
            use_ssl=self.mail_ssl,
        )
        email = EmailMessage(
            settings.EMAIL_SUBJECT_PREFIX + title,
            content,
            self.mail_from,
            [user_object.email],
            connection=connection,
        )
        if attachment:
            email.attach(attachment.name, attachment.read())

        if self.test:
            email.send()
        else:
            self.queue.append(email)

    def send_first_mail(self) -> None:
        """
        Send the first mail in the queue.
        """
        if len(self.queue) == 0:
            return
        try:
            self.queue[0].send()
            self.queue.pop(0)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print("Error sending mail", e, file=sys.stderr)
            mail = self.queue.pop(0)
            self.queue.append(mail)

class MailManager:
    """
    Manage emails.
    """
    mailers: dict[str, UserMailer] = {}

    @staticmethod
    def get_mailer(mail_from: str) -> UserMailer | None:
        """
        Get a mailer for a specific email address.
        """
        if mail_from not in MailManager.mailers:
            return None
        return MailManager.mailers[mail_from]

    @staticmethod
    def get_default_mailer() -> UserMailer | None:
        """
        Get a mailer for a specific email address.
        """
        if len(MailManager.mailers) == 0:
            return None
        return list(MailManager.mailers.values())[0]

    @staticmethod
    def add_mailer(mail_host: str, mail_port: str, mail_from: str, mail_pass: str, mail_ssl: bool,
                   test: bool = False) -> None:
        """
        Add a mailer for a specific email address.
        """
        MailManager.mailers[mail_from] = UserMailer(mail_host, mail_port, mail_from, mail_pass,
                                                    mail_ssl, test=test)

    @staticmethod
    def send_queued_mail() -> None:
        """
        Send first mail in all mailer's queue.
        """
        for mailer in MailManager.mailers.values():
            mailer.send_first_mail()

def start_job() -> None:
    # Check if we are in test mode
    test = 'test' in sys.argv

    # Add mailers
    for auth in settings.EMAIL_AUTH:
        mailer = settings.EMAIL_AUTH[auth]
        MailManager.add_mailer(mailer["host"], mailer["port"], mailer["from"], mailer["pass"],
                               mailer["ssl"], test=test)

    # Start scheduler
    if not test:
        scheduler.add_job(MailManager.send_queued_mail, 'interval', seconds=30)
