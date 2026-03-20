"""
Issue Data Fetchers
===================
Fetches issues and comments from GitHub repositories.
"""

import logging
from typing import Any, Dict, List

from github import Github, GithubException

logger = logging.getLogger(__name__)


def fetch_issues(
    github_client: Github,
    repo_full_name: str,
    max_issues: int = 15
) -> List[Dict[str, Any]]:
    """
    Fetch issues with participation and resolution metrics.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_issues: Maximum number of issues to fetch

    Returns:
        List of issue data with metrics
    """
    issues = []
    try:
        repo = github_client.get_repo(repo_full_name)
        repo_issues = repo.get_issues(state='all', sort='updated', direction='desc')
        count = 0

        for issue in repo_issues:
            # Skip pull requests (GitHub issues API includes PRs)
            if hasattr(issue, 'pull_request') and issue.pull_request:
                continue
            if count >= max_issues:
                break
            try:
                issue_data = _extract_issue_data(issue, repo_full_name)
                issues.append(issue_data)
                count += 1
            except GithubException as e:
                logger.warning(f"Could not fetch issue: {e}")
    except GithubException as e:
        logger.warning(f"Could not fetch issues for {repo_full_name}: {e}")
    return issues


def _extract_issue_data(issue, repo_full_name: str) -> Dict[str, Any]:
    """
    Extract comprehensive data from an issue object.

    Args:
        issue: PyGithub Issue object
        repo_full_name: Full repository name

    Returns:
        Dictionary with issue data
    """
    created_at = issue.created_at
    closed_at = issue.closed_at
    time_to_close = None
    if created_at and closed_at:
        time_to_close = (closed_at - created_at).total_seconds() / 3600

    return {
        "repo_name": repo_full_name,
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "state": issue.state,
        "created_at": str(created_at),
        "updated_at": str(issue.updated_at),
        "closed_at": str(closed_at) if closed_at else None,
        "time_to_close_hours": time_to_close,
        "num_comments": issue.comments,
        "labels": [label.name for label in issue.labels] if hasattr(issue, 'labels') else [],
        "author": issue.user.login if hasattr(issue, 'user') else None,
        "assignees": [a.login for a in issue.assignees] if hasattr(issue, 'assignees') else [],
        "is_locked": issue.locked if hasattr(issue, 'locked') else False,
    }


def fetch_issue_comments(
    github_client: Github,
    repo_full_name: str,
    max_issues: int = 10,
    max_comments_per_issue: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch issue comments for communication analysis.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_issues: Maximum number of issues to check
        max_comments_per_issue: Maximum comments per issue

    Returns:
        List of comment data
    """
    comments = []
    try:
        repo = github_client.get_repo(repo_full_name)
        repo_issues = repo.get_issues(state='all', sort='updated', direction='desc')

        count = 0
        for issue in repo_issues:
            if hasattr(issue, 'pull_request') and issue.pull_request:
                continue
            if count >= max_issues:
                break
            try:
                issue_comments = _fetch_single_issue_comments(
                    issue, repo_full_name, max_comments_per_issue
                )
                comments.extend(issue_comments)
            except GithubException as e:
                logger.warning(f"Could not fetch comments for issue #{issue.number}: {e}")
            count += 1
    except GithubException as e:
        logger.warning(f"Could not fetch issue comments: {e}")
    return comments


def _fetch_single_issue_comments(
    issue,
    repo_full_name: str,
    max_comments: int
) -> List[Dict[str, Any]]:
    """
    Fetch comments for a single issue.

    Args:
        issue: PyGithub Issue object
        repo_full_name: Full repository name
        max_comments: Maximum comments to fetch

    Returns:
        List of comment data for the issue
    """
    comments = []
    body_text = issue.body or ''

    for comment in issue.get_comments()[:max_comments]:
        comments.append({
            "repo_name": repo_full_name,
            "issue_number": issue.number,
            "issue_title": issue.title,
            "user": comment.user.login,
            "created_at": str(comment.created_at),
            "body": comment.body,
            "body_length": len(comment.body) if comment.body else 0,
            "has_code_block": '```' in (comment.body or ''),
            "has_links": 'http' in (comment.body or ''),
        })

    # Also include the issue body as a comment if it has content
    if body_text and len(body_text) > 10:
        comments.insert(0, {
            "repo_name": repo_full_name,
            "issue_number": issue.number,
            "issue_title": issue.title,
            "user": issue.user.login if hasattr(issue, 'user') else None,
            "created_at": str(issue.created_at),
            "body": body_text,
            "body_length": len(body_text),
            "has_code_block": '```' in body_text,
            "has_links": 'http' in body_text,
        })

    return comments
