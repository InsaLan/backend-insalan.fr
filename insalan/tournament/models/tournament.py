from __future__ import annotations

from datetime import datetime, timedelta
from math import ceil
from typing import Any, cast, TYPE_CHECKING

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.core.validators import (
    FileExtensionValidator,
    MinValueValidator,
    MinLengthValidator,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
# No stubs are available for django-polymorphic
# https://github.com/jazzband/django-polymorphic/issues/579
from polymorphic.models import PolymorphicModel  # type: ignore

from insalan.components.image_field import ImageField

from . import team, caster, group, bracket, swiss, payement_status as ps

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from django_stubs_ext import ValuesQuerySet

    from .bracket import Bracket
    from .caster import Caster
    from .event import Event
    from .game import Game
    from .group import Group
    from .swiss import SwissRound
    from .team import Team


def in_thirty_days() -> datetime:
    """Return now + 30 days"""
    return timezone.now() + timedelta(days=30)


# Ignore type error because django-polymorphic doesn't have types stubs.
class BaseTournament(PolymorphicModel):  # type: ignore[misc]
    """
    Base class for a Tournament. Contains the common fields between a Tournament.
    """
    game = models.ForeignKey("Game", verbose_name=_("Jeu"), on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name=_("Nom du tournoi"),
        validators=[MinLengthValidator(3)],
        max_length=512,
    )
    rules = models.TextField(
        verbose_name=_("Règlement du tournoi"),
        max_length=50000,
        null=False,
        blank=True,
        default="",
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
    max_team_thresholds = ArrayField(
        models.IntegerField(validators=[MinValueValidator(1)]),
        default=list,
        verbose_name=_("Seuils du nombre d'équipes"),
        help_text=_("Liste croissante de seuils (ex: [24, 32, 40])"),
    )
    current_threshold_index = models.IntegerField(
        default=0,
        verbose_name=_("Index du seuil actuel"),
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

    # The teams field is defined in the tournament field in the Team model as
    # realated name but mypy doesn't detect it.
    teams: RelatedManager[Team]

    class Meta:
        """Meta options"""

        indexes = [
            models.Index(fields=["game"]),
        ]

    def __str__(self) -> str:
        """Format this Tournament to a str"""
        return f"{self.name}"

    def get_name(self) -> str:
        """Get the name of the tournament"""
        return self.name

    def get_game(self) -> "Game":
        """Get the game of a tournament"""
        return self.game

    def get_teams(self) -> QuerySet[Team]:
        """Return the list of Teams in that Tournament"""
        return self.teams.all()

    def get_teams_id(self) -> ValuesQuerySet[Team, int]:
        """Return the list of identifiers of this Tournament's Teams"""
        return self.get_teams().values_list("id", flat=True)

    def get_rules(self) -> str:
        """Return the raw tournament rules"""
        return self.rules

    def get_max_team(self) -> int:
        """Retourne la limite actuelle basée sur le seuil actif"""
        if not self.max_team_thresholds:
            return 0
        return self.max_team_thresholds[self.current_threshold_index]

    def get_next_threshold(self) -> int | None:
        """Retourne le prochain seuil ou None si on est au maximum"""
        if self.current_threshold_index + 1 < len(self.max_team_thresholds):
            return self.max_team_thresholds[self.current_threshold_index + 1]
        return None

    def can_expand_threshold(self) -> bool:
        """Vérifie si on peut passer au seuil suivant"""
        next_threshold = self.get_next_threshold()
        if next_threshold is None:
            return False

        validated_count = self.get_validated_teams()
        potential_teams = self.get_teams_ready_for_validation()

        # We can expand if the sum of validated teams and teams ready for validation
        # is greater than or equal to the next threshold
        return (validated_count + potential_teams) >= next_threshold

    def get_teams_ready_for_validation(self) -> int:
        """
        Compte les équipes non-validées mais qui pourraient l'être
        (ont suffisamment de joueurs payés)
        """
        teams = self.teams.filter(validated=False)
        count = 0

        for tm in teams:
            if self.team_meets_validation_criteria(tm):
                count += 1

        return count

    # /!\ This method need to be in the Tournament model because
    # if it's in the Team model, the polymorphic behavior is
    # not working properly and the isinstance checks fail /!\
    # took a few time to figure that out :(
    def team_meets_validation_criteria(self, tm: Team) -> bool:
        """Vérifie si une équipe remplit les critères de validation"""
        # An EventTournament team is validated if ceil((n+1)/2) players have paid
        if isinstance(self, EventTournament):
            players = tm.get_players()
            game = self.get_game()
            threshold = ceil((game.get_players_per_team() + 1) / 2)
            paid_seats = players.filter(payment_status=ps.PaymentStatus.PAID).count()
            return paid_seats >= threshold
        # A PrivateTournament team is validated if the team is full
        if isinstance(self, PrivateTournament):
            players = tm.get_players()
            game = self.get_game()
            return players.count() == game.get_players_per_team()
        return False

    def validate_eligible_teams(self) -> int:
        """
        Valide toutes les équipes éligibles qui ne sont pas encore validées.
        Retourne le nombre d'équipes nouvellement validées.
        """
        newly_validated = 0
        validated_count = self.get_validated_teams()
        current_max = self.get_max_team()

        # Get all non-validated teams
        teams_to_check = self.teams.filter(validated=False).select_related('tournament')

        for tm in teams_to_check:
            # Stop if we've reached the current max
            if validated_count >= current_max:
                break

            # Validate the team if it meets the criteria
            if self.team_meets_validation_criteria(tm):
                tm.validated = True
                tm.save(update_fields=['validated'])
                validated_count += 1
                newly_validated += 1

        return newly_validated

    def try_expand_threshold(self) -> bool:
        """Tente d'étendre au seuil suivant. Retourne True si étendu."""
        if self.can_expand_threshold():
            self.current_threshold_index += 1
            self.save(update_fields=['current_threshold_index'])

            # when we expand, we need to validate eligible teams
            self.validate_eligible_teams()

            # Check again if we can expand further
            # (in case many teams were eligible)
            return self.try_expand_threshold() or True

        return False

    def get_validated_teams(self, exclude: int | None = None) -> int:
        """Return the number of validated teams"""
        return len(team.Team.objects.filter(tournament=self, validated=True).exclude(id=exclude))

    def get_groups(self) -> QuerySet[Group]:
        return group.Group.objects.filter(tournament=self)

    def get_groups_id(self) -> ValuesQuerySet[Group, int]:
        return group.Group.objects.filter(tournament=self).values_list("id",flat=True)

    def get_brackets(self) -> QuerySet[Bracket]:
        return bracket.Bracket.objects.filter(tournament=self)

    def get_brackets_id(self) -> ValuesQuerySet[Bracket, int]:
        return bracket.Bracket.objects.filter(tournament=self).values_list("id",flat=True)

    def get_swiss_rounds_id(self) -> ValuesQuerySet[SwissRound, int]:
        return swiss.SwissRound.objects.filter(tournament=self).values_list("id",flat=True)

    def update_name_in_game(self) -> None:
        """Update all name_in_game of players and substitutes in the tournament"""
        for team_obj in self.get_teams():
            for player in team_obj.get_players():
                player.update_name_in_game()
            for substitute in team_obj.get_substitutes():
                substitute.update_name_in_game()

class PrivateTournament(BaseTournament):
    """
    A private Tournament without paid registration.
    """

    objects: Manager[PrivateTournament]

    # No need to use a password field here, as it would add unnecessary complexity
    password = models.CharField(
        verbose_name=_("Mot de passe"),
        max_length=512,
        validators=[MinLengthValidator(3)],
        blank=True,
        null=False,
    )
    running = models.BooleanField(
        verbose_name=_("En cours"),
        default=True,
        null=False,
    )
    start = models.DateTimeField(
        verbose_name=_("Début du tournoi"),
        default=timezone.now,
        null=False,
    )
    rewards = models.TextField(
        verbose_name=_("Récompenses du tournois"),
        max_length=50000,
        null=False,
        blank=True,
        default="",
    )

    class Meta:
        """Meta options"""

        verbose_name = _("Tournoi privé")
        verbose_name_plural = _("Tournois privés")


class EventTournament(BaseTournament):
    """
    A Tournament happening during an event that Teams of players register for.
    """

    objects: Manager[EventTournament]

    event = models.ForeignKey(
        "Event", verbose_name=_("Évènement"), on_delete=models.CASCADE
    )
    is_announced = models.BooleanField(verbose_name=_("Annoncé"), default=False)
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
    planning_file = models.FileField(
        verbose_name=_("Fichier ICS du planning"),
        blank=True,
        null=True,
        upload_to="tournament-planning",
        validators=[FileExtensionValidator(allowed_extensions=["ics"])],
    )

    class Meta:
        """Meta options"""

        verbose_name = _("Tournoi")
        verbose_name_plural = _("Tournois")
        indexes = [
            models.Index(fields=["event"]),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
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
                name=cast(str, _(f"Place {self.name} Joueur en ligne - {self.event.name}")),
                desc=cast(str, _(f"Inscription au tournoi {self.name} joueur")),
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
                name=cast(str, _(f"Place {self.name} manager en ligne - {self.event.name}")),
                desc=cast(str, _(f"Inscription au tournoi {self.name} manager")),
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
                name=cast(str, _(f"Place {self.name} remplaçant en ligne - {self.event.name}")),
                desc=cast(str, _(f"Inscription au tournoi {self.name} remplaçant")),
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

    def get_event(self) -> Event:
        """Get the event of a tournament"""
        return self.event

    def get_casters(self) -> QuerySet[Caster]:
        """Return the list of casters for this tournament"""
        return caster.Caster.objects.filter(tournament=self)
