"""
Fetchers Package
================
Modular fetchers for different GitHub data types.
"""

from .user import (
    fetch_user_metadata,
    fetch_starred_repos,
    fetch_orgs,
    fetch_gists,
)
from .repos import (
    fetch_repos,
    fetch_languages,
    fetch_repo_structure,
    fetch_dependency_files,
    fetch_branches,
    fetch_releases,
)
from .commits import (
    fetch_commits,
    classify_commit_message,
)
from .pull_requests import (
    fetch_pull_requests,
    fetch_pr_reviews,
)
from .issues import (
    fetch_issues,
    fetch_issue_comments,
)
from .events import fetch_events

__all__ = [
    # User fetchers
    'fetch_user_metadata',
    'fetch_starred_repos',
    'fetch_orgs',
    'fetch_gists',
    # Repo fetchers
    'fetch_repos',
    'fetch_languages',
    'fetch_repo_structure',
    'fetch_dependency_files',
    'fetch_branches',
    'fetch_releases',
    # Commit fetchers
    'fetch_commits',
    'classify_commit_message',
    # PR fetchers
    'fetch_pull_requests',
    'fetch_pr_reviews',
    # Issue fetchers
    'fetch_issues',
    'fetch_issue_comments',
    # Event fetchers
    'fetch_events',
]
