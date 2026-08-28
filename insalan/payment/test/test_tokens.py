"""Test module for the HelloAsso OAuth2 Token class."""

from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from insalan.settings import HA_OAUTH_CLIENT_ID, HA_OAUTH_CLIENT_SECRET, HA_URL

from ..tokens import Token


class TestToken(TestCase):
    """Tests for the Token class."""

    def setUp(self) -> None:
        # Create a token without calling obtain_token()
        self.token = Token.__new__(Token)
        # We need to clear the singleton before each test case.
        Token.instance = None

    def test_create_instance_should_obtain_token(self) -> None:
        """
        Tests that creating a new Token instance should try to obtain a token.
        """
        with patch.object(Token, "obtain_token") as mock_obtain_token:
            Token()

        mock_obtain_token.assert_called_once_with()

    def test_get_instance_should_return_same_instance(self) -> None:
        """Tests that Token.get_instance() always retuns the same instance."""
        with patch.object(Token, "obtain_token") as mock_obtain_token:
            token1: Token = Token.get_instance()
            token2: Token = Token.get_instance()

        self.assertIs(
            token1,
            token2,
            "Token.get_instance() must always returns the same instance",
        )
        mock_obtain_token.assert_called_once()

    def test_obtain_token(self) -> None:
        """Tests to obtain a token from the HelloAsso API."""
        mock_response = Mock(**{
            "json.return_value": {
                "expires_in": "10",
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
            },
        })
        mock_response.status_code = 200

        with patch("requests.post", return_value=mock_response) as mock_post:
            with patch("time.time", return_value=100.0) as mock_time:
                self.token.obtain_token()

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "client_secret": HA_OAUTH_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=45,
        )
        mock_time.assert_called_once_with()
        mock_response.json.assert_called()
        self.assertEqual(self.token.expiration_date, 110.0)
        self.assertEqual(self.token.bearer_token, "test_access_token")
        self.assertEqual(self.token.refresh_token, "test_refresh_token")

    def test_obtain_token_requests_exception(self) -> None:
        """
        Tests that a requests exception while obtaining a token raises a
        RuntimeError.
        """
        Token.instance = self.token

        with patch(
            "requests.post",
            side_effect=requests.exceptions.RequestException(),
        ) as mock_post:
            with self.assertRaises(RuntimeError) as context:
                self.token.obtain_token()

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "client_secret": HA_OAUTH_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=45,
        )
        self.assertEqual(
            context.exception.args[0],
            "Impossible de rafraîchir le jeton HelloAsso",
        )
        self.assertIsNone(
            Token.instance,
            "Token instance must not be saved when the requests failed",
        )

    def test_obtain_token_requests_failed(self) -> None:
        """
        Tests that requests with a non-200 status code raise a RuntimeError.
        """
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch("requests.post", return_value=mock_response) as mock_post:
            with self.assertRaises(RuntimeError) as context:
                self.token.obtain_token()

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "client_secret": HA_OAUTH_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=45,
        )
        self.assertEqual(
            context.exception.args[0],
            "Impossible de rafraîchir le jeton HelloAsso: Not found",
        )

    def test_obtain_token_requests_with_error_message(self) -> None:
        """
        Tests that successful requests containing an error message raise a
        RuntimeError.
        """
        mock_response = Mock(**{
            "json.return_value": {
                "error": True,
                "error_description": "Test error message",
            },
        })
        mock_response.status_code = 200

        with patch("requests.post", return_value=mock_response) as mock_post:
            with self.assertRaises(RuntimeError) as context:
                self.token.obtain_token()

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "client_secret": HA_OAUTH_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=45,
        )
        self.assertEqual(
            context.exception.args[0],
            "Impossible de rafraîchir le jeton HelloAsso: Test error message",
        )

    def test_obtain_token_with_secret(self) -> None:
        """Tests to obtain a token witha refresh token from the HelloAsso API."""
        mock_response = Mock(**{
            "json.return_value": {
                "expires_in": "10",
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
            },
        })
        mock_response.status_code = 200

        with patch("requests.post", return_value=mock_response) as mock_post:
            with patch("time.time", return_value=100.0) as mock_time:
                self.token.obtain_token(secret="test_secret")

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "refresh_token": "test_secret",
                "grant_type": "refresh_token",
            },
            timeout=45,
        )
        mock_time.assert_called_once_with()
        mock_response.json.assert_called()
        self.assertEqual(self.token.expiration_date, 110.0)
        self.assertEqual(self.token.bearer_token, "test_access_token")
        self.assertEqual(self.token.refresh_token, "test_refresh_token")

    def test_obtain_token_with_secret_requests_exception(self) -> None:
        """
        Tests that a requests exception while obtaining a token raises a
        RuntimeError.
        """
        Token.instance = self.token

        with patch(
            "requests.post",
            side_effect=requests.exceptions.RequestException(),
        ) as mock_post:
            with self.assertRaises(RuntimeError) as context:
                self.token.obtain_token(secret="test_secret")

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "refresh_token": "test_secret",
                "grant_type": "refresh_token",
            },
            timeout=45,
        )
        self.assertEqual(
            context.exception.args[0],
            "Impossible de rafraîchir le jeton HelloAsso",
        )
        self.assertIsNone(
            Token.instance,
            "Token instance must not be saved when the requests failed",
        )


    def test_obtain_token_with_secret_requests_failed(self) -> None:
        """
        Tests that requests with a non-200 status code raise a RuntimeError.
        """
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch("requests.post", return_value=mock_response) as mock_post:
            with self.assertRaises(RuntimeError) as context:
                self.token.obtain_token(secret="test_secret")

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "refresh_token": "test_secret",
                "grant_type": "refresh_token",
            },
            timeout=45,
        )
        self.assertEqual(
            context.exception.args[0],
            "Impossible de rafraîchir le jeton HelloAsso: Not found",
        )

    def test_obtain_token_with_secrect_requests_with_error_message(self
                                                                   ) -> None:
        """
        Tests that successful requests containing an error message raise a
        RuntimeError.
        """
        mock_response = Mock(**{
            "json.return_value": {
                "error": True,
                "error_description": "Test error message",
            },
        })
        mock_response.status_code = 200

        with patch("requests.post", return_value=mock_response) as mock_post:
            with self.assertRaises(RuntimeError) as context:
                self.token.obtain_token(secret="test_secret")

        mock_post.assert_called_once_with(
            url=f"{HA_URL}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "client_id": HA_OAUTH_CLIENT_ID,
                "refresh_token": "test_secret",
                "grant_type": "refresh_token",
            },
            timeout=45,
        )
        self.assertEqual(
            context.exception.args[0],
            "Impossible de rafraîchir le jeton HelloAsso: Test error message",
        )

    def test_get_token(self) -> None:
        """Tests getting a bearer token."""
        self.token.expiration_date = 200.0
        self.token.bearer_token = "test_token"

        with patch("time.time", return_value=100.0) as mock_time:
            token: str = self.token.get_token()

        mock_time.assert_called_once_with()
        self.assertEqual(token, "test_token")

    def test_get_token_should_refresh(self) -> None:
        """Tests getting a expired token should trigger a token refresh."""
        self.token.expiration_date = 50.0
        self.token.bearer_token = "test_token"

        def mock_refresh_side_effect() -> None:
            self.token.bearer_token = "refreshed_test_token"

        with patch.object(
            Token,
            "refresh",
            side_effect=mock_refresh_side_effect,
        ) as mock_refresh:
            with patch("time.time", return_value=100.0) as mock_time:
                token: str = self.token.get_token()

        mock_refresh.assert_called_once_with()
        mock_time.assert_called_once_with()
        self.assertEqual(token, "refreshed_test_token")

    def test_refresh(self) -> None:
        """
        Tests that refresh try to obtain a new token with the refresh token.
        """
        self.token.refresh_token = "test_refresh_token"

        with patch.object(Token, "obtain_token") as mock_obtain_token:
            self.token.refresh()

        mock_obtain_token.assert_called_once_with(secret="test_refresh_token")
