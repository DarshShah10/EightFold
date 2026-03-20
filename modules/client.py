"""
GitHub Client Setup and Rate Limiting
======================================
Handles GitHub API authentication and rate limit management.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional

from github import Github, GithubException

logger = logging.getLogger(__name__)

# Progress indicator for real-time feedback
_progress_dots = 0


def _print_progress(msg: str = ""):
    """Print progress without newline for real-time feedback."""
    global _progress_dots
    _progress_dots += 1
    if _progress_dots % 10 == 0:
        print(f"\r{'.' * (_progress_dots % 40):<40} {msg}", end="", flush=True)
    else:
        print(".", end="", flush=True)


def load_env_file() -> None:
    """
    Load environment variables from .env file if it exists.
    Uses python-dotenv if available, otherwise simple parsing.
    """
    env_path = Path('.env')

    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        logger.debug("Loaded .env file via python-dotenv")
    except ImportError:
        # Fallback to simple parsing
        logger.debug("python-dotenv not available, using simple .env parsing")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value


def get_github_token() -> Optional[str]:
    """
    Get GitHub token from environment or .env file.

    Priority:
    1. GITHUB_TOKEN environment variable
    2. GITHUB_TOKEN from .env file
    """
    # Ensure .env is loaded
    load_env_file()

    token = os.environ.get('GITHUB_TOKEN')
    if token:
        logger.info(f"Using GitHub token: {token[:4]}...{token[-4:]}")
    else:
        logger.warning("No GITHUB_TOKEN found - using unauthenticated access (rate limited)")

    return token


def get_github_client() -> Github:
    """
    Create and return a GitHub client.

    Uses token from environment or .env file if available.
    """
    token = get_github_token()
    if token:
        return Github(token)
    return Github()


def check_rate_limit(github_client: Github) -> dict:
    """
    Get current rate limit status.

    Returns dict with remaining, limit, and reset timestamp.
    """
    try:
        rate_limit = github_client.get_rate_limit()
        if hasattr(rate_limit, 'core'):
            core = rate_limit.core
            return {
                'remaining': getattr(core, 'remaining', 0),
                'limit': getattr(core, 'limit', 0),
                'reset': getattr(core, 'reset', None),
            }
    except Exception as e:
        logger.debug(f"Could not get rate limit: {e}")

    return {'remaining': 0, 'limit': 0, 'reset': None}


def handle_rate_limit(github_client: Github, min_remaining: int = 10) -> None:
    """
    Check GitHub API rate limit and wait if needed.

    Args:
        github_client: GitHub client instance
        min_remaining: Minimum remaining requests before waiting
    """
    status = check_rate_limit(github_client)
    remaining = status.get('remaining', 0)
    reset_time = status.get('reset')

    # Only wait if we're truly running low (not just below arbitrary threshold)
    if remaining < 5 and reset_time:
        try:
            reset_ts = reset_time.timestamp() if hasattr(reset_time, 'timestamp') else 0
            if reset_ts > time.time():
                wait_time = max(1, reset_ts - time.time()) + 1
                print(f"\n[WAITING] Rate limit low ({remaining} remaining). Waiting {wait_time:.0f}s for reset...", flush=True)
                time.sleep(wait_time)
        except Exception as e:
            logger.debug(f"Rate limit handling error: {e}")
