from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from insalan.tickets.models import Ticket
from insalan.user.models import User

from .payement_status import PaymentStatus

class Manager(models.Model):
    """
    A Manager is someone in charge of heading a team of players.
    """

    user = models.ForeignKey(
        User,
        verbose_name=_("Utilisateur⋅ice"),
        on_delete=models.CASCADE,
    )
    team = models.ForeignKey(
        "Team",
        verbose_name=_("Équipe"),
        on_delete=models.CASCADE
    )
    payment_status = models.CharField(
        verbose_name=_("Statut du paiement"),
        max_length=10,
        blank=True,
        default=PaymentStatus.NOT_PAID,
        choices=PaymentStatus.choices,
        null=False,
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        verbose_name=_("Ticket"),
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        """Meta Options"""

        verbose_name = _("Inscription d'un⋅e manager")
        verbose_name_plural = _("Inscriptions de managers")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "team"], name="not_twice_same_manager"
            )
        ]

    def __str__(self) -> str:
        """Format this manager registration as a str"""
        return f"(Manager) {self.user.username} for {self.team}"

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self):
        """Return the Team object of the current team"""
        return self.team

    def clean(self):
        """
        Assert that the user associated with the provided manager does not already
        exist in any team of any tournament of the event
        """
        user = self.user
        event = self.get_team().get_tournament().get_event()
        if not unique_event_registration_validator(user,event, manager=self.id):
            raise ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        if not tournament_announced(self.team.get_tournament()):
            raise ValidationError(
                _("Tournoi non annoncé")
            )