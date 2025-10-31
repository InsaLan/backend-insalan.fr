"""Handling of the payment of a registration (player, substitute and manager)."""

import logging

from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from insalan.mailer import MailManager
from insalan.payment.models import Product, ProductCategory, Transaction
from insalan.payment.hooks import PaymentHooks, PaymentCallbackSystem
from insalan.tickets.models import Ticket
from insalan.tournament.models import Player, Manager, Substitute, PaymentStatus
from insalan.settings import EMAIL_AUTH
from insalan.user.models import User


logger = logging.getLogger("insalan.tournament.hooks")


class PaymentHandler(PaymentHooks):
    """Handler of the payment of a ticket/registration"""

    @staticmethod
    def fetch_registration(product: Product, user: User
                           ) -> tuple[Manager | Player | Substitute, bool, bool]:
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
            manager_registration = Manager.objects.filter(
                team__tournament=tourney,
                user=user,
                payment_status=PaymentStatus.NOT_PAID,
            )
            if len(manager_registration) > 1:
                raise RuntimeError(_("Plusieurs inscription manager à un même tournoi"))
            if len(manager_registration) == 0:
                raise RuntimeError(
                    _("Pas d'inscription à valider au paiement pour %(user)s").format(
                        user=user.username
                    )
                )
            return manager_registration[0], True, False
        if is_substitute:
            substitute_registration = Substitute.objects.filter(
                team__tournament=tourney,
                user=user,
                payment_status=PaymentStatus.NOT_PAID,
            )
            if len(substitute_registration) > 1:
                raise RuntimeError(
                    _("Plusieurs inscription remplaçant à un même tournoi")
                )
            if len(substitute_registration) == 0:
                raise RuntimeError(_("Aucune inscription remplaçant trouvée"))
            return substitute_registration[0], False, True
        player_registration = Player.objects.filter(
            team__tournament=tourney,
            user=user,
            payment_status=PaymentStatus.NOT_PAID,
        )
        if len(player_registration) > 1:
            raise RuntimeError(_("Plusieurs inscription joueur⋅euse à un même tournoi"))
        if len(player_registration) == 0:
            raise RuntimeError(_("Aucune inscription joueur⋅euse trouvée"))
        return player_registration[0], False, False

    @staticmethod
    def prepare_transaction(transaction: Transaction, product: Product, _count: int) -> bool:
        """See if you can actually buy this"""

        user_obj = transaction.payer
        assert user_obj is not None
        try:
            PaymentHandler.fetch_registration(product, user_obj)
        except RuntimeError:
            # Not gonna work out
            return False
        return True

    @staticmethod
    def payment_success(transaction: Transaction, product: Product, _count: int) -> None:
        """Handle success of the registration"""
        user_obj = transaction.payer
        assert user_obj is not None
        reg, is_manager, is_substitute = PaymentHandler.fetch_registration(product, user_obj)

        if is_manager:
            assert isinstance(reg, Manager)
            PaymentHandler.handle_manager_reg(reg)
        elif is_substitute:
            assert isinstance(reg, Substitute)
            PaymentHandler.handle_substitute_reg(reg)
        else:
            assert isinstance(reg, Player)
            PaymentHandler.handle_player_reg(reg)

    @staticmethod
    def handle_player_reg(reg: Player) -> None:
        """
        Handle validation of a Player registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user, tournament=reg.team.tournament)
        tick.save()

        reg.ticket = tick
        reg.save()

        # Send an email to the user
        mailer = MailManager.get_mailer(EMAIL_AUTH["contact"]["from"])
        assert mailer is not None
        mailer.send_ticket_mail(reg.user, tick)

    @staticmethod
    def handle_manager_reg(reg: Manager) -> None:
        """
        Handle validation of a Manager registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user, tournament=reg.team.tournament)
        tick.save()

        reg.ticket = tick
        reg.save()

        # Send an email to the user
        mailer = MailManager.get_mailer(EMAIL_AUTH["contact"]["from"])
        assert mailer is not None
        mailer.send_ticket_mail(reg.user, tick)

    @staticmethod
    def handle_substitute_reg(reg: Substitute) -> None:
        """
        Handle validation of a Substitute registration
        """
        reg.payment_status = PaymentStatus.PAID
        tick = Ticket.objects.create(user=reg.user, tournament=reg.team.tournament)
        tick.save()

        reg.ticket = tick
        reg.save()

        # Send an email to the user
        mailer = MailManager.get_mailer(EMAIL_AUTH["contact"]["from"])
        assert mailer is not None
        mailer.send_ticket_mail(reg.user, tick)

    @staticmethod
    def payment_failure(transaction: Transaction, product: Product, _count: int) -> None:
        """Handle the failure of a registration"""

        user_obj = transaction.payer
        assert user_obj is not None
        PaymentHandler.fetch_registration(product, user_obj)

        # Whatever happens, just delete the registration
        # reg.delete()

    @staticmethod
    def payment_refunded(transaction: Transaction, product: Product, _count: int) -> None:
        """Handle a refund of a registration"""

        # Find a registration that was ongoing for the user
        assoc_tourney = product.associated_tournament
        if assoc_tourney is None:
            raise RuntimeError(_("Tournoi associé à un produit acheté nul!"))

        is_manager = product.category == ProductCategory.REGISTRATION_MANAGER
        is_substitute = product.category == ProductCategory.REGISTRATION_SUBSTITUTE
        reg_list: QuerySet[Manager | Player | Substitute]
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


def payment_handler_register() -> None:
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
