"""
Commit Data Fetchers
====================
Fetches commits with deep metrics from GitHub repositories.
"""

import os
import re
import time
import logging
from typing import Any, Dict, List, Optional

from github import Github, GithubException

from modules.config import COMMIT_PATTERNS

logger = logging.getLogger(__name__)

# Global state for progress reporting
_commit_progress = 0


def _print_progress(repo_name: str, count: int, total: int):
    """Print commit fetch progress."""
    global _commit_progress
    _commit_progress += 1
    if _commit_progress % 5 == 0 or count == total:
        print(f"\r    Commits: {count}/{total}", end="", flush=True)


def classify_commit_message(message: str) -> str:
    """
    Classify commit type based on message patterns.

    Args:
        message: Commit message to classify

    Returns:
        Commit type string (feat, fix, refactor, etc.)
    """
    message_lower = message.lower()

    # Priority order: security > fix > feat > refactor > test > docs > perf > chore > ci > revert
    if re.search(COMMIT_PATTERNS['security'], message_lower):
        return 'security'
    if re.search(COMMIT_PATTERNS['fix'], message_lower):
        return 'fix'
    if re.search(COMMIT_PATTERNS['feat'], message_lower):
        return 'feat'
    if re.search(COMMIT_PATTERNS['refactor'], message_lower):
        return 'refactor'
    if re.search(COMMIT_PATTERNS['test'], message_lower):
        return 'test'
    if re.search(COMMIT_PATTERNS['docs'], message_lower):
        return 'docs'
    if re.search(COMMIT_PATTERNS['perf'], message_lower):
        return 'perf'
    if re.search(COMMIT_PATTERNS['ci'], message_lower):
        return 'ci'
    if re.search(COMMIT_PATTERNS['chore'], message_lower):
        return 'chore'
    if re.search(COMMIT_PATTERNS['revert'], message_lower):
        return 'revert'
    return 'other'


def fetch_commits(
    github_client: Github,
    repo_full_name: str,
    max_commits: int = 30,
    timeout_per_commit: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Fetch recent commits with deep metrics.

    Args:
        github_client: Authenticated GitHub client
        repo_full_name: Full repository name (owner/repo)
        max_commits: Maximum number of commits to fetch
        timeout_per_commit: Max seconds to spend on file details per commit

    Returns:
        List of commit data with deep metrics
    """
    global _commit_progress
    commits = []
    _commit_progress = 0

    try:
        repo = github_client.get_repo(repo_full_name)
        commits_list = repo.get_commits()
        count = 0

        for commit in commits_list:
            if count >= max_commits:
                break

            try:
                commit_data = _extract_commit_data(
                    commit,
                    timeout=timeout_per_commit,
                    repo_full_name=repo_full_name
                )
                commits.append(commit_data)
                count += 1

                # Show progress every 5 commits
                if count % 5 == 0:
                    print(f"\r    Fetched {count}/{max_commits} commits...", end="", flush=True)

            except Exception as e:
                logger.debug(f"Could not fetch commit in {repo_full_name}: {e}")
                # If a commit fails, still count it but skip detailed data
                commits.append({
                    "sha": getattr(commit, 'sha', 'unknown')[:12] if commit else 'unknown',
                    "error": str(e),
                    "repo_name": repo_full_name,
                })
                count += 1

        print(f"\r    Fetched {count}/{max_commits} commits from {repo_full_name}")

    except GithubException as e:
        logger.warning(f"Could not fetch commits for {repo_full_name}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching commits for {repo_full_name}: {e}")

    return commits


def _extract_commit_data(
    commit,
    timeout: float = 5.0,
    repo_full_name: str = ""
) -> Dict[str, Any]:
    """
    Extract comprehensive data from a commit object.

    Args:
        commit: PyGithub Commit object
        timeout: Max seconds for file details
        repo_full_name: Repository name for logging

    Returns:
        Dictionary with commit data
    """
    start_time = time.time()

    # Basic commit data (always get this - it's fast)
    commit_data = {
        "sha": commit.sha,
        "message": (commit.commit.message.split('\n')[0] if commit.commit.message else ""),
        "message_full": commit.commit.message,
        "date": str(commit.commit.author.date) if commit.commit.author else "",
        "author_date": str(commit.commit.author.date) if commit.commit.author else "",
        "committer_date": str(commit.commit.committer.date) if commit.commit.committer else "",
        "author_name": commit.commit.author.name if commit.commit.author else "",
        "author_email": commit.commit.author.email if commit.commit.author else "",
        "committer_name": commit.commit.committer.name if commit.commit.committer else "",
        "verified": commit.commit.verification.verified if hasattr(commit.commit, 'verification') else False,
        "num_parents": len(commit.parents) if commit.parents else 0,
        "is_merge": len(commit.parents) > 1 if commit.parents else False,
        "files": [],
        "commit_type": classify_commit_message(commit.commit.message or ""),
    }

    # Get stats (fast API call)
    _add_commit_stats(commit_data, commit)

    # Time-of-day analysis (from existing data, no API call)
    _add_time_analysis(commit_data, commit)

    # Get file details (slow - may skip if taking too long)
    elapsed = time.time() - start_time
    if elapsed < timeout:
        remaining_timeout = timeout - elapsed
        _add_file_details(commit_data, commit, remaining_timeout)

    return commit_data


def _add_commit_stats(commit_data: Dict[str, Any], commit) -> None:
    """Add commit statistics to commit data."""
    try:
        stats = commit.stats
        commit_data["additions"] = stats.additions if hasattr(stats, 'additions') else 0
        commit_data["deletions"] = stats.deletions if hasattr(stats, 'deletions') else 0
        commit_data["total_lines"] = stats.total if hasattr(stats, 'total') else 0
        commit_data["churn_ratio"] = commit_data["additions"] / max(1, commit_data["deletions"])
    except Exception:
        commit_data["additions"] = 0
        commit_data["deletions"] = 0
        commit_data["total_lines"] = 0
        commit_data["churn_ratio"] = 0


def _add_time_analysis(commit_data: Dict[str, Any], commit) -> None:
    """Add time-of-day analysis to commit data."""
    if commit.commit.author and commit.commit.author.date:
        dt = commit.commit.author.date
        commit_data["hour_of_day"] = dt.hour
        commit_data["day_of_week"] = dt.weekday()
        commit_data["is_weekend"] = dt.weekday() >= 5
        commit_data["year_month"] = f"{dt.year}-{dt.month:02d}"


def _add_file_details(
    commit_data: Dict[str, Any],
    commit,
    timeout: float = 3.0
) -> None:
    """Add file-level details to commit data with timeout protection."""
    try:
        file_count = 0
        start = time.time()

        for file in commit.files:
            # Check timeout
            if time.time() - start > timeout:
                logger.debug(f"Timeout fetching files for commit {commit.sha[:8]}")
                break

            filename = getattr(file, 'filename', '')
            commit_data["files"].append({
                "filename": filename,
                "patch": getattr(file, 'patch', None),
                "additions": file.additions,
                "deletions": file.deletions,
                "status": getattr(file, 'status', ''),
                "is_test": 'test' in filename.lower() or 'spec' in filename.lower(),
                "is_docs": 'doc' in filename.lower() or 'readme' in filename.lower(),
                "is_config": any(x in filename.lower() for x in [
                    'config', '.json', '.yaml', '.yml', '.toml', 'dockerfile'
                ]),
                "file_extension": os.path.splitext(filename)[1] if filename else '',
            })
            file_count += 1

            # Safety limit - max 100 files per commit
            if file_count >= 100:
                break

    except Exception as e:
        logger.debug(f"Could not fetch file details: {e}")

    commit_data["num_files"] = len(commit_data["files"])
    commit_data["num_test_files"] = sum(1 for f in commit_data["files"] if f.get("is_test"))
    commit_data["num_docs_files"] = sum(1 for f in commit_data["files"] if f.get("is_docs"))
