from datetime import timedelta

from typing import List
from django.db import models
from django.core.validators import (
    FileExtensionValidator,
    MinValueValidator,
    MinLengthValidator,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField

from insalan.components.image_field import ImageField
from . import team, caster, group, bracket, swiss

def in_thirty_days():
    """Return now + 30 days"""
    return timezone.now() + timedelta(days=30)

class Tournament(models.Model):
    """
    A Tournament happening during an event that Teams of players register for.
    """

    event = models.ForeignKey(
        "Event", verbose_name=_("Évènement"), on_delete=models.CASCADE
    )
    game = models.ForeignKey("Game", verbose_name=_("Jeu"), on_delete=models.CASCADE)
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
    logo: models.FileField = ImageField(
        verbose_name=_("Logo"),
        blank=True,
        null=True,
        upload_to="tournament-icons",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp", "avif"])
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
    description_bottom = models.CharField(
        null=False,
        blank=True,
        default='',
        verbose_name=_("Description du tournoi en bas de page"),
        max_length=300,
    )
    planning = models.CharField(
        null=False,
        blank=True,
        default='',
        verbose_name=_("Nom du content du planning du tournoi"),
        max_length=300,
    )

    class Meta:
        """Meta options"""

        verbose_name = _("Tournoi")
        verbose_name_plural = _("Tournois")
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["game"]),
        ]

    def save(self, *args, **kwargs):
        """
        Override default save of Tournament.
        When a Tournament object is created, it creates 2 products, its associated
        products to allow players and managers to pay the entry fee
        """

        # pylint: disable=import-outside-toplevel
        from insalan.payment.models import Product, ProductCategory

        super().save(*args, **kwargs)  # Get the self accessible to the products

        need_save = False

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

    def get_event(self) -> "Event":
        """Get the event of a tournament"""
        return self.event

    def get_game(self) -> "Game":
        """Get the game of a tournament"""
        return self.game

    def get_teams(self) -> List["Team"]:
        """Return the list of Teams in that Tournament"""
        return team.Team.objects.filter(tournament=self)

    def get_teams_id(self) -> List[int]:
        """Return the list of identifiers of this Tournament's Teams"""
        return self.get_teams().values_list("id", flat=True)

    def get_rules(self) -> str:
        """Return the raw tournament rules"""
        return self.rules

    def get_max_team(self) -> int:
        """Return the max number of teams"""
        return self.maxTeam

    def get_validated_teams(self, exclude=None) -> int:
        """Return the number of validated teams"""
        return len(team.Team.objects.filter(tournament=self,validated=True).exclude(id=exclude))

    def get_casters(self) -> List["Caster"]:
        """Return the list of casters for this tournament"""
        return caster.Caster.objects.filter(tournament=self)

    def get_groups(self) -> List["Group"]:
        return group.Group.objects.filter(tournament=self)

    def get_groups_id(self) -> List[int]:
        return group.Group.objects.filter(tournament=self).values_list("id",flat=True)

    def get_brackets(self) -> List["Bracket"]:
        return bracket.Bracket.objects.filter(tournament=self)

    def get_brackets_id(self) -> List[int]:
        return bracket.Bracket.objects.filter(tournament=self).values_list("id",flat=True)

    def get_swissRounds(self) -> List["SwissRound"]:
        return swiss.SwissRound.objects.filter(tournament=self)

    def get_swissRounds_id(self) -> List[int]:
        return swiss.SwissRound.objects.filter(tournament=self).values_list("id",flat=True)
