import json
import requests
from os import getenv

class tokens :
    def __init__(self, bearer, refresh):
        self.bearer_token=bearer
        self.refresh_token=refresh
    def get_token(self):
        return self.bearer
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
    def init(self):
        request = requests.post(
            url="https://api.helloasso-sandbox.com/oauth2/token",
            headers={'Content-Type': "application/x-www-form-urlencoded"},
            data={
                'client_id': getenv("CLIENT_ID"),
                'client_secret': self.refresh_token,
                'grant_type': "client_credentials",
            },
        )
        self.bearer_token=json.loads(request.text)["access_token"]
        self.bearer_token = json.loads(request.text)["refresh_token"]