"""Handling of the payment of a registration (player and manager)"""

import logging

from django.utils.translation import gettext_lazy as _

from insalan.payment.models import ProductCategory
from insalan.payment.hooks import PaymentHooks, PaymentCallbackSystem
from insalan.tickets.models import Ticket
from insalan.tournament.models import Player, Manager, Substitute, PaymentStatus


logger = logging.getLogger("insalan.tournament.hooks")


class PaymentHandler(PaymentHooks):
    """Handler of the payment of a ticket/registration"""

    @staticmethod
    def fetch_registration(product, user):
        """
        Fetch a registration for a user and product.

        Returns a tuple (reg, is_manager, is_substitute), which is pretty explicit. Raises
        RuntimeError otherwise.
        """
        # Is there even a tournament?
        tourney = product.associated_tournament
        if tourney is None:
            raise RuntimeError(_("Aucun tournoi associé"))

        is_manager = product.category == ProductCategory.REGISTRATION_MANAGER
        is_substitute = product.category == ProductCategory.REGISTRATION_SUBSTITUTE
        # Find a registration on that user within the tournament

        if is_manager:
            reg = Manager.objects.filter(
                team__tournament=tourney,
                user=user,
                payment_status=PaymentStatus.NOT_PAID,
            )
            if len(reg) > 1:
                raise RuntimeError(_("Plusieurs inscription manager à un même tournoi"))
            if len(reg) == 0:
                raise RuntimeError(
                    _("Pas d'inscription à valider au paiement pour %(user)s").format(
                        user=user.username
                    )
                )
            return (reg[0], True, False)
        if is_substitute:
            reg = Substitute.objects.filter(
                team__tournament=tourney,
                user=user,
                payment_status=PaymentStatus.NOT_PAID,
            )
            if len(reg) > 1:
                raise RuntimeError(
                    _("Plusieurs inscription remplaçant à un même tournoi")
                )
            if len(reg) == 0:
                raise RuntimeError(_("Aucune inscription remplaçant trouvée"))
            return (reg[0], False, True)
        reg = Player.objects.filter(
            team__tournament=tourney,
            user=user,
            payment_status=PaymentStatus.NOT_PAID,
        )
        if len(reg) > 1:
            raise RuntimeError(
                _("Plusieurs inscription joueur⋅euse à un même tournoi")
            )
        if len(reg) == 0:
            raise RuntimeError(_("Aucune inscription joueur⋅euse trouvée"))
        return (reg[0], False, False)

    @staticmethod
    def prepare_transaction(transaction, product, _count) -> bool:
        """See if you can actually buy this"""

        user_obj = transaction.payer
        try:
            PaymentHandler.fetch_registration(product, user_obj)
        except RuntimeError:
            # Not gonna work out
            return False
        return True

    @staticmethod
    def payment_success(transaction, product, _count):
        """Handle success of the registration"""

        user_obj = transaction.payer
        (reg, is_manager, is_substitute) = PaymentHandler.fetch_registration(product, user_obj)

        if is_manager:
            PaymentHandler.handle_player_reg(reg)
        elif is_substitute:
            PaymentHandler.handle_manager_reg(reg)
        else:
            PaymentHandler.handle_manager_reg(reg)

    @staticmethod
    def handle_player_reg(reg: Player):
        """
        Handle validation of a Player registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user, tournament=reg.team.tournament)
        tick.save()

        reg.ticket = tick
        reg.save()

    @staticmethod
    def handle_manager_reg(reg: Manager):
        """
        Handle validation of a Manager registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user, tournament=reg.team.tournament)
        tick.save()

        reg.ticket = tick
        reg.save()

    @staticmethod
    def handle_substitute_reg(reg: Substitute):
        """
        Handle validation of a Substitute registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user, tournament=reg.team.tournament)
        tick.save()

        reg.ticket = tick
        reg.save()

    @staticmethod
    def payment_failure(transaction, product, _count):
        """Handle the failure of a registration"""

        user_obj = transaction.payer
        PaymentHandler.fetch_registration(product, user_obj)

        # Whatever happens, just delete the registration
        # reg.delete()

    @staticmethod
    def payment_refunded(transaction, product, _count):
        """Handle a refund of a registration"""

        # Find a registration that was ongoing for the user
        assoc_tourney = product.associated_tournament
        if assoc_tourney is None:
            raise RuntimeError(_("Tournoi associé à un produit acheté nul!"))

        is_manager = product.category == ProductCategory.REGISTRATION_MANAGER
        is_substitute = product.category == ProductCategory.REGISTRATION_SUBSTITUTE
        if is_manager:
            reg_list = Manager.objects.filter(
                user=transaction.payer, team__tournament=assoc_tourney
            )
        elif is_substitute:
            reg_list = Substitute.objects.filter(
                user=transaction.payer, team__tournament=assoc_tourney
            )
        else:
            reg_list = Player.objects.filter(
                user=transaction.payer, team__tournament=assoc_tourney
            )

        if len(reg_list) == 0:
            logger.warning(
                _(f"Aucune inscription à détruire trouvée pour le refund de {transaction.id}")
            )
            return

        reg = reg_list[0]
        team = reg.team
        ticket = reg.ticket
        reg.delete()

        team.refresh_validation()

        if ticket is not None:
            ticket.status = Ticket.Status.CANCELLED
            ticket.save()


def payment_handler_register():
    """Register the callbacks"""
    PaymentCallbackSystem.register_handler(
        ProductCategory.REGISTRATION_PLAYER, PaymentHandler, overwrite=True
    )
    PaymentCallbackSystem.register_handler(
        ProductCategory.REGISTRATION_MANAGER, PaymentHandler, overwrite=True
    )
    PaymentCallbackSystem.register_handler(
        ProductCategory.REGISTRATION_SUBSTITUTE, PaymentHandler, overwrite=True
    )
