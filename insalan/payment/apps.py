"""
This module contains the configuration for the Payment app.

It defines the PaymentConfig class, which is responsible for configuring the app.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentConfig(AppConfig):
    """
    App configuration
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name ='insalan.payment'
    verbose_name = _('Paiement')
