import json
import requests
from os import getenv


class tokens :
    instance=None
    def __init__(self):
        if tokens.instance is None:
            tokens.instance = self
        request = requests.post(
            url="https://api.helloasso-sandbox.com/oauth2/token",
            headers={'Content-Type': "application/x-www-form-urlencoded"},
            data={
                'client_id': getenv("CLIENT_ID"),
                'client_secret': getenv("CLIENT_SECRET"),
                'grant_type': "client_credentials",
            },
        )
        self.bearer_token = json.loads(request.text)["access_token"]
        self.refresh_token = json.loads(request.text)["refresh_token"]
    def get_token(self):
        return self.bearer_token

    def refresh(self):
        request = requests.post(
            url="https://api.helloasso-sandbox.com/oauth2/token",
            headers={'Content-Type': "application/x-www-form-urlencoded"},
            data={
                'client_id': getenv("CLIENT_ID"),
                'client_secret': self.refresh_token,
                'grant_type': "refresh_token",
            },
        )
        self.bearer_token=json.loads(request.text)["access_token"]
        self.refresh_token=json.loads(request.text)["refresh_token"]