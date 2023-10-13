import json
import requests
from os import getenv
import logging
logger = logging.getLogger(__name__)
class Tokens :
    instance=None
    def __init__(self):
        if Tokens.instance is None:
            Tokens.instance = self
        logger.debug(getenv("HELLOASSO_ENDPOINT"))
        request = requests.post(
                url=f"{getenv('HELLOASSO_ENDPOINT')}/oauth2/token",
            headers={'Content-Type': "application/x-www-form-urlencoded"},
            data={
                'client_id': getenv("HELLOASSO_CLIENTID"),
                'client_secret': getenv("HELLOASSO_CLIENT_SECRET"),
                'grant_type': "client_credentials",
            },
        )
        logger.debug(request.text)
        self.bearer_token = request.json["access_token"]
        self.refresh_token = request.json["refresh_token"]

    def get_token(self):
        return self.bearer_token

    def refresh(self):
        request = requests.post(
            url=f"{getenv('HELLOASSO_ENDPOINT')}/oauth2/token",
            headers={'Content-Type': "application/x-www-form-urlencoded"},
            data={
                'client_id': getenv("CLIENT_ID"),
                'client_secret': self.refresh_token,
                'grant_type': "refresh_token",
            },
        )
        self.bearer_token=request.json["access_token"]
        self.refresh_token=request.json["refresh_token"]
