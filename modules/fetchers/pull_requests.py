"""
Pull Request Data Fetchers
==========================
Fetches PRs and code review data from GitHub repositories.
"""

import logging
from typing import Any, Dict, List

from github import Github, GithubException

logger = logging.getLogger(__name__)


def fetch_pull_requests(
    github_client: Github,
    repo_full_name: str,
    max_prs: int = 15
) -> List[Dict[str, Any]]:
    """
    Fetch PRs with full collaboration metrics.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_prs: Maximum number of PRs to fetch

    Returns:
        List of PR data with collaboration metrics
    """
    prs = []
    try:
        repo = github_client.get_repo(repo_full_name)
        pulls = repo.get_pulls(state='all', sort='updated', direction='desc')
        count = 0

        for pr in pulls:
            if count >= max_prs:
                break
            try:
                pr_data = _extract_pr_data(pr, repo_full_name)
                prs.append(pr_data)
                count += 1
            except GithubException as e:
                logger.warning(f"Could not fetch PR: {e}")
    except GithubException as e:
        logger.warning(f"Could not fetch PRs for {repo_full_name}: {e}")
    return prs


def _extract_pr_data(pr, repo_full_name: str) -> Dict[str, Any]:
    """
    Extract comprehensive data from a PR object.

    Args:
        pr: PyGithub PullRequest object
        repo_full_name: Full repository name

    Returns:
        Dictionary with PR data
    """
    # Calculate time metrics
    created_at = pr.created_at
    merged_at = pr.merged_at
    closed_at = pr.closed_at

    time_to_merge = None
    time_to_close = None
    if created_at and merged_at:
        time_to_merge = (merged_at - created_at).total_seconds() / 3600
    if created_at and closed_at:
        time_to_close = (closed_at - created_at).total_seconds() / 3600

    return {
        "repo_name": repo_full_name,
        "number": pr.number,
        "title": pr.title,
        "body": pr.body,
        "state": pr.state,
        "merged": pr.merged_at is not None,
        "merged_by": str(pr.merged_by.login) if pr.merged_by else None,
        "created_at": str(created_at),
        "updated_at": str(pr.updated_at),
        "merged_at": str(merged_at) if merged_at else None,
        "closed_at": str(closed_at) if closed_at else None,
        "time_to_merge_hours": time_to_merge,
        "time_to_close_hours": time_to_close,
        "num_commits": pr.commits,
        "num_files_changed": pr.changed_files if hasattr(pr, 'changed_files') else 0,
        "num_comments": pr.comments,
        "num_review_comments": pr.review_comments,
        "num_additions": pr.additions if hasattr(pr, 'additions') else 0,
        "num_deletions": pr.deletions if hasattr(pr, 'deletions') else 0,
        "labels": [label.name for label in pr.labels] if hasattr(pr, 'labels') else [],
        "is_draft": pr.draft if hasattr(pr, 'draft') else False,
        "is_maintainer_can_modify": getattr(pr, 'maintainer_can_modify', False),
        "head_ref": pr.head.ref if hasattr(pr, 'head') else None,
        "base_ref": pr.base.ref if hasattr(pr, 'base') else None,
    }


def fetch_pr_reviews(
    github_client: Github,
    repo_full_name: str,
    max_prs: int = 15,
    max_reviews_per_pr: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch PR reviews for code review behavior analysis.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_prs: Maximum number of PRs to check
        max_reviews_per_pr: Maximum reviews per PR

    Returns:
        List of review data
    """
    reviews = []
    try:
        repo = github_client.get_repo(repo_full_name)
        pulls = repo.get_pulls(state='all', sort='updated', direction='desc')

        count = 0
        for pr in pulls:
            if count >= max_prs:
                break
            try:
                pr_reviews = _fetch_single_pr_reviews(pr, repo_full_name, max_reviews_per_pr)
                reviews.extend(pr_reviews)
            except GithubException as e:
                logger.warning(f"Could not fetch reviews for PR #{pr.number}: {e}")
            count += 1
    except GithubException as e:
        logger.warning(f"Could not fetch PR reviews: {e}")
    return reviews


def _fetch_single_pr_reviews(
    pr,
    repo_full_name: str,
    max_reviews: int
) -> List[Dict[str, Any]]:
    """
    Fetch reviews for a single PR.

    Args:
        pr: PyGithub PullRequest object
        repo_full_name: Full repository name
        max_reviews: Maximum reviews to fetch

    Returns:
        List of review data for the PR
    """
    reviews = []
    count = 0
    try:
        # PaginatedList doesn't support slicing - iterate and limit manually
        for review in pr.get_reviews():
            if count >= max_reviews:
                break
            reviews.append({
                "repo_name": repo_full_name,
                "pr_number": pr.number,
                "pr_title": pr.title,
                "user": review.user.login,
                "state": review.state,  # APPROVED, CHANGES_REQUESTED, COMMENTED, etc.
                "submitted_at": str(review.submitted_at) if review.submitted_at else None,
                "body": review.body,
                "commit_id": review.commit_id,
            })
            count += 1
    except Exception as e:
        logger.warning(f"Error fetching reviews for PR #{pr.number}: {e}")
    return reviews
