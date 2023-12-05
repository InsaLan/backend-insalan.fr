"""Module that helps retrieve a OAuth2 token from HelloAsso"""
import logging
import time

import requests

from django.utils.translation import gettext_lazy as _

import insalan.settings as app_settings

logger = logging.getLogger(__name__)


class Token:
    """
    HelloAsso OAuth2 Token Singleton

    This class simply holds the token as a singleton, and is used to refresh it
    when needed.
    """

    instance = None

    def __init__(self):
        """Initialize the Token retrieval instance"""
        if Token.instance is None:
            Token.instance = self

        self.expiration_date = None
        self.bearer_token = None
        self.refresh_token = None

        self.obtain_token()

    @classmethod
    def get_instance(cls):
        """Get the potential singleinstance of the Token"""
        if cls.instance is None:
            token = cls()
            return token

        return cls.instance

    def obtain_token(self, secret=None):
        """
        Obtain a token, either from the original secret, or from the previous
        refresh token
        """
        if secret is None:
            c_secret = app_settings.HA_OAUTH_CLIENT_SECRET
            grant_type = "client_credentials"
            data = {
                "client_id": app_settings.HA_OAUTH_CLIENT_ID,
                "client_secret": c_secret,
                "grant_type": grant_type,
            }
        else:
            refresh_token = secret
            grant_type = "refresh_token"
            data = {
                "client_id": app_settings.HA_OAUTH_CLIENT_ID,
                "grant_type": grant_type,
                "refresh_token": refresh_token,
            }
        try:
            request = requests.post(
                url=f"{app_settings.HA_URL}/oauth2/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            )
        except requests.exceptions.RequestException as err:
            logger.error("Unable to obtain token: %s", err)
            # Clean everything
            Token.instance = None
            self.expiration_date = None
            self.bearer_token = None
            self.refresh_token = None
            # Propagate errors
            raise RuntimeError(
                _("Impossible de rafraîchir le jeton HelloAsso")
            ) from err

        result = request.json()
        if "error" in result:
            raise RuntimeError(_("Impossible de rafraichir le jeton HelloAsso: %s") % result["error_description"])

        self.assign_token_data(request.json())

    def assign_token_data(self, data):
        """Assign data from the json body"""
        # Store our tokens, but also keep track of the refresh time
        self.expiration_date = time.time() + int(data["expires_in"])
        self.bearer_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def get_token(self):
        """Return the singleton's token"""
        # Should we refresh?
        if time.time() >= self.expiration_date:
            self.refresh()
        return self.bearer_token

    def refresh(self):
        """Refresh our HelloAsso token"""
        self.obtain_token(secret=self.refresh_token)
