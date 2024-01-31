import logging
import sys
from django.contrib.auth.models import Permission
from django.core.mail import EmailMessage, get_connection, send_mail
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.utils.translation import gettext_lazy as _

import insalan.settings
from insalan.user.models import User
from insalan.tickets.models import TicketManager
from apscheduler.schedulers.background import BackgroundScheduler

class EmailConfirmationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generate an email confirmation token.
    It's just a PasswordResetTokenGenerator with a different salt.

    (NB: the django app secret is also used as a salt)
    """

    def __init__(self):
        super().__init__()
        self.key_salt = "IWontLaunch8TwitchStreamsWhenConnectionIsAlreadyBad"


class UserMailer:
    """
    Send emails.
    """
    def __init__(self, MAIL_HOST:str, MAIL_PORT:str, MAIL_FROM: str, MAIL_PASS: str, MAIL_SSL:bool, TEST: bool = False):
        self.MAIL_HOST = MAIL_HOST
        self.MAIL_PORT = MAIL_PORT
        self.MAIL_SSL = MAIL_SSL
        self.MAIL_FROM = MAIL_FROM
        self.MAIL_PASS = MAIL_PASS
        self.TEST = TEST
        self.queue = []

    def send_email_confirmation(self, user_object: User):
        """
        Send an e-mail confirmation token to the user registring.
        """
        # remove email confirmation permission
        user_object.user_permissions.remove(
            Permission.objects.get(codename="email_active")
        )
        token = EmailConfirmationTokenGenerator().make_token(user_object)
        user = user_object.username

        connection = get_connection(
            host=self.MAIL_HOST,
            port=self.MAIL_PORT,
            password=self.MAIL_PASS,
            fail_silently=False,
            use_ssl=self.MAIL_SSL,
            username=self.MAIL_FROM,
        )
        email = EmailMessage(
            insalan.settings.EMAIL_SUBJECT_PREFIX + _("Confirmez votre courriel"),
            _("Confirmez votre adresse de courriel en cliquant sur ") +
            f"{insalan.settings.PROTOCOL}://{insalan.settings.WEBSITE_HOST}/verification/{user}/{token}",
            self.MAIL_FROM,
            [user_object.email],
            connection=connection,
        )
        if self.TEST:
            email.send()
        else:
            self.queue.append(email)

    def send_password_reset(self, user_object: User):
        """
        Send a password reset token.
        """
        token = default_token_generator.make_token(user_object)
        user = user_object.username

        connection = get_connection(
            fail_silently=False,
            username=self.MAIL_FROM,
            password=self.MAIL_PASS,
            host=self.MAIL_HOST,
            port=self.MAIL_PORT,
            use_ssl=self.MAIL_SSL,
        )
        email = EmailMessage(
            insalan.settings.EMAIL_SUBJECT_PREFIX + _("Demande de ré-initialisation de mot de passe"),
            _(
                "Une demande de ré-initialisation de mot de passe a été effectuée "
                "pour votre compte. Si vous êtes à l'origine de cette demande, "
                "vous pouvez cliquer sur le lien suivant: "
            ) +
            f"{insalan.settings.PROTOCOL}://{insalan.settings.WEBSITE_HOST}/reset-password/{user}/{token}",
            self.MAIL_FROM,
            [user_object.email],
            connection=connection,
        )
        if self.TEST:
            email.send()
        else:
            self.queue.append(email)

    def send_kick_mail(self, user_object: User, team_name: str):
        """
        Send a mail to a user that has been kicked.
        """
        connection = get_connection(
            fail_silently=False,
            username=self.MAIL_FROM,
            password=self.MAIL_PASS,
            host=self.MAIL_HOST,
            port=self.MAIL_PORT,
            use_ssl=self.MAIL_SSL,
        )
        email = EmailMessage(
            insalan.settings.EMAIL_SUBJECT_PREFIX + _("Vous avez été exclu.e de votre équipe"),
            _("Vous avez été exclu.e de l'équipe %s.") % team_name,
            self.MAIL_FROM,
            [user_object.email],
            connection=connection,
        )
        if self.TEST:
            email.send()
        else:
            self.queue.append(email)

    def send_ticket_mail(self, user_object: User, ticket: str):
        """
        Send a mail to a user that has been kicked.
        """

        ticket_pdf = TicketManager.generate_ticket_pdf(ticket)

        connection = get_connection(
            fail_silently=False,
            username=self.MAIL_FROM,
            password=self.MAIL_PASS,
            host=self.MAIL_HOST,
            port=self.MAIL_PORT,
            use_ssl=self.MAIL_SSL,
        )
        email = EmailMessage(
            insalan.settings.EMAIL_SUBJECT_PREFIX + _("Votre billet pour l'InsaLan"),
            _("Votre inscription pour l'Insalan a été payée. Votre billet est disponible en pièce jointe. Vous pouvez retrouver davantages d'informations sur l'évènement sur le site internet de l'InsaLan."),
            self.MAIL_FROM,
            [user_object.email],
            connection=connection,
        )
        email.attach(
            TicketManager.create_pdf_name(ticket),
            ticket_pdf,
            "application/pdf"
        )

        if self.TEST:
            email.send()
        else:
            self.queue.append(email)

    def send_tournament_mail(self, user_object: User, title: str, content: str, attachment: str):
        """
        Send a mail
        """
        connection = get_connection(
            fail_silently=False,
            username=self.MAIL_FROM,
            password=self.MAIL_PASS,
            host=self.MAIL_HOST,
            port=self.MAIL_PORT,
            use_ssl=self.MAIL_SSL,
        )
        email = EmailMessage(
            insalan.settings.EMAIL_SUBJECT_PREFIX + title,
            content,
            self.MAIL_FROM,
            [user_object.email],
            connection=connection,
        )
        if attachment:
            email.attach(attachment.name, attachment.read())

        if self.TEST:
            email.send()
        else:
            self.queue.append(email)

    def send_first_mail(self):
        """
        Send the first mail in the queue.
        """
        if len(self.queue) == 0:
            return
        self.queue[0].send()
        self.queue.pop(0)

class MailManager:
    """
    Manage emails.
    """
    mailers = {}

    @staticmethod
    def get_mailer(MAIL_FROM: str) -> UserMailer:
        """
        Get a mailer for a specific email address.
        """
        if MAIL_FROM not in MailManager.mailers:
            return None
        return MailManager.mailers[MAIL_FROM]
    
    @staticmethod
    def get_default_mailer() -> UserMailer:
        """
        Get a mailer for a specific email address.
        """
        if len(MailManager.mailers) == 0:
            return None
        return list(MailManager.mailers.values())[0]

    @staticmethod
    def add_mailer(MAIL_HOST:str, MAIL_PORT: str, MAIL_FROM: str, MAIL_PASS: str, MAIL_SSL:bool, TEST: bool = False):
        """
        Add a mailer for a specific email address.
        """
        MailManager.mailers[MAIL_FROM] = UserMailer(MAIL_HOST, MAIL_PORT, MAIL_FROM, MAIL_PASS, MAIL_SSL, TEST=TEST)

    @staticmethod
    def send_queued_mail():
        """
        Send first mail in all mailer's queue.
        """
        for mailer in MailManager.mailers.values():
            mailer.send_first_mail()

def start_scheduler():
    # Remove apscheduler logs
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

    # Check if we are in test mode
    TEST = 'test' in sys.argv
    print(TEST, file=sys.stderr)

    # Add mailers
    for auth in insalan.settings.EMAIL_AUTH:
        mailer = insalan.settings.EMAIL_AUTH[auth]
        MailManager.add_mailer(mailer["host"], mailer["port"], mailer["from"], mailer["pass"], mailer["ssl"], TEST=TEST)

    # Start scheduler
    if not TEST:
        scheduler = BackgroundScheduler()
        scheduler.add_job(MailManager.send_queued_mail, 'interval', seconds=30)
        scheduler.start()
