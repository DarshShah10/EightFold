"""
Contribution Events Fetcher
===========================
Fetches contribution event data from GitHub users.
"""

import logging
from typing import Any, Dict, List

from github import Github, GithubException

logger = logging.getLogger(__name__)


def fetch_events(
    github_client: Github,
    handle: str,
    max_events: int = 200
) -> List[Dict[str, Any]]:
    """
    Fetch contribution events for activity pattern analysis.

    Args:
        github_client: Authenticated GitHub client
        handle: GitHub username
        max_events: Maximum number of events to fetch

    Returns:
        List of contribution event data
    """
    events = []
    try:
        user = github_client.get_user(handle)
        user_events = user.get_events()
        count = 0

        for event in user_events:
            if count >= max_events:
                break
            try:
                event_data = _extract_event_data(event)
                events.append(event_data)
                count += 1
            except Exception as e:
                logger.debug(f"Could not process event: {e}")
    except GithubException as e:
        logger.warning(f"Could not fetch events for {handle}: {e}")
    return events


def _extract_event_data(event) -> Dict[str, Any]:
    """
    Extract comprehensive data from an event object.

    Args:
        event: PyGithub Event object

    Returns:
        Dictionary with event data
    """
    event_data = {
        "type": event.type,
        "repo": event.repo.name if event.repo else None,
        "created_at": str(event.created_at),
        "payload": {},
    }

    # Parse event payload
    if hasattr(event, 'payload') and event.payload:
        payload = event.payload
        if isinstance(payload, dict):
            _parse_event_payload(event_data, payload)

    # Time analysis
    if event.created_at:
        dt = event.created_at
        event_data["hour_of_day"] = dt.hour
        event_data["day_of_week"] = dt.weekday()
        event_data["is_weekend"] = dt.weekday() >= 5
        event_data["year_month"] = f"{dt.year}-{dt.month:02d}"
        event_data["year"] = dt.year
        event_data["month"] = dt.month

    return event_data


def _parse_event_payload(event_data: Dict[str, Any], payload: Dict) -> None:
    """
    Parse event payload for relevant data.

    Args:
        event_data: Dictionary to update with parsed payload
        payload: Raw payload dictionary
    """
    if 'commits' in payload:
        commits = payload.get('commits', [])
        event_data["payload"]["commit_count"] = len(commits)
        if commits and isinstance(commits[0], dict):
            event_data["payload"]["first_commit_sha"] = commits[0].get('sha', '')[:12]

    if 'action' in payload:
        event_data["payload"]["action"] = payload.get('action')

    if 'ref' in payload:
        event_data["payload"]["ref"] = payload.get('ref')

    if 'description' in payload:
        event_data["payload"]["description"] = payload.get('description')

    if 'issue' in payload:
        issue = payload['issue']
        if isinstance(issue, dict):
            event_data["payload"]["issue_number"] = issue.get('number')

    if 'pull_request' in payload:
        pr = payload['pull_request']
        if isinstance(pr, dict):
            event_data["payload"]["pr_number"] = pr.get('number')
            event_data["payload"]["pr_action"] = pr.get('action')
