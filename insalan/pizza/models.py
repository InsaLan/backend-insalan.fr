"""
This module contains the Django models for the pizza ordering system.

It includes the following models:
- Pizza: Represents a pizza with its name, price, ingredients, image, and availability.
- TimeSlot: Represents a time slot for ordering pizzas, including delivery time, end time, and maximum number of pizzas.
- Order: Represents a pizza order, including the user, time slot, pizzas, payment method, price, and delivery status.
"""
from typing import List

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField


class Pizza(models.Model):
    """
    Pizza model
    """
    class Meta:
        """Meta options"""

        verbose_name = _("Pizza")
        verbose_name_plural = _("Pizzas")

    id: int
    name: models.CharField = models.CharField(
        max_length=200, verbose_name=_("Nom de la pizza")
    )
    ingredients: models.CharField = ArrayField(
        models.CharField(max_length=200, verbose_name=_("Ingrédient")),
        verbose_name=_("Ingrédients"),
        blank=True,
        null=True,
    )
    allergens: models.CharField = ArrayField(
        models.CharField(max_length=200, verbose_name=_("Allergène")),
        verbose_name = _("Allergènes"),
        blank=True,
        null=True,
    )
    image: models.FileField = models.FileField(
        verbose_name=_("Image"),
        upload_to="pizzas",
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg", "webp"])
        ],
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.name}"

class TimeSlot(models.Model):
    """
    TimeSlot model
    """
    class Meta:
        """Meta options"""

        verbose_name = _("Créneau de commande")
        verbose_name_plural = _("Créneaux de commande")

    id: int
    delivery_time: models.DateTimeField = models.DateTimeField(
        verbose_name=_("Heure de livraison")
    )
    start: models.DateTimeField = models.DateTimeField(
        verbose_name=_("Début des commandes")
    )
    end: models.DateTimeField = models.DateTimeField(
        verbose_name=_("Fin des commandes")
    )
    pizza: models.ManyToManyField = models.ManyToManyField(
        "pizza.Pizza",
        verbose_name=_("Pizzas disponibles"),
        related_name="pizzas",
    )
    pizza_max: models.IntegerField = models.IntegerField(
        verbose_name=_("Nombre maximum de pizzas")
    )
    public: models.BooleanField = models.BooleanField(
        verbose_name=_("Créneau ouvert à tous"),
        default=True
    )
    ended: models.BooleanField = models.BooleanField(
        verbose_name=_("Créneau terminé"),
        default=False
    )
    player_price: models.FloatField = models.FloatField(
        verbose_name=_("Prix pour les joueurs")
    )
    staff_price: models.FloatField = models.FloatField(
        verbose_name=_("Prix pour les staffs")
    )
    external_price: models.FloatField = models.FloatField(
        verbose_name=_("Prix pour les externes")
    )

    player_product: models.ForeignKey = models.ForeignKey(
        "payment.Product",
        related_name="player_pizza_product_reference",
        null=True,
        blank=True,
        verbose_name=_("Produit pour les joueurs"),
        on_delete=models.SET_NULL,
    )
    staff_product: models.ForeignKey = models.ForeignKey(
        "payment.Product",
        related_name="staff_pizza_product_reference",
        null=True,
        blank=True,
        verbose_name=_("Produit pour les staffs"),
        on_delete=models.SET_NULL,
    )
    external_product: models.ForeignKey = models.ForeignKey(
        "payment.Product",
        related_name="external_pizza_product_reference",
        null=True,
        blank=True,
        verbose_name=_("Produit pour les externes"),
        on_delete=models.SET_NULL,
    )

    def __str__(self) -> str:
        return f"{self.delivery_time}"

    def save(self, *args, **kwargs):

        # pylint: disable=import-outside-toplevel
        from insalan.payment.models import Product, ProductCategory

        super().save(*args, **kwargs)  # Get the self accessible to the products

        need_save = False

        if not self.player_product:
            self.player_product = Product.objects.create(
                name=_(f"Pizza {self.delivery_time} - Joueurs"),
                price=self.player_price,
                desc=_(f"Pizza {self.delivery_time} - Joueurs"),
                category=ProductCategory.PIZZA,
                associated_timeslot=self,
                available_from=self.start,
                available_until=self.end,
            )
            need_save = True

        self.player_product.available_from = self.start
        self.player_product.available_until = self.end
        self.player_product.save()

        if not self.staff_product:
            self.staff_product = Product.objects.create(
                name=_(f"Pizza {self.delivery_time} - Staffs"),
                price=self.staff_price,
                desc=_(f"Pizza {self.delivery_time} - Staffs"),
                category=ProductCategory.PIZZA,
                associated_timeslot=self,
                available_from=self.start,
                available_until=self.end,
            )
            need_save = True

        self.staff_product.available_from = self.start
        self.staff_product.available_until = self.end
        self.staff_product.save()

        if not self.external_product:
            self.external_product = Product.objects.create(
                name=_(f"Pizza {self.delivery_time} - Externes"),
                price=self.external_price,
                desc=_(f"Pizza {self.delivery_time} - Externes"),
                category=ProductCategory.PIZZA,
                associated_timeslot=self,
                available_from=self.start,
                available_until=self.end,
            )
            need_save = True


        self.external_product.available_from = self.start
        self.external_product.available_until = self.end
        self.external_product.save()

        if need_save:
            self.save()

    def get_orders_id(self) -> List[int]:
        """
        retrieve orders associated to a timeslot with their id
        """
        return Order.objects.filter(time_slot=self).values_list("id", flat=True)

class PizzaOrder(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    pizza = models.ForeignKey('pizza.Pizza', on_delete=models.CASCADE)


class Order(models.Model):
    """
    Order model
    """
    class Meta:
        """Meta options"""

        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")

    id: int
    user: models.CharField = models.CharField(
        verbose_name=_("Utilisateur"),
        max_length=200,
        blank=True,
    )
    user_obj: models.ForeignKey = models.ForeignKey(
        "user.user",
        verbose_name=_("Utilisateur du site"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    time_slot: models.ForeignKey = models.ForeignKey(
        "pizza.TimeSlot",
        verbose_name=_("Créneau de commande"),
        on_delete=models.CASCADE,
    )
    pizza: models.ManyToManyField = models.ManyToManyField(
        "pizza.Pizza",
        verbose_name=_("Pizzas commandées"),
        related_name="pizza_order",
        through='PizzaOrder',
    )
    payment_method: models.CharField = models.CharField(
        verbose_name=_("Moyen de paiement"),
        max_length=2,
        choices=[
            ("CA", _("Carte")),
            ("CH", _("Chèque")),
            ("ES", _("Espèces")),
            ("LI", _("Lyfpay")),
        ],
        default="CA",
    )
    price: models.FloatField = models.FloatField(verbose_name=_("Prix"))
    paid: models.BooleanField = models.BooleanField(
        verbose_name=_("Payé"),
        default=False
    )
    delivered: models.BooleanField = models.BooleanField(
        verbose_name=_("Livrée"),
        default=False
    )
    delivery_date: models.DateField = models.DateField(
        verbose_name=_("Date de livraison"),
        default=timezone.now,
    )
    created_at: models.DateTimeField = models.DateTimeField(
        verbose_name=_("Date de création"),
        auto_now_add=True,
    )

    def get_pizza_ids(self) -> List[int]:
        """
        retrieve pizza associated to an order with their id
        """
        return PizzaOrder.objects.filter(order=self)
    def __str__(self) -> str:
        return f"{self.user} - {self.time_slot}"

    def get_username(self) -> str:
        """
        return the username of the user
        """
        if self.user_obj:
            return self.user_obj.username
        return self.user
    get_username.short_description = _('Utilisateur')