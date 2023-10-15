"""Module that helps retrieve a OAuth2 token from HelloAsso"""
import logging

from os import getenv

import requests

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
        logger.debug(getenv("HELLOASSO_ENDPOINT"))
        request = requests.post(
            url=f"{getenv('HELLOASSO_ENDPOINT')}/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": getenv("HELLOASSO_CLIENTID"),
                "client_secret": getenv("HELLOASSO_CLIENT_SECRET"),
                "grant_type": "client_credentials",
            },
        )
        logger.debug(request.text)
        self.bearer_token = request.json()["access_token"]
        self.refresh_token = request.json()["refresh_token"]

    def get_token(self):
        """Return the singleton's token"""
        return self.bearer_token

    def refresh(self):
        """Refresh our HelloAsso token"""
        request = requests.post(
            url=f"{getenv('HELLOASSO_ENDPOINT')}/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": getenv("CLIENT_ID"),
                "client_secret": self.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        self.bearer_token = request.json()["access_token"]
        self.refresh_token = request.json()["refresh_token"]
