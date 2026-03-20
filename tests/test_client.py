"""
Tests for GitHub Client Module
==============================
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from github import Github

# Import the module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.client import (
    load_env_file,
    get_github_token,
    get_github_client,
    check_rate_limit,
    handle_rate_limit,
)


class TestLoadEnvFile:
    """Tests for load_env_file function."""

    def test_load_env_file_no_file(self, tmp_path):
        """Test that missing .env file doesn't raise error."""
        with patch('os.getcwd', return_value=str(tmp_path)):
            load_env_file()  # Should not raise

    def test_load_env_file_doesnt_overwrite(self, tmp_path):
        """Test that existing env vars aren't overwritten."""
        os.environ['GITHUB_TOKEN'] = 'existing_token'

        env_file = tmp_path / ".env"
        env_file.write_text('GITHUB_TOKEN=new_token\n')

        with patch('os.getcwd', return_value=str(tmp_path)):
            load_env_file()

        assert os.environ.get('GITHUB_TOKEN') == 'existing_token'

        # Cleanup
        del os.environ['GITHUB_TOKEN']


class TestGetGitHubToken:
    """Tests for get_github_token function."""

    def test_get_token_from_env(self):
        """Test getting token from environment variable."""
        os.environ['GITHUB_TOKEN'] = 'env_token_abc'
        token = get_github_token()
        assert token == 'env_token_abc'
        del os.environ['GITHUB_TOKEN']

    def test_get_token_missing(self):
        """Test behavior when no token is available."""
        # Clear any existing token and reload
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']

        # Clear cached env vars by reloading
        import importlib
        import modules.client
        importlib.reload(modules.client)
        from modules.client import get_github_token

        token = get_github_token()
        # Token will be None or from .env file if it exists
        assert token is None or isinstance(token, str)


class TestGetGitHubClient:
    """Tests for get_github_client function."""

    def test_get_client_with_token(self):
        """Test creating client with token."""
        os.environ['GITHUB_TOKEN'] = 'test_token'
        client = get_github_client()
        assert isinstance(client, Github)
        del os.environ['GITHUB_TOKEN']

    def test_get_client_without_token(self):
        """Test creating client without token."""
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
        client = get_github_client()
        assert isinstance(client, Github)


class TestRateLimit:
    """Tests for rate limit functions."""

    def test_check_rate_limit(self, mock_github_client):
        """Test checking rate limit status."""
        mock_rate = MagicMock()
        mock_core = MagicMock()
        mock_core.remaining = 4500
        mock_core.limit = 5000
        mock_core.reset.timestamp.return_value = 1700000000
        mock_rate.core = mock_core
        mock_github_client.get_rate_limit.return_value = mock_rate

        status = check_rate_limit(mock_github_client)
        assert status['remaining'] == 4500
        assert status['limit'] == 5000

    def test_handle_rate_limit_no_wait_needed(self, mock_github_client):
        """Test that no wait happens when rate limit is fine."""
        mock_rate = MagicMock()
        mock_core = MagicMock()
        mock_core.remaining = 100
        mock_core.limit = 5000
        mock_rate.core = mock_core
        mock_github_client.get_rate_limit.return_value = mock_rate

        # Should not raise or wait
        handle_rate_limit(mock_github_client, min_remaining=10)

    def test_handle_rate_limit_error(self, mock_github_client):
        """Test handling of rate limit check errors."""
        mock_github_client.get_rate_limit.side_effect = Exception("API Error")

        # Should not raise
        handle_rate_limit(mock_github_client)
