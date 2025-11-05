"""Module that helps retrieve a OAuth2 token from HelloAsso"""

from __future__ import annotations

import logging
import time
from typing import Any

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

    def __init__(self) -> None:
        """Initialize the Token retrieval instance"""
        if Token.instance is None:
            Token.instance = self

        self.expiration_date: float | None = None
        self.bearer_token: str | None = None
        self.refresh_token: str | None = None

        self.obtain_token()

    @classmethod
    def get_instance(cls) -> Token:
        """Get the potential singleinstance of the Token"""
        if cls.instance is None:
            token = cls()
            return token

        return cls.instance

    def obtain_token(self, secret: str | None = None) -> None:
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
                timeout=45,
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

        if request.status_code != 200:
            raise RuntimeError(
                _("Impossible de rafraîchir le jeton HelloAsso: %s")
                % request.text
            )
        result = request.json()
        if "error" in result:
            raise RuntimeError(
                _("Impossible de rafraichir le jeton HelloAsso: %s") % result["error_description"]
            )

        self.assign_token_data(request.json())

    def assign_token_data(self, data: Any) -> None:
        """Assign data from the json body"""
        # Store our tokens, but also keep track of the refresh time
        self.expiration_date = time.time() + int(data["expires_in"])
        self.bearer_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def get_token(self) -> str:
        """Return the singleton's token"""
        # Should we refresh?
        assert self.expiration_date is not None
        if time.time() >= self.expiration_date:
            self.refresh()
        assert self.bearer_token is not None
        return self.bearer_token

    def refresh(self) -> None:
        """Refresh our HelloAsso token"""
        self.obtain_token(secret=self.refresh_token)
