from django.db import models
from django.utils.translation import gettext_lazy as _
from insalan.tournament.models import Tournament, Team, Player

from insalan.mailer import MailManager
from insalan.settings import EMAIL_AUTH

class TournamentMailer(models.Model):
    """
    The TournamentMailer model is used to send emails to players of a tournament with filters.
    
    The filters are:
    - tournament: the tournament of the players
    - team_validated: if the players are in validated teams
    - captains: if the players are captains

    The save method is overriden to send the mail to every players matching the filters and not
    actually save the object. The database table should be empty at all time.

    """
    class Meta:
        verbose_name_plural = 'mailers'  # The name displayed in the admin sidebar


    mail = models.CharField(
        verbose_name=_("Mail"),
        max_length=100,
        null=False,
        blank=True,
        default="",
    )
    number = models.IntegerField(
        verbose_name=_("Nombre de mails dans la file"),
        null=False,
        blank=True,
        default=0,
    )
    tournament = models.ForeignKey(
        Tournament,
        verbose_name=_("Tournoi"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    team_validated = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("Filtre d'équipe validée")
    )
    captains = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("Filtre de capitaines")
    )
    title = models.CharField(
        verbose_name=_("Titre du mail"),
        max_length=100,
        null=False,
        blank=True,
        default="",
    )
    content = models.TextField(
        verbose_name=_("Contenu du mail"),
        max_length=50000,
        null=False,
        blank=True,
        default="",
    )
    attachment = models.FileField(
        verbose_name=_("Pièce jointe"),
        blank=True,
        null=True,
        upload_to="mail-attachments",
    )

    def save(self, *args, **kwargs):
        """Override default save of TournamentMailer"""
        if self.mail != "":
            return super().save(*args, **kwargs)
        # get every players of the ongoing event
        players = Player.objects.filter(team__tournament__event__ongoing=True)
        # if the tournament is specified, filter by tournament
        if self.tournament is not None:
            players = players.filter(team__tournament=self.tournament)
        # if the team is validated, filter by validated teams
        if self.team_validated:
            players = players.filter(team__validated=True)
        # if the captains filter is enabled, filter by captains
        if self.captains:
            # get every teams
            teams = Team.objects.all()
            # get every captains
            captains = [team.captain.id for team in teams if team.captain is not None]
            # filter players by captains
            players = players.filter(id__in=captains)
        # send the mail to every players
        for player in players:
            # send the mail
            MailManager.get_mailer(EMAIL_AUTH["tournament"]["from"]).send_tournament_mail(
                player.user,
                self.title,
                self.content,
                self.attachment,
            )
