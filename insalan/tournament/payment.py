"""Handling of the payment of a registration (player and manager)"""

from insalan.payment.models import ProductCategory
from insalan.payment.hooks import PaymentHooks, PaymentCallbackSystem

from django.utils.translation import gettext_lazy as _

from insalan.tickets.models import Ticket
from insalan.tournament.models import Player, Manager, PaymentStatus


class PaymentHandler(PaymentHooks):
    """Handler of the payment of a ticket/registration"""

    @staticmethod
    def fetch_registration(tourney, user):
        """
        Fetch a registration for a user in a tournament.

        Returns a tuple (reg, is_manager), which is pretty explicit.
        """
        # Find a registration on that user within the tournament
        # Could they be player?
        reg = Player.objects.filter(
            team__tournament=tourney, user=user, payment_status=PaymentStatus.NOT_PAID
        )
        if len(reg) > 1:
            raise RuntimeError(_("Plusieurs inscription joueur⋅euse à un même tournoi"))
        if len(reg) == 1:
            return (reg[0], False)

        reg = Manager.objects.filter(
            team__tournament=tourney, user=user, payment_status=PaymentStatus.NOT_PAID
        )
        if len(reg) > 1:
            raise RuntimeError(_("Plusieurs inscription manager à un même tournoi"))
        if len(reg) == 0:
            raise RuntimeError(
                _(f"Pas d'inscription à valider au paiement pour {user}")
            )
        return (reg[0], True)

    @staticmethod
    def payment_success(transaction, product, _count):
        """Handle success of the registration"""

        assoc_tourney = product.associated_tournament
        if assoc_tourney is None:
            raise RuntimeError(_("Tournoi associé à un produit acheté nul!"))

        user_obj = transaction.payer
        (reg, is_manager) = PaymentHandler.fetch_registration(assoc_tourney, user_obj)

        if is_manager:
            PaymentHandler.handle_player_reg(reg)
        else:
            PaymentHandler.handle_manager_reg(reg)

    @staticmethod
    def handle_player_reg(reg: Player):
        """
        Handle validation of a Player registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user)
        tick.save()

        reg.ticket = tick
        reg.save()

    @staticmethod
    def handle_manager_reg(reg: Manager):
        """
        Handle validation of a Manager registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user)
        tick.save()

        reg.ticket = tick
        reg.save()

    @staticmethod
    def payment_failure(transaction, product, _count):
        """Handle the failure of a registration"""

        # Find a registration that was ongoing for the user
        assoc_tourney = product.associated_tournament
        if assoc_tourney is None:
            raise RuntimeError(_("Tournoi associé à un produit acheté nul!"))

        user_obj = transaction.payer
        (reg, _is_manager) = PaymentHandler.fetch_registration(assoc_tourney, user_obj)

        # Whatever happens, just delete the registration
        reg.delete()

def payment_handler_register():
    """Register the callbacks"""
    PaymentCallbackSystem.register_handler(
        ProductCategory.REGISTRATION_PLAYER, PaymentHandler,
        overwrite = True
    )
    PaymentCallbackSystem.register_handler(
        ProductCategory.REGISTRATION_MANAGER, PaymentHandler,
        overwrite = True
    )
