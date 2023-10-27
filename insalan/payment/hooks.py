"""
Hooks module for payment

This file is not part of the Django rest framework. Rather, it is a component
designed for other components of the application to come and register custom
handlers for payment success or failure.
"""

import logging

from django.utils.translation import gettext_lazy as _

from .models import ProductCategory


class PaymentCallbackSystem:
    """
    Interface to register your hooks with, and get them
    """

    # The dictionary of hooks
    __HOOKS = {}
    __logger = logging.getLogger("insalan.payment.hooks.PaymentCallbackSystem")

    @classmethod
    def register_handler(cls, prodcat, handler, overwrite=False):
        """
        Register a handler for a product category

        You give it a product (any instance of
        `payment.models.ProductCategory`), and a handler (any subclass of
        `payment.hooks.PaymentHooks`).

        Overwriting an existing hook will trigger an error, unless you set
        `overwrite=False`.
        """

        # Verify arguments
        # 1. product is an instance of Product
        if not isinstance(prodcat, ProductCategory):
            raise ValueError(_("Produit qui n'est pas une instance de Produit"))

        if not issubclass(handler, PaymentHooks):
            raise ValueError(_("Descripteur qui ne dérive pas de PaymentHooks"))

        if cls.__HOOKS.get(prodcat):
            if overwrite:
                cls.__logger.warning(
                    "Overwriting handler for product category %s", prodcat
                )
            else:
                raise ValueError(_(f"Descripteur déjà défini pour {prodcat}"))
        cls.__HOOKS[prodcat] = handler

    @classmethod
    def retrieve_handler(cls, prodcat):
        """
        Retrieve a handler class for a product category

        If a handler is not registered, returns None
        """
        return cls.__HOOKS.get(prodcat)


# Base class/interface
class PaymentHooks:
    """
    Payment Hooks Class

    This is a base class that must be derived by all hooks implementers, who
    will then implement their way of handling payment success and failure.
    """

    @staticmethod
    def prepare_transaction(_transaction, _product, _count) -> bool:
        """
        Prepare things that may have to be created prior to payment

        Arguments are the preliminary transaction, product and count.
        This hook is ran by the payment view exactly right before forwarding the
        user to HelloAsso.
        """

    @staticmethod
    def payment_success(_transaction, _product, _count):
        """
        Payment Success Handler

        This method handles the process of validating a transaction, with the
        transaction object, product and count given.
        By that point, you can safely assume that the payment succeeded, and
        that the `.payment_status` field of the transaction is set to
        `SUCCEEDED`.
        """

    @staticmethod
    def payment_failure(_transaction, _product, _count):
        """
        Payment Failure Handler

        This method handles the process of cleaning up after a failed
        transaction. By this point you can safely assume that the payment failed
        and that `.payment_status` on the transaction object is set to `FAILED`.
        """

    @staticmethod
    def payment_refunded(_transaction, _product, _count):
        """
        Payment Refund Handler

        This method handles the process of cleaning up after a refund of a
        transaction. By this point, you can safely assume that the payment has
        been refunded on the side of helloasso.
        """


# vim: set tw=80:
