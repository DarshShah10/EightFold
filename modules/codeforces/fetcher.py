"""
Codeforces API Fetcher
====================
Wraps the Codeforces public API for fetching user data, submissions, and contests.
No API key required — uses Codeforces public API.
"""

import logging
import time
import requests
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Codeforces API base URL
CF_API_BASE = "https://codeforces.com/api"

# Rate limiting — Codeforces allows ~2 requests/second
_last_request_time = 0.0
_REQUEST_INTERVAL = 0.6  # seconds between requests


def _rate_limit():
    """Enforce rate limiting between API requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _REQUEST_INTERVAL:
        time.sleep(_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _api_call(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Make a rate-limited API call to Codeforces.

    Args:
        endpoint: API endpoint (e.g., "user.status")
        params: Query parameters

    Returns:
        JSON response dict

    Raises:
        ValueError: If the API returns an error status
    """
    _rate_limit()

    url = f"{CF_API_BASE}/{endpoint}"
    try:
        response = requests.get(url, params=params or {}, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            comment = data.get("comment", "")
            logger.warning(f"Codeforces API error for {endpoint}: {comment}")
            raise ValueError(f"Codeforces API error: {comment}")

        return data.get("result", {})
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling {endpoint}: {e}")
        raise ValueError(f"Network error: {e}")


def get_user_info(handle: str) -> Dict[str, Any]:
    """
    Fetch basic user info from Codeforces.

    Args:
        handle: Codeforces username

    Returns:
        Dict with: handle, firstName, lastName, country, city, organization,
                  rating, maxRating, rank, maxRank, contribution, etc.
    """
    result = _api_call("user.info", {"handles": handle})
    if not result:
        raise ValueError(f"User '{handle}' not found on Codeforces")
    return result[0]


def get_user_status(handle: str) -> List[Dict[str, Any]]:
    """
    Fetch all submissions for a user.

    Args:
        handle: Codeforces username

    Returns:
        List of submission dicts with keys:
        - id, contestId, problem, author, programmingLanguage,
        - verdict, creationTimeSeconds, relativeTimeSeconds
        - testset, passedTestCount, timeConsumed, memoryConsumedBytes
    """
    result = _api_call("user.status", {"handle": handle})
    return result


def get_contest_list() -> List[Dict[str, Any]]:
    """
    Fetch all Codeforces contests.

    Returns:
        List of contest dicts with keys:
        - id, name, phase, startTimeSeconds, durationSeconds, type
    """
    result = _api_call("contest.list")
    # Filter to finished contests only
    return [c for c in result if c.get("phase") == "FINISHED"]


def get_user_rating(handle: str) -> List[Dict[str, Any]]:
    """
    Fetch rating changes for a user across all contests.

    Returns:
        List of rating change dicts with keys:
        - contestId, contestName, rank, ratingUpdateTimeSeconds,
        - oldRating, newRating
    """
    result = _api_call("user.rating", {"handle": handle})
    return result


def get_user_standings(
    handle: str,
    contest_id: int,
    from_position: int = 1,
    count: int = 1
) -> Dict[str, Any]:
    """
    Fetch user's standing in a specific contest.

    Args:
        handle: Codeforces username
        contest_id: Contest ID
        from_position: Starting rank position
        count: Number of rows to fetch

    Returns:
        Dict with rows, problems, contest info
    """
    result = _api_call("contest.standings", {
        "contestId": contest_id,
        "handles": handle,
        "from": from_position,
        "count": count,
    })
    return result


def get_problemset_problems() -> List[Dict[str, Any]]:
    """
    Fetch all problems from the problemset.

    Returns:
        List of problem dicts with keys:
        - contestId, index, name, type, points, rating, tags
    """
    result = _api_call("problemset.problems")
    return result.get("problems", [])


def check_user_exists(handle: str) -> bool:
    """
    Check if a Codeforces handle exists.

    Args:
        handle: Codeforces username

    Returns:
        True if user exists, False otherwise
    """
    try:
        get_user_info(handle)
        return True
    except ValueError:
        return False


# ─── Convenience functions ──────────────────────────────────────────────────────


def get_user_summary(handle: str) -> Dict[str, Any]:
    """
    Get a quick summary of a user's Codeforces profile.

    Args:
        handle: Codeforces username

    Returns:
        Summary dict with basic info + rating summary
    """
    info = get_user_info(handle)

    # Count submissions
    try:
        submissions = get_user_status(handle)
        total_submissions = len(submissions)
        ac_count = sum(1 for s in submissions if s.get("verdict") == "OK")
    except ValueError:
        total_submissions = 0
        ac_count = 0

    # Get rating history
    try:
        rating_history = get_user_rating(handle)
        max_rating = max((r.get("newRating", 0) for r in rating_history), default=0)
        contest_count = len(rating_history)
    except ValueError:
        rating_history = []
        max_rating = 0
        contest_count = 0

    return {
        "handle": handle,
        "info": info,
        "total_submissions": total_submissions,
        "accepted_count": ac_count,
        "ac_rate": round(ac_count / total_submissions, 3) if total_submissions > 0 else 0,
        "rating": info.get("rating", 0),
        "max_rating": info.get("maxRating", 0),
        "rank": info.get("rank", "unrated"),
        "max_rank": info.get("maxRank", "unrated"),
        "contest_count": contest_count,
        "rating_history": rating_history,
    }
