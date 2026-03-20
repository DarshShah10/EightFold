"""
Aggregate Computation
=====================
Computes comprehensive metrics from harvested data.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)


def compute_all_aggregates(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute comprehensive aggregates from all harvested data.

    Args:
        raw_data: Complete harvested data dictionary

    Returns:
        Dictionary with computed aggregate metrics
    """
    repos = raw_data.get("repos", [])
    commits = raw_data.get("commits", [])
    pull_requests = raw_data.get("pull_requests", [])
    issues = raw_data.get("issues", [])
    events = raw_data.get("events", [])
    pr_reviews = raw_data.get("pr_reviews", [])
    issue_comments = raw_data.get("issue_comments", [])
    starred = raw_data.get("starred_repos", [])
    user = raw_data.get("user", {})

    aggregates = {
        # Basic counts
        "total_repos": len(repos),
        "total_commits": len(commits),
        "total_prs": len(pull_requests),
        "total_issues": len(issues),
        "total_events": len(events),
        "total_reviews_received": len(pr_reviews),
        "total_issue_comments": len(issue_comments),
        "total_starred": len(starred),

        # PR metrics
        "avg_pr_size": 0.0,
        "avg_pr_time_to_merge_hours": 0.0,
        "merge_rate": 0.0,
        "avg_review_comments": 0.0,
        "avg_pr_comments": 0.0,
        "prs_created": 0,
        "prs_merged": 0,

        # Issue metrics
        "avg_issue_close_hours": 0.0,
        "issues_closed_ratio": 0.0,
        "avg_issue_comments": 0.0,

        # Commit metrics
        "avg_commit_size": 0.0,
        "avg_files_per_commit": 0.0,
        "large_commit_ratio": 0.0,
        "merge_commit_ratio": 0.0,
        "signed_commit_ratio": 0.0,
        "weekend_coding_ratio": 0.0,
        "late_night_coding_ratio": 0.0,
        "avg_hour_of_day": 0.0,
        "commit_types_distribution": {},

        # Activity metrics
        "contributions_per_week": 0.0,
        "most_active_year_month": None,
        "unique_repos_contributed": 0,

        # Engineering maturity
        "test_coverage_ratio": 0.0,
        "ci_usage_ratio": 0.0,
        "docker_usage_ratio": 0.0,
        "readme_ratio": 0.0,
        "docs_ratio": 0.0,
        "security_doc_ratio": 0.0,

        # Code review signals
        "reviews_given_per_pr": 0.0,
        "approval_ratio": 0.0,
        "change_request_ratio": 0.0,

        # Social signals
        "avg_starred_repo_stars": 0.0,
        "follower_following_ratio": 0.0,

        # Release signals
        "repos_with_releases": 0,
        "total_releases": 0,

        # Branching signals
        "avg_branches_per_repo": 0.0,
        "protected_branch_ratio": 0.0,
    }

    # Compute PR aggregates
    _compute_pr_aggregates(pull_requests, aggregates)

    # Compute issue aggregates
    _compute_issue_aggregates(issues, aggregates)

    # Compute commit aggregates
    _compute_commit_aggregates(commits, aggregates)

    # Compute event aggregates
    _compute_event_aggregates(events, user, aggregates)

    # Compute repo structure aggregates
    _compute_repo_aggregates(repos, aggregates)

    # Compute review aggregates
    _compute_review_aggregates(pr_reviews, aggregates)

    # Compute social aggregates
    _compute_social_aggregates(starred, user, aggregates)

    return aggregates


def _compute_pr_aggregates(
    pull_requests: list,
    aggregates: Dict[str, Any]
) -> None:
    """Compute PR-related aggregates."""
    if not pull_requests:
        return

    prs_with_sizes = [pr['num_additions'] + pr['num_deletions'] for pr in pull_requests]
    aggregates["avg_pr_size"] = round(sum(prs_with_sizes) / len(prs_with_sizes), 2) if prs_with_sizes else 0.0

    merged_prs = [pr for pr in pull_requests if pr['merged']]
    aggregates["merge_rate"] = round(len(merged_prs) / len(pull_requests), 4) if pull_requests else 0.0
    aggregates["prs_merged"] = len(merged_prs)
    aggregates["prs_created"] = len(pull_requests)

    review_comments = [pr['num_review_comments'] for pr in pull_requests]
    aggregates["avg_review_comments"] = round(sum(review_comments) / len(review_comments), 2) if review_comments else 0.0

    pr_comments = [pr['num_comments'] for pr in pull_requests]
    aggregates["avg_pr_comments"] = round(sum(pr_comments) / len(pr_comments), 2) if pr_comments else 0.0

    merge_times = [pr['time_to_merge_hours'] for pr in merged_prs if pr.get('time_to_merge_hours')]
    if merge_times:
        aggregates["avg_pr_time_to_merge_hours"] = round(sum(merge_times) / len(merge_times), 2)


def _compute_issue_aggregates(
    issues: list,
    aggregates: Dict[str, Any]
) -> None:
    """Compute issue-related aggregates."""
    if not issues:
        return

    closed_issues = [i for i in issues if i['state'] == 'closed']
    aggregates["issues_closed_ratio"] = round(len(closed_issues) / len(issues), 4) if issues else 0.0

    close_times = [i['time_to_close_hours'] for i in closed_issues if i.get('time_to_close_hours')]
    if close_times:
        aggregates["avg_issue_close_hours"] = round(sum(close_times) / len(close_times), 2)

    issue_comments_count = [i['num_comments'] for i in issues]
    aggregates["avg_issue_comments"] = round(sum(issue_comments_count) / len(issue_comments_count), 2) if issue_comments_count else 0.0


def _compute_commit_aggregates(
    commits: list,
    aggregates: Dict[str, Any]
) -> None:
    """Compute commit-related aggregates."""
    if not commits:
        return

    commit_sizes = []
    files_counts = []
    late_night_count = 0
    weekend_count = 0
    merge_count = 0
    signed_count = 0
    large_commit_count = 0
    hours = []
    commit_types = defaultdict(int)

    for commit in commits:
        total_lines = commit.get("total_lines", 0)
        commit_sizes.append(total_lines)
        if total_lines > 500:
            large_commit_count += 1

        num_files = commit.get("num_files", 0)
        files_counts.append(num_files)

        hour = commit.get("hour_of_day")
        if hour is not None:
            hours.append(hour)
            if hour >= 22 or hour < 6:
                late_night_count += 1

        if commit.get("is_weekend", False):
            weekend_count += 1

        if commit.get("is_merge", False):
            merge_count += 1

        if commit.get("verified", False):
            signed_count += 1

        commit_types[commit.get("commit_type", "other")] += 1

    total = len(commits)
    aggregates["avg_commit_size"] = round(sum(commit_sizes) / total, 2) if commit_sizes else 0.0
    aggregates["avg_files_per_commit"] = round(sum(files_counts) / total, 2) if files_counts else 0.0
    aggregates["large_commit_ratio"] = round(large_commit_count / total, 4) if total else 0.0
    aggregates["merge_commit_ratio"] = round(merge_count / total, 4) if total else 0.0
    aggregates["signed_commit_ratio"] = round(signed_count / total, 4) if total else 0.0
    aggregates["weekend_coding_ratio"] = round(weekend_count / total, 4) if total else 0.0
    aggregates["late_night_coding_ratio"] = round(late_night_count / total, 4) if total else 0.0
    aggregates["avg_hour_of_day"] = round(sum(hours) / len(hours), 2) if hours else 0.0
    aggregates["commit_types_distribution"] = dict(commit_types)


def _compute_event_aggregates(
    events: list,
    user: Dict[str, Any],
    aggregates: Dict[str, Any]
) -> None:
    """Compute event-based aggregates."""
    if not events or not user.get("created_at"):
        return

    try:
        account_start = datetime.fromisoformat(user["created_at"].replace('Z', '+00:00'))
        account_weeks = max(1, (datetime.now(timezone.utc) - account_start).days / 7)
        aggregates["contributions_per_week"] = round(len(events) / account_weeks, 2)

        year_month_counts = defaultdict(int)
        for event in events:
            ym = event.get("year_month")
            if ym:
                year_month_counts[ym] += 1
        if year_month_counts:
            aggregates["most_active_year_month"] = max(year_month_counts, key=year_month_counts.get)

        repos_contributed = set()
        for event in events:
            if event.get("repo"):
                repos_contributed.add(event["repo"])
        aggregates["unique_repos_contributed"] = len(repos_contributed)
    except Exception as e:
        logger.debug(f"Could not compute event patterns: {e}")


def _compute_repo_aggregates(
    repos: list,
    aggregates: Dict[str, Any]
) -> None:
    """Compute repository structure aggregates."""
    if not repos:
        return

    total = len(repos)
    has_tests = sum(1 for r in repos if r.get("structure", {}).get("has_tests", False))
    has_ci = sum(1 for r in repos if r.get("structure", {}).get("has_ci", False))
    has_docker = sum(1 for r in repos if r.get("structure", {}).get("has_dockerfile", False))
    has_readme = sum(1 for r in repos if r.get("structure", {}).get("has_readme", False))
    has_docs = sum(1 for r in repos if r.get("structure", {}).get("has_docs", False))
    has_security = sum(1 for r in repos if r.get("structure", {}).get("has_security", False))

    aggregates["test_coverage_ratio"] = round(has_tests / total, 4) if total else 0.0
    aggregates["ci_usage_ratio"] = round(has_ci / total, 4) if total else 0.0
    aggregates["docker_usage_ratio"] = round(has_docker / total, 4) if total else 0.0
    aggregates["readme_ratio"] = round(has_readme / total, 4) if total else 0.0
    aggregates["docs_ratio"] = round(has_docs / total, 4) if total else 0.0
    aggregates["security_doc_ratio"] = round(has_security / total, 4) if total else 0.0


def _compute_review_aggregates(
    pr_reviews: list,
    aggregates: Dict[str, Any]
) -> None:
    """Compute code review aggregates."""
    if not pr_reviews:
        return

    total_reviews = len(pr_reviews)
    approvals = sum(1 for r in pr_reviews if r.get("state") == "APPROVED")
    changes_requested = sum(1 for r in pr_reviews if r.get("state") == "CHANGES_REQUESTED")
    aggregates["approval_ratio"] = round(approvals / total_reviews, 4) if total_reviews else 0.0
    aggregates["change_request_ratio"] = round(changes_requested / total_reviews, 4) if total_reviews else 0.0


def _compute_social_aggregates(
    starred: list,
    user: Dict[str, Any],
    aggregates: Dict[str, Any]
) -> None:
    """Compute social/engagement aggregates."""
    if starred:
        starred_stars = [s.get("stars", 0) for s in starred]
        aggregates["avg_starred_repo_stars"] = round(sum(starred_stars) / len(starred_stars), 2) if starred_stars else 0.0

    followers = user.get("followers", 0)
    following = user.get("following", 0)
    if following > 0:
        aggregates["follower_following_ratio"] = round(followers / following, 2)
