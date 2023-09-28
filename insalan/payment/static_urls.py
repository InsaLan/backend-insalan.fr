class static_urls:
    instance = None

    def __init__(self):
        if static_urls.instance is None:
            static_urls.instance = self
        self.tokens_url="https://api.helloasso-sandbox.com/oauth2/token"
        self.checkout_url="https://api.helloasso-sandbox.com/organizations/insalan-test/checkout-intents"
        self.back_url=""
        self.error_url=""
        self.return_url=""

    def get_tokens_url(self):
        return self.tokens_url

    def get_checkout_url(self):
        return self.checkout_url

    def get_back_url(self):
        return self.back_url

    def get_error_url(self):
        return self.error_url

    def get_return_url(self):
        return self.return_url