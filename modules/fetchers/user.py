"""
User Data Fetchers
==================
Fetches user profile, social, and personal data from GitHub.
"""

import logging
from typing import Any, Dict, List

from github import Github, GithubException

logger = logging.getLogger(__name__)


def fetch_user_metadata(github_client: Github, handle: str) -> Dict[str, Any]:
    """
    Fetch complete user profile metadata.

    Args:
        github_client: Authenticated GitHub client
        handle: GitHub username

    Returns:
        Dictionary with user profile data
    """
    try:
        user = github_client.get_user(handle)
        return {
            "login": user.login,
            "name": user.name,
            "bio": user.bio,
            "company": user.company,
            "location": user.location,
            "blog": user.blog,
            "email": user.email,
            "hireable": user.hireable,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": str(user.created_at),
            "updated_at": str(user.updated_at),
            "type": getattr(user, 'type', 'User'),
            "site_admin": getattr(user, 'site_admin', False),
            "twitter_username": getattr(user, 'twitter_username', None),
            "public_gists": getattr(user, 'public_gists', 0),
        }
    except GithubException as e:
        logger.error(f"Failed to fetch user metadata: {e}")
        return {"login": handle, "error": str(e)}


def fetch_starred_repos(
    github_client: Github,
    handle: str,
    max_stars: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch repositories starred by the user (interests signal).

    Args:
        github_client: Authenticated GitHub client
        handle: GitHub username
        max_stars: Maximum number of starred repos to fetch

    Returns:
        List of starred repository data
    """
    starred = []
    try:
        user = github_client.get_user(handle)
        for repo in user.get_starred()[:max_stars]:
            starred.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "description": repo.description,
                "topics": repo.get_topics() if hasattr(repo, 'get_topics') else [],
            })
            if len(starred) % 20 == 0:
                logger.info(f"Fetched {len(starred)} starred repos...")
    except GithubException as e:
        logger.warning(f"Could not fetch starred repos: {e}")
    return starred


def fetch_orgs(github_client: Github, handle: str) -> List[Dict[str, Any]]:
    """
    Fetch organizations the user belongs to.

    Args:
        github_client: Authenticated GitHub client
        handle: GitHub username

    Returns:
        List of organization data
    """
    orgs = []
    try:
        user = github_client.get_user(handle)
        for org in user.get_orgs():
            orgs.append({
                "login": org.login,
                "description": org.description,
                "members_count": getattr(org, 'members_count', 0),
                "public_repos": getattr(org, 'public_repos', 0),
            })
    except GithubException as e:
        logger.warning(f"Could not fetch orgs: {e}")
    return orgs


def fetch_gists(github_client: Github, handle: str) -> List[Dict[str, Any]]:
    """
    Fetch user's public gists.

    Args:
        github_client: Authenticated GitHub client
        handle: GitHub username

    Returns:
        List of gist data
    """
    gists = []
    try:
        user = github_client.get_user(handle)
        for gist in user.get_gists()[:20]:
            gists.append({
                "id": gist.id,
                "description": gist.description,
                "created_at": str(gist.created_at),
                "updated_at": str(gist.updated_at),
                "files": list(gist.files.keys()),
                "public": gist.public,
                "html_url": gist.html_url,
            })
    except GithubException as e:
        logger.warning(f"Could not fetch gists: {e}")
    return gists
