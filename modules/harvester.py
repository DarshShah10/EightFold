"""
GitHub Signal Extraction Engine - Main Harvester
=================================================
Comprehensive GitHub data harvester that collects ALL behavioral signals
needed for deep developer profiling and skill inference.

This is the main orchestration module that coordinates all fetchers.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

from modules.client import get_github_client, handle_rate_limit
from modules.storage import (
    ensure_output_dir,
    save_harvested_data,
    validate_harvested_data,
    save_json,
    get_output_path,
)
from modules.database import (
    save_user,
    save_repos,
    save_commits,
    save_pull_requests,
    save_issues,
    save_languages,
    save_orgs,
    print_db_stats,
)
from modules.aggregates import compute_all_aggregates
from modules.fetchers import (
    fetch_user_metadata,
    fetch_starred_repos,
    fetch_orgs,
    fetch_gists,
    fetch_repos,
    fetch_languages,
    fetch_repo_structure,
    fetch_dependency_files,
    fetch_branches,
    fetch_releases,
    fetch_commits,
    fetch_pull_requests,
    fetch_pr_reviews,
    fetch_issues,
    fetch_issue_comments,
    fetch_events,
)
from modules.config import DEFAULTS

logger = logging.getLogger(__name__)

# Configure console logging for real-time feedback
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logging.getLogger().addHandler(_console_handler)
logging.getLogger().setLevel(logging.INFO)


def _print(msg: str, end: str = "\n", flush: bool = True):
    """Print with immediate flush for real-time feedback."""
    print(msg, end=end, flush=flush)
    logger.info(msg)


def harvest(github_handle: str, output_dir: str = "data") -> Dict[str, Any]:
    """
    Harvest ALL GitHub signals for comprehensive developer profiling.

    Args:
        github_handle: GitHub username to harvest
        output_dir: Directory to save harvested data

    Returns:
        Complete raw_data dict with all signal sources
    """
    start_time = time.time()
    _print("=" * 60)
    _print(f"GitHub Signal Extraction - Harvesting @{github_handle}")
    _print("=" * 60)

    ensure_output_dir(output_dir)
    github_client = get_github_client()

    # Initialize result structure
    result = _init_result_structure(github_handle)

    # Phase 1: User & Social Data
    phase_start = time.time()
    _print("[1/5] Fetching user profile and social data...", flush=True)
    _harvest_user_data(github_client, github_handle, result)
    _save_to_db(github_handle, result, phase="user")
    _save_checkpoint(result, output_dir, github_handle, "01_user_data")
    _print(f"    Done in {time.time() - phase_start:.1f}s", flush=True)

    # Phase 2: Repository Data
    phase_start = time.time()
    _print("[2/5] Fetching repositories...", flush=True)
    if not _harvest_repositories(github_client, github_handle, result):
        _print("[ERROR] No repositories found", flush=True)
        return result
    _save_to_db(github_handle, result, phase="repos")
    _save_checkpoint(result, output_dir, github_handle, "02_repos")
    _print(f"    Found {len(result['repos'])} repos in {time.time() - phase_start:.1f}s", flush=True)

    # Phase 3-4: Deep Analysis of Top Repos (reduced to 5 for speed)
    phase_start = time.time()
    _print("[3/5] Deep analyzing top repos...", flush=True)
    _harvest_deep_repo_analysis(github_client, result)
    _save_to_db(github_handle, result, phase="commits")
    _save_checkpoint(result, output_dir, github_handle, "03_deep_analysis")
    _print(f"    Done in {time.time() - phase_start:.1f}s", flush=True)

    # Phase 4: Contribution Events
    phase_start = time.time()
    _print("[4/5] Fetching contribution events...", flush=True)
    _harvest_events(github_client, github_handle, result)
    _save_checkpoint(result, output_dir, github_handle, "04_events")
    _print(f"    Done in {time.time() - phase_start:.1f}s", flush=True)

    # Phase 5: Compute Aggregates
    phase_start = time.time()
    _print("[5/5] Computing metrics...", flush=True)
    result["aggregates"] = compute_all_aggregates(result)

    # Final save
    _print("Saving final data...", flush=True)
    _save_results(result, output_dir, github_handle, start_time)
    _save_to_db(github_handle, result, phase="final")

    # Print DB stats
    print_db_stats()

    return result


def _save_checkpoint(result: Dict[str, Any], output_dir: str, handle: str, stage: str) -> None:
    """Save intermediate checkpoint for resilience."""
    try:
        output_path = get_output_path(output_dir, handle, f"_checkpoint_{stage}")
        save_json(result, output_path)
        _print(f"    [CHECKPOINT] Saved {stage}", flush=True)
    except Exception as e:
        logger.warning(f"Checkpoint save failed: {e}")


def _save_to_db(handle: str, result: Dict[str, Any], phase: str) -> None:
    """Save harvested data to SQLite database after each phase."""
    try:
        # User data
        if result.get("user") and "error" not in result["user"]:
            save_user(handle, result["user"])

        # Repos
        if result.get("repos"):
            save_repos(handle, result["repos"])

        # Languages
        if result.get("lang_bytes"):
            save_languages(handle, result["lang_bytes"])

        # Orgs
        if result.get("orgs"):
            save_orgs(handle, result["orgs"])

        # Commits (with code diffs!)
        if result.get("commits"):
            save_commits(handle, result["commits"])
            _print(f"    [DB] Saved {len(result['commits'])} commits with code diffs", flush=True)

        # PRs
        if result.get("pull_requests"):
            save_pull_requests(handle, result["pull_requests"])
            _print(f"    [DB] Saved {len(result['pull_requests'])} PRs", flush=True)

        # Issues
        if result.get("issues"):
            save_issues(handle, result["issues"])
            _print(f"    [DB] Saved {len(result['issues'])} issues", flush=True)

        logger.info(f"Database updated at phase: {phase}")
    except Exception as e:
        logger.warning(f"Database save failed: {e}")


def _init_result_structure(github_handle: str) -> Dict[str, Any]:
    """Initialize the result dictionary structure."""
    return {
        "github_handle": github_handle,
        "user": {},
        "repos": [],
        "lang_bytes": {},
        "commits": [],
        "pull_requests": [],
        "pr_reviews": [],
        "issues": [],
        "issue_comments": [],
        "events": [],
        "starred_repos": [],
        "gists": [],
        "orgs": [],
        "dep_files": {},
        "branches": {},
        "releases": {},
        "aggregates": {},
        "metadata": {
            "harvested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "errors": [],
            "rate_limits_hit": 0,
        }
    }


def _harvest_user_data(
    github_client,
    github_handle: str,
    result: Dict[str, Any]
) -> None:
    """Phase 1: Harvest user and social data."""
    user_data = fetch_user_metadata(github_client, github_handle)
    result["user"] = user_data

    if "error" in user_data:
        result["metadata"]["errors"].append(f"User fetch failed: {user_data['error']}")
        return

    # Fetch additional social data
    result["starred_repos"] = fetch_starred_repos(github_client, github_handle)
    result["orgs"] = fetch_orgs(github_client, github_handle)
    result["gists"] = fetch_gists(github_client, github_handle)


def _harvest_repositories(
    github_client,
    github_handle: str,
    result: Dict[str, Any]
) -> bool:
    """Phase 2: Harvest repository data. Returns False if no repos found."""
    repos = fetch_repos(github_client, github_handle)
    result["repos"] = repos

    if not repos:
        result["metadata"]["errors"].append("No public repositories found")
        return False

    _print(f"  Found {len(repos)} repositories", flush=True)
    result["lang_bytes"] = fetch_languages(github_client, repos)

    return True


def _harvest_deep_repo_analysis(
    github_client,
    result: Dict[str, Any]
) -> None:
    """Phases 3-8: Deep analysis of top repos - optimized for speed."""
    repos = result["repos"]
    # Reduced from 10 to 5 repos for speed
    top_repos = sorted(repos, key=lambda r: r.get('size', 0), reverse=True)[:5]

    _print(f"  Deep analyzing top {len(top_repos)} repos (structure, branches, releases)...", flush=True)

    for i, repo_data in enumerate(top_repos):
        repo_name = repo_data['full_name']
        _print(f"    [{i+1}/{len(top_repos)}] {repo_name}", flush=True)
        handle_rate_limit(github_client, min_remaining=5)

        try:
            # Fetch structure
            repo_data["structure"] = fetch_repo_structure(github_client, repo_name)

            # Fetch branches
            result["branches"][repo_name] = fetch_branches(
                github_client, repo_name, DEFAULTS['max_branches_per_repo']
            )

            # Fetch releases
            result["releases"][repo_name] = fetch_releases(
                github_client, repo_name, DEFAULTS['max_releases_per_repo']
            )
        except Exception as e:
            logger.warning(f"Error analyzing {repo_name}: {e}")

    # Phase 4: Commits (reduced to 10 per repo for speed)
    _print(f"  Fetching commits from {len(top_repos)} repos...", flush=True)
    for i, repo_data in enumerate(top_repos):
        repo_name = repo_data['full_name']
        handle_rate_limit(github_client, min_remaining=5)

        try:
            repo_commits = fetch_commits(github_client, repo_name, 10)
            for commit in repo_commits:
                commit['repo_name'] = repo_name
                result["commits"].append(commit)
            _print(f"    [{i+1}/{len(top_repos)}] {repo_name}: {len(repo_commits)} commits", flush=True)
        except Exception as e:
            logger.warning(f"Error fetching commits from {repo_name}: {e}")

    # Phase 5: Pull Requests (reduced to 5 per repo for speed)
    _print(f"  Fetching PRs...", flush=True)
    for i, repo_data in enumerate(top_repos):
        repo_name = repo_data['full_name']
        handle_rate_limit(github_client, min_remaining=5)

        try:
            prs = fetch_pull_requests(github_client, repo_name, 5)
            result["pull_requests"].extend(prs)
            _print(f"    [{i+1}/{len(top_repos)}] {repo_name}: {len(prs)} PRs", flush=True)
        except Exception as e:
            logger.warning(f"Error fetching PRs from {repo_name}: {e}")

    # Phase 6: PR Reviews (top 3 repos only)
    _print(f"  Fetching PR reviews...", flush=True)
    for repo_data in top_repos[:3]:
        repo_name = repo_data['full_name']
        handle_rate_limit(github_client, min_remaining=5)

        try:
            reviews = fetch_pr_reviews(github_client, repo_name, 5)
            result["pr_reviews"].extend(reviews)
            _print(f"    {repo_name}: {len(reviews)} reviews", flush=True)
        except Exception as e:
            logger.warning(f"Error fetching reviews from {repo_name}: {e}")

    # Phase 7: Issues (top 3 repos only)
    _print(f"  Fetching issues...", flush=True)
    for repo_data in top_repos[:3]:
        repo_name = repo_data['full_name']
        handle_rate_limit(github_client, min_remaining=5)

        try:
            issues = fetch_issues(github_client, repo_name, 10)
            result["issues"].extend(issues)
            _print(f"    {repo_name}: {len(issues)} issues", flush=True)
        except Exception as e:
            logger.warning(f"Error fetching issues from {repo_name}: {e}")

    # Phase 8: Issue Comments (top 3 repos only)
    _print(f"  Fetching issue comments...", flush=True)
    for repo_data in top_repos[:3]:
        repo_name = repo_data['full_name']
        handle_rate_limit(github_client, min_remaining=5)

        try:
            comments = fetch_issue_comments(github_client, repo_name, 5)
            result["issue_comments"].extend(comments)
        except Exception as e:
            logger.warning(f"Error fetching comments from {repo_name}: {e}")


def _harvest_events(
    github_client,
    github_handle: str,
    result: Dict[str, Any]
) -> None:
    """Phase 9: Harvest contribution events."""
    handle_rate_limit(github_client, min_remaining=5)
    result["events"] = fetch_events(github_client, github_handle, DEFAULTS['max_events'])


def _save_results(
    result: Dict[str, Any],
    output_dir: str,
    github_handle: str,
    start_time: float
) -> None:
    """Save results to file and update metadata."""
    # Save main data
    output_path = save_harvested_data(result, output_dir, github_handle)
    if not output_path:
        result["metadata"]["errors"].append("Failed to save data to file")

    # Update metadata counts
    duration = time.time() - start_time
    result["metadata"]["duration_seconds"] = round(duration, 2)
    result["metadata"]["repos_count"] = len(result["repos"])
    result["metadata"]["commits_count"] = len(result["commits"])
    result["metadata"]["prs_count"] = len(result["pull_requests"])
    result["metadata"]["issues_count"] = len(result["issues"])
    result["metadata"]["events_count"] = len(result["events"])
    result["metadata"]["reviews_count"] = len(result["pr_reviews"])
    result["metadata"]["comments_count"] = len(result["issue_comments"])
    result["metadata"]["starred_count"] = len(result["starred_repos"])
    result["metadata"]["gists_count"] = len(result["gists"])
    result["metadata"]["orgs_count"] = len(result["orgs"])

    # Re-save with updated metadata
    if output_path:
        from modules.storage import save_json
        save_json(result, output_path)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys

    handle = sys.argv[1] if len(sys.argv) > 1 else "gvanrossum"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "data"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    result = harvest(handle, output_dir)

    print("\n" + "=" * 60)
    print(f"HARVEST COMPLETE: {handle}")
    print("=" * 60)
    print(f"Duration: {result['metadata'].get('duration_seconds', 0)}s")
    print(f"Repos: {result['metadata'].get('repos_count', 0)}")
    print(f"Commits: {result['metadata'].get('commits_count', 0)}")
    print(f"Data saved to: {output_dir}/{handle}_raw.json")
