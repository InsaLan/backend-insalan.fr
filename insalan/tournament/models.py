"""
Module that contains the declaration of structures tied to tournaments
"""

# Disable lints:
# "Too few public methods"
# pylint: disable=R0903

from datetime import datetime, timedelta
from typing import List, Optional
from math import ceil
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    MinLengthValidator,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from rest_framework import serializers
from typing import Union, List

from insalan.tickets.models import Ticket
from insalan.user.models import User


class Event(models.Model):
    """
    An Event is any single event that is characterized by the following:
     - A single player can only register for a single tournament per event

    This means, for example, that if we want to let players play in the smash
    tournaments and InsaLan one year, we can have two events happening
    concurrently.
    """

    name = models.CharField(
        verbose_name=_("Nom de l'évènement"),
        max_length=40,
        validators=[MinLengthValidator(4)],
        null=False,
    )
    description = models.CharField(
        verbose_name=_("Description de l'évènement"),
        max_length=128,
        default="",
        blank=True,
    )
    year = models.IntegerField(
        verbose_name=_("Année"), null=False, validators=[MinValueValidator(2003)]
    )
    month = models.IntegerField(
        verbose_name=_("Mois"),
        null=False,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    ongoing = models.BooleanField(verbose_name=_("En cours"), default=False)
    logo: models.FileField = models.FileField(
        verbose_name=_("Logo"),
        blank=True,
        null=True,
        upload_to="event-icons",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp"])
        ],
    )

    class Meta:
        """Meta options"""

        verbose_name = _("Évènement")
        verbose_name_plural = _("Évènements")

    def __str__(self) -> str:
        """Format this Event to a str"""
        return f"{self.name} ({self.year}-{self.month:02d})"

    def get_tournaments_id(self) -> List[int]:
        """Return the list of tournaments identifiers for that Event"""
        return Tournament.objects.filter(event=self).values_list("id", flat=True)

    def get_tournaments(self) -> List["Tournament"]:
        """Return the list of tournaments for that Event"""
        return Tournament.objects.filter(event=self)

    @staticmethod
    def get_ongoing_ids() -> List[int]:
        """Return the identifiers of ongoing events"""
        return __class__.objects.filter(ongoing=True).values_list("id", flat=True)


class Game(models.Model):
    """
    A Game is the representation of a Game that is being played at InsaLan
    """

    class Meta:
        """Meta options"""

        verbose_name = _("Jeu")
        verbose_name_plural = _("Jeux")

    name = models.CharField(
        verbose_name=_("Nom du jeux"),
        validators=[MinLengthValidator(2)],
        max_length=40,
        null=False,
    )
    short_name = models.CharField(
        verbose_name=_("Nom raccourci du jeu"),
        validators=[MinLengthValidator(2)],
        max_length=10,
        null=False,
        blank=False,
    )
    players_per_team = models.IntegerField(
        verbose_name=_("Number of players per team"),
        null=False,
        validators=[MinValueValidator(1)],
        default=1
    )
    substitute_players_per_team = models.IntegerField(
        verbose_name=_("Number of substitute players per team"),
        null=False,
        validators=[MinValueValidator(0)],
        default=0
    )

    def __str__(self) -> str:
        """Format this Game to a str"""
        return f"{self.name} ({self.short_name})"

    def get_name(self) -> str:
        """Return the name of the game"""
        return self.name

    def get_short_name(self) -> str:
        """Return the short name of the game"""
        return self.short_name

    def get_players_per_team(self) -> int:
        """Return the number of players per team"""
        return self.players_per_team

    def get_substitute_players_per_team(self) -> int:
        """Return the number of substitute players per team"""
        return self.substitute_players_per_team

def in_thirty_days():
    """Return now + 30 days"""
    return timezone.now() + timedelta(days=30)


class Tournament(models.Model):
    """
    A Tournament happening during an event that Teams of players register for.
    """

    event = models.ForeignKey(
        Event, verbose_name=_("Évènement"), on_delete=models.CASCADE
    )
    game = models.ForeignKey(Game, verbose_name=_("Jeu"), on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name=_("Nom du tournoi"),
        validators=[MinLengthValidator(3)],
        max_length=40,
    )
    is_announced = models.BooleanField(verbose_name=_("Annoncé"), default=False)
    rules = models.TextField(
        verbose_name=_("Règlement du tournoi"),
        max_length=50000,
        null=False,
        blank=True,
        default="",
    )
    registration_open = models.DateTimeField(
        verbose_name=_("Ouverture des inscriptions"),
        default=timezone.now,
        blank=True,
        null=False,
    )
    registration_close = models.DateTimeField(
        verbose_name=_("Fermeture des inscriptions"),
        blank=True,
        default=in_thirty_days,
        null=False,
    )
    logo: models.FileField = models.FileField(
        verbose_name=_("Logo"),
        blank=True,
        null=True,
        upload_to="tournament-icons",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp"])
        ],
    )
    # Tournament player slot prices
    # These prices are used at the tournament creation to create associated
    # products
    player_price_online = models.DecimalField(
        null=False,
        default=0.0,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("prix joueur en ligne"),
    )  # when paying on the website

    player_price_onsite = models.DecimalField(
        null=False,
        default=0.0,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("prix joueur sur place"),
    )  # when paying on site

    # Tournament manager slot prices
    manager_price_online = models.DecimalField(
        null=False,
        default=0.0,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("prix manager en ligne"),
    )  # when paying on the website

    manager_price_onsite = models.DecimalField(
        null=False,
        default=0.0,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("prix manager sur place"),
    )  # when paying on site
        # Tournament manager slot prices
    substitute_price_online = models.DecimalField(
        null=False,
        default=0.0,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("prix Remplaçant en ligne"),
    )  # when paying on the website
    substitute_price_onsite = models.DecimalField(
        null=False,
        default=0.0,
        max_digits=5,
        decimal_places=2,
        verbose_name=_("prix Remplaçant sur place"),
    )  # when paying on site
    cashprizes = ArrayField(
        models.DecimalField(
            null=False,
            default=0.0,
            decimal_places=2,
            max_digits=6,
            validators=[MinValueValidator(0)],
        ),
        default=list,
        blank=True,
        verbose_name=_("Cashprizes"),
    )
    manager_online_product = models.ForeignKey(
        "payment.Product",
        related_name="manager_product_reference",
        null=True,
        blank=True,
        verbose_name=_("Produit manager"),
        on_delete=models.SET_NULL,
    )
    substitute_online_product = models.ForeignKey(
        "payment.Product",
        related_name="substitute_product_reference",
        null=True,
        blank=True,
        verbose_name=_("Produit substitute"),
        on_delete=models.SET_NULL,
    )
    player_online_product = models.ForeignKey(
        "payment.Product",
        related_name="player_product_reference",
        null=True,
        blank=True,
        verbose_name=_("Produit joueur"),
        on_delete=models.SET_NULL,
    )
    maxTeam = models.IntegerField(
        default=0,
        null=False,
        verbose_name=_("Nombre maximal d'équipe"),
        validators=[MinValueValidator(0)],
    )
    description = models.CharField(
        null=False,
        blank=True,
        default='',
        verbose_name=_("Description du tournoi"),
        max_length=300,
    )

    class Meta:
        """Meta options"""

        verbose_name = _("Tournoi")
        verbose_name_plural = _("Tournois")

    def save(self, *args, **kwargs):
        """
        Override default save of Tournament.
        When a Tournament object is created, it creates 2 products, its associated
        products to allow players and managers to pay the entry fee
        """

        from insalan.payment.models import Product, ProductCategory

        super().save(*args, **kwargs)  # Get the self accessible to the products

        need_save = False
        update_fields = kwargs.get("update_fields", [])

        if self.player_online_product is None:
            prod = Product.objects.create(
                price=self.player_price_online,
                name=_(f"Place {self.name} Joueur en ligne"),
                desc=_(f"Inscription au tournoi {self.name} joueur"),
                category=ProductCategory.REGISTRATION_PLAYER,
                associated_tournament=self,
                available_from=self.registration_open,
                available_until=self.registration_close,
            )
            self.player_online_product = prod
            need_save = True

        self.player_online_product.available_from = self.registration_open
        self.player_online_product.available_until = self.registration_close
        self.player_online_product.save()

        if self.manager_online_product is None:
            prod = Product.objects.create(
                price=self.manager_price_online,
                name=_(f"Place {self.name} manager en ligne"),
                desc=_(f"Inscription au tournoi {self.name} manager"),
                category=ProductCategory.REGISTRATION_MANAGER,
                associated_tournament=self,
                available_from=self.registration_open,
                available_until=self.registration_close,
            )
            self.manager_online_product = prod
            need_save = True

        self.manager_online_product.available_from = self.registration_open
        self.manager_online_product.available_until = self.registration_close
        self.manager_online_product.save()

        if self.substitute_online_product is None:
            prod = Product.objects.create(
                price=self.substitute_price_online,
                name=_(f"Place {self.name} remplaçant en ligne"),
                desc=_(f"Inscription au tournoi {self.name} remplaçant"),
                category=ProductCategory.REGISTRATION_SUBSTITUTE,
                associated_tournament=self,
                available_from=self.registration_open,
                available_until=self.registration_close,
            )
            self.substitute_online_product = prod
            need_save = True
        
        self.substitute_online_product.available_from = self.registration_open
        self.substitute_online_product.available_until = self.registration_close
        self.substitute_online_product.save()

        if need_save:
            super().save()

    def __str__(self) -> str:
        """Format this Tournament to a str"""
        return f"{self.name} (@ {self.event})"

    def get_name(self) -> str:
        """Get the name of the tournament"""
        return self.name

    def get_event(self) -> Event:
        """Get the event of a tournament"""
        return self.event

    def get_game(self) -> Game:
        """Get the game of a tournament"""
        return self.game

    def get_teams(self) -> List["Team"]:
        """Return the list of Teams in that Tournament"""
        return Team.objects.filter(tournament=self)

    def get_teams_id(self) -> List[int]:
        """Return the list of identifiers of this Tournament's Teams"""
        return self.get_teams().values_list("id", flat=True)

    def get_rules(self) -> str:
        """Return the raw tournament rules"""
        return self.rules

    def get_maxTeam(self) -> int:
        """Return the max number of teams"""
        return self.maxTeam

    def get_validated_teams(self, exclude=None) -> int:
        """Return the number of validated teams"""
        return len(Team.objects.filter(tournament=self,validated=True).exclude(id=exclude))

    def get_casters(self) -> List["Caster"]:
        """Return the list of casters for this tournament"""
        return Caster.objects.filter(tournament=self)


class Team(models.Model):
    """
    A Team consists in a group of one or more players, potentially helmed by a
    `Manager`.
    """

    tournament = models.ForeignKey(
        Tournament,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name=_("Tournoi"),
    )
    name = models.CharField(
        max_length=42,
        validators=[MinLengthValidator(3)],
        null=False,
        blank=False,
        verbose_name=_("Nom d'équipe"),
    )
    validated = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("Équipe validée")
    )
    password = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(8)],
        null=False,
        blank=False,
        verbose_name=_("Mot de passe de l'équipe"),
    )

    class Meta:
        """Meta Options"""

        verbose_name = _("Équipe")
        verbose_name_plural = _("Équipes")
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "name"], name="no_name_conflict_in_tournament"
            )
        ]

    def __str__(self) -> str:
        """Format this team to a str"""
        if self.tournament is not None:
            return f"{self.name} ({self.tournament.event})"
        return f"{self.name} (???)"

    def get_name(self):
        """
        Retrieve the name of this team.
        """
        return self.name

    def get_tournament(self) -> Optional[Tournament]:
        """
        Retrieve the tournament of this team. Potentially null.
        """
        return self.tournament

    def get_players(self) -> List["Player"]:
        """
        Retrieve all the players in the database for that team
        """
        return Player.objects.filter(team=self)

    def get_players_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all players
        """
        return self.get_players().values_list("id", flat=True)

    def get_managers(self) -> List["Manager"]:
        """
        Retrieve all the managers in the database for that team
        """
        return Manager.objects.filter(team=self)

    def get_managers_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all managers
        """
        return self.get_managers().values_list("id", flat=True)
    
    def get_substitutes(self) -> List["Substitute"]:
        """
        Retrieve all the substitutes in the database for that team
        """
        return Substitute.objects.filter(team=self)
    
    def get_substitutes_id(self) -> List[int]:
        """
        Retrieve the user identifiers of all substitutes
        """
        return self.get_substitutes().values_list("id", flat=True)

    def get_password(self) -> str:
        """Return team password"""
        return self.password

    def refresh_validation(self):
        """Refreshes the validation state of a tournament"""
        # Condition 1: ceil((n+1)/2) players have paid/will pay
        if self.validated:
            return
        else:
            if self.tournament.get_validated_teams() < self.tournament.get_maxTeam():
                players = self.get_players()

                game = self.get_tournament().get_game()

                threshold = ceil((game.get_players_per_team()+1)/2)

                paid_seats = len(players.filter(payment_status=PaymentStatus.PAID))

                self.validated = paid_seats >= threshold
                self.save()

    def clean(self):
        """
        Assert that the tournament associated with the provided team is announced
        """
        if not tournament_announced(self.tournament):
            raise ValidationError(
                _("Tournoi non annoncé")
            )
        if tournament_registration_full(self.tournament, exclude=self.id):
            raise ValidationError(
                _("Tournoi complet")
            )


class PaymentStatus(models.TextChoices):
    """Information about the current payment status of a Player/Manager"""

    NOT_PAID = "NOTPAID", _("Pas payé")
    PAID = "PAID", _("Payé")
    PAY_LATER = "LATER", _("Payera sur place")


class Player(models.Model):
    """
    A Player at InsaLan is simply anyone who is registered to participate in a
    tournamenent, whichever it might be.
    """

    class Meta:
        """Meta options"""

        verbose_name = _("Inscription d'un⋅e joueur⋅euse")
        verbose_name_plural = _("Inscription de joueur⋅euses")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Utilisateur⋅ice"),
    )
    team = models.ForeignKey(
        "tournament.Team",
        on_delete=models.CASCADE,
        verbose_name=_("Équipe")
    )
    payment_status = models.CharField(
        max_length=10,
        blank=True,
        default=PaymentStatus.NOT_PAID,
        choices=PaymentStatus.choices,
        null=False,
        verbose_name=_("Statut du paiement"),
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        verbose_name=_("Ticket"),
        null=True,
        blank=True,
        default=None,
    )
    name_in_game = models.CharField(
        max_length=42,
        validators=[MinLengthValidator(1)],
        null=False,
        blank=False,
        verbose_name=_("Pseudo en jeu"),
    )

    def __str__(self) -> str:
        """Format this player registration to a str"""
        return f"{self.user.username} for {self.team}"

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self) -> Team:
        """Return the Team object of the current team"""
        return self.team

    def get_name_in_game(self) -> str:
        """Return the name_in_game of the player"""
        return self.name_in_game

    def clean(self):
        """
        Assert that the user associated with the provided player does not already
        exist in any team of any tournament of the event
        """
        user = self.user
        event = self.team.get_tournament().get_event()
        if not unique_event_registration_validator(user,event,player=self.id):
            raise ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        if max_players_per_team_reached(self.team, exclude=self.id):
            raise ValidationError(
                _("Équipe déjà remplie")
            )
        if not tournament_announced(self.team.get_tournament()):
            raise ValidationError(
                _("Tournoi non annoncé")
            )

    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        self.team.refresh_validation()


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
        "tournament.Team",
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


class Substitute(models.Model):
    """
    A Substitute is someone that can replace a player in a team.
    """

    user = models.ForeignKey(
        User,
        verbose_name=_("Utilisateur⋅ice"),
        on_delete=models.CASCADE,
    )
    team = models.ForeignKey(
        "tournament.Team",
        verbose_name=_("Équipe"),
        on_delete=models.CASCADE,
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
    name_in_game = models.CharField(
        max_length=42,
        validators=[MinLengthValidator(1)],
        null=False,
        blank=False,
        verbose_name=_("Pseudo en jeu"),
    )


    class Meta:
        """Meta Options"""

        verbose_name = _("Inscription d'un⋅e remplaçant⋅e")
        verbose_name_plural = _("Inscriptions de remplaçant⋅es")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "team"], name="not_twice_same_substitute"
            )
        ]

    def __str__(self) -> str:
        """Format this substitute registration as a str"""
        return f"(Substitute) {self.user.username} for {self.team}"

    def as_user(self) -> User:
        """Return the current player as a User object"""
        return self.user

    def get_team(self):
        """Return the Team object of the current team"""
        return self.team
    
    def get_name_in_game(self) -> str:
        """Return the name_in_game of the player"""
        return self.name_in_game

    def clean(self):
        """
        Assert that the user associated with the provided substitute does not already
        exist in any team of any tournament of the event
        """
        user = self.user
        event = self.get_team().get_tournament().get_event()
        if not unique_event_registration_validator(user,event, player=self.id):
            raise ValidationError(
                _("Utilisateur⋅rice déjà inscrit⋅e dans un tournoi de cet évènement")
            )
        if max_substitue_per_team_reached(self.team, exclude=self.id):
            raise ValidationError(
                _("Nombre maximum de remplaçants déjà atteint")
            )
        if not tournament_announced(self.team.get_tournament()):
            raise ValidationError(
                _("Tournoi non annoncé")
            )


class Caster(models.Model):
    
    name = models.CharField(
        max_length=42,
        null=False,
        blank=False,
        verbose_name=_("Nom du casteur")
    )
    image = models.FileField(
        verbose_name=_("Photo de profil"),
        blank=True,
        null=True,
        upload_to="profile-pictures",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp"])
        ],
    )
    tournament = models.ForeignKey(
        Tournament,
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    url = models.URLField(
        verbose_name=_("Lien twitch ou autre"),
        blank=True,
        null=True,
    )


def unique_event_registration_validator(user: User, event: Event, player = None, manager = None, substitute = None):
    """Validate a unique registration per event"""
    e_regs = Player.objects.filter(team__tournament__event=event,user=user).exclude(id=player).values("id").union(Manager.objects.filter(team__tournament__event=event, user=user).exclude(id=manager).values("id")).union(Substitute.objects.filter(team__tournament__event=event, user=user).exclude(id=substitute).values("id"))
    if len(e_regs) > 0:
        return False
    else:
        return True

def player_manager_user_unique_validator(user: User):
    """
    Validate that a user cannot be a player and manager of the same
    tournament
    """
    p_regs = {
        (obj.user, obj.team.tournament) for obj in Player.objects.filter(user=user)
    }
    m_regs = {
        (obj.user, obj.team.tournament) for obj in Manager.objects.filter(user=user)
    }
    s_regs = {
        (obj.user, obj.team.tournament) for obj in Substitute.objects.filter(user=user)
    }
    if len(m_regs.intersection(p_regs)) > 0:
        raise ValidationError(
            _("Utilisateur⋅rice déjà inscrit⋅e dans ce tournois (rôles distincts)")
        )
    
def max_players_per_team_reached(team: Team, exclude=None):
    """Validate the number of players in a team"""
    if len(team.get_players().exclude(id=exclude)) >= team.get_tournament().get_game().get_players_per_team():
        return True
    else:
        return False
    
def max_substitue_per_team_reached(team: Team, exclude=None):
    """Validate the number of sub in a team"""
    if len(team.get_substitutes().exclude(id=exclude)) >= team.get_tournament().get_game().get_substitute_players_per_team():
        return True
    else:
        return False
    
def tournament_announced(tournament: Tournament):
    """Validate if a tournament is announced"""
    if tournament.is_announced:
        return True
    else:
        return False

def tournament_registration_full(tournament: Tournament, exclude=None):
    """Validate if a tournament is full"""
    if tournament.get_validated_teams(exclude) >= tournament.get_maxTeam():
        return True
    else:
        return False
