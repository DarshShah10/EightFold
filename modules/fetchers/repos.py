"""
Repository Data Fetchers
========================
Fetches repository metadata, languages, structure, and dependencies.
"""

import logging
from typing import Any, Dict, List

from github import Github, GithubException

from modules.config import DEPENDENCY_FILES, STRUCTURE_PATTERNS

logger = logging.getLogger(__name__)


def fetch_repos(github_client: Github, handle: str) -> List[Dict[str, Any]]:
    """
    Fetch all public repos owned by the user.

    Args:
        github_client: Authenticated GitHub client
        handle: GitHub username

    Returns:
        List of repository data (only repos owned by the user)
    """
    repos = []
    try:
        logger.info(f"Fetching repositories for {handle}")
        user_repos = github_client.get_user(handle).get_repos(type='owner')

        for repo in user_repos:
            # CRITICAL: Only include repos owned by this user
            # Verify the repo owner matches the requested handle
            if not repo.full_name.startswith(f"{handle}/"):
                logger.debug(f"Skipping repo {repo.full_name} - not owned by {handle}")
                continue

            # Skip forks
            if repo.fork:
                logger.debug(f"Skipping fork: {repo.full_name}")
                continue

            try:
                repo_data = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "owner": handle,  # Explicitly mark owner
                    "language": repo.language,
                    "stargazers": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "watchers": repo.watchers_count,
                    "created_at": str(repo.created_at),
                    "updated_at": str(repo.updated_at),
                    "pushed_at": str(repo.pushed_at),
                    "size": repo.size,
                    "description": repo.description,
                    "homepage": repo.homepage,
                    "topics": repo.get_topics() if hasattr(repo, 'get_topics') else [],
                    "license": repo.license.spdx_id if repo.license else None,
                    "open_issues": repo.open_issues_count,
                    "default_branch": repo.default_branch,
                    "is_archived": repo.archived,
                    "is_disabled": repo.disabled,
                    "has_issues": getattr(repo, 'has_issues', False),
                    "has_wiki": getattr(repo, 'has_wiki', False),
                    "has_projects": getattr(repo, 'has_projects', False),
                    "has_pages": getattr(repo, 'has_pages', False),
                    "has_downloads": getattr(repo, 'has_downloads', False),
                    "allow_forking": getattr(repo, 'allow_forking', False),
                    "visibility": getattr(repo, 'visibility', 'public'),
                    "mirror_url": getattr(repo, 'mirror_url', None),
                    "archived_at": str(repo.archived_at) if hasattr(repo, 'archived_at') and repo.archived_at else None,
                    "is_fork": repo.fork,
                }
                repos.append(repo_data)
            except GithubException as e:
                logger.warning(f"Could not fetch details for repo {repo.name}: {e}")
                continue

            if len(repos) % 50 == 0:
                logger.info(f"Fetched {len(repos)} repos so far...")

        logger.info(f"Total repos owned by {handle}: {len(repos)}")
    except GithubException as e:
        logger.error(f"Failed to fetch repos: {e}")
    return repos


def fetch_languages(
    github_client: Github,
    repos: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Fetch language breakdown across all repos (bytes-weighted).

    Args:
        github_client: Authenticated GitHub client
        repos: List of repository data

    Returns:
        Dictionary mapping language to total bytes
    """
    language_bytes: Dict[str, int] = {}
    logger.info("Fetching language data for repositories")

    for repo_data in repos:
        try:
            repo = github_client.get_repo(repo_data['full_name'])
            languages = repo.get_languages()
            for lang, bytes_count in languages.items():
                language_bytes[lang] = language_bytes.get(lang, 0) + bytes_count
        except GithubException as e:
            logger.warning(f"Could not fetch languages for {repo_data['name']}: {e}")

    logger.info(f"Language data fetched for {len(language_bytes)} languages")
    return language_bytes


def fetch_repo_structure(
    github_client: Github,
    repo_full_name: str
) -> Dict[str, bool]:
    """
    Check repo for structure signals (tests, docs, CI, etc.).

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)

    Returns:
        Dictionary of structure signals
    """
    structure = {key: False for key in STRUCTURE_PATTERNS.keys()}
    try:
        repo = github_client.get_repo(repo_full_name)
        contents_tree = repo.get_git_tree(repo.default_branch, recursive=True).tree
        file_paths = [item.path.lower() for item in contents_tree if item.type == 'blob']

        for key, patterns in STRUCTURE_PATTERNS.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower.endswith('/'):
                    if any(p.startswith(pattern_lower) for p in file_paths):
                        structure[key] = True
                        break
                else:
                    if pattern_lower in file_paths:
                        structure[key] = True
                        break
    except GithubException as e:
        logger.warning(f"Could not fetch structure for {repo_full_name}: {e}")
    return structure


def fetch_dependency_files(
    github_client: Github,
    repo_full_name: str
) -> Dict[str, str]:
    """
    Fetch content of dependency files from a repository.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)

    Returns:
        Dictionary mapping file path to content
    """
    contents = {}
    try:
        repo = github_client.get_repo(repo_full_name)
        contents_tree = repo.get_git_tree(repo.default_branch, recursive=True).tree
        file_paths = {item.path.lower(): item.path for item in contents_tree if item.type == 'blob'}

        for dep_file in DEPENDENCY_FILES:
            normalized_name = dep_file.lower()
            if normalized_name in file_paths:
                try:
                    file_content = repo.get_contents(file_paths[normalized_name])
                    if not isinstance(file_content, list):
                        contents[file_paths[normalized_name]] = file_content.decoded_content.decode('utf-8', errors='replace')
                except Exception as e:
                    logger.debug(f"Could not fetch {file_paths[normalized_name]}: {e}")
    except GithubException as e:
        logger.warning(f"Could not fetch file tree for {repo_full_name}: {e}")
    return contents


def fetch_branches(
    github_client: Github,
    repo_full_name: str,
    max_branches: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch branching strategy signals.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_branches: Maximum number of branches to fetch

    Returns:
        List of branch data
    """
    branches = []
    try:
        repo = github_client.get_repo(repo_full_name)
        for branch in repo.get_branches()[:max_branches]:
            branches.append({
                "name": branch.name,
                "is_protected": branch.protected,
                "is_default": branch.name == repo.default_branch,
                "commit_sha": branch.commit.sha[:12] if branch.commit else None,
            })
    except GithubException as e:
        logger.warning(f"Could not fetch branches for {repo_full_name}: {e}")
    return branches


def fetch_releases(
    github_client: Github,
    repo_full_name: str,
    max_releases: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch release information for release engineering signals.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_releases: Maximum number of releases to fetch

    Returns:
        List of release data
    """
    releases = []
    try:
        repo = github_client.get_repo(repo_full_name)
        releases_list = repo.get_releases()
        count = 0
        for release in releases_list:
            if count >= max_releases:
                break
            try:
                releases.append({
                    "tag_name": release.tag_name,
                    "name": release.title,
                    "created_at": str(release.created_at),
                    "published_at": str(release.published_at) if hasattr(release, 'published_at') else None,
                    "prerelease": release.prerelease,
                    "draft": release.draft,
                    "assets_count": len(list(release.get_assets())) if hasattr(release, 'get_assets') else 0,
                })
                count += 1
            except Exception as e:
                logger.debug(f"Could not process release: {e}")
    except GithubException as e:
        logger.warning(f"Could not fetch releases for {repo_full_name}: {e}")
    return releases
