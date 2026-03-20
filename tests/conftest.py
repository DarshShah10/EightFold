"""
Test Fixtures and Configuration
==============================
Pytest fixtures for GitHub Signal Extraction Engine tests.
"""

import os
import pytest
from unittest.mock import MagicMock, Mock
from pathlib import Path


@pytest.fixture
def mock_github_client():
    """Mock GitHub client for testing without API calls."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "login": "testuser",
        "name": "Test User",
        "bio": "Software engineer",
        "company": "TestCorp",
        "location": "San Francisco",
        "blog": "https://testuser.dev",
        "email": "test@testuser.dev",
        "hireable": True,
        "public_repos": 42,
        "followers": 100,
        "following": 50,
        "created_at": "2020-01-15T10:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "type": "User",
        "site_admin": False,
        "twitter_username": "testuser",
        "public_gists": 5,
    }


@pytest.fixture
def sample_repo_data():
    """Sample repository data for testing."""
    return {
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "language": "Python",
        "stargazers": 150,
        "forks": 25,
        "watchers": 10,
        "created_at": "2021-06-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "pushed_at": "2024-01-15T12:00:00Z",
        "size": 5000,
        "description": "A test repository",
        "homepage": "https://testrepo.dev",
        "topics": ["python", "testing", "automation"],
        "license": "MIT",
        "open_issues": 5,
        "default_branch": "main",
        "is_archived": False,
        "is_disabled": False,
        "has_issues": True,
        "has_wiki": True,
        "has_projects": False,
        "has_pages": True,
        "has_downloads": False,
        "allow_forking": True,
        "visibility": "public",
        "mirror_url": None,
        "archived_at": None,
    }


@pytest.fixture
def sample_commit_data():
    """Sample commit data for testing."""
    return {
        "sha": "abc123def456",
        "message": "feat: Add new feature",
        "message_full": "feat: Add new feature\n\nThis commit adds a new feature.",
        "date": "2024-01-15T10:30:00Z",
        "author_date": "2024-01-15T10:30:00Z",
        "committer_date": "2024-01-15T10:30:00Z",
        "author_name": "Test User",
        "author_email": "test@testuser.dev",
        "committer_name": "Test User",
        "verified": True,
        "num_parents": 1,
        "is_merge": False,
        "files": [
            {
                "filename": "src/feature.py",
                "patch": "+ new feature",
                "additions": 50,
                "deletions": 5,
                "status": "added",
                "is_test": False,
                "is_docs": False,
                "is_config": False,
                "file_extension": ".py",
            }
        ],
        "commit_type": "feat",
        "additions": 50,
        "deletions": 5,
        "total_lines": 55,
        "churn_ratio": 10.0,
        "hour_of_day": 14,
        "day_of_week": 0,
        "is_weekend": False,
        "year_month": "2024-01",
        "num_files": 1,
        "num_test_files": 0,
        "num_docs_files": 0,
    }


@pytest.fixture
def sample_pr_data():
    """Sample PR data for testing."""
    return {
        "repo_name": "testuser/test-repo",
        "number": 42,
        "title": "Add new feature",
        "body": "This PR adds a new feature",
        "state": "closed",
        "merged": True,
        "merged_by": "reviewer",
        "created_at": "2024-01-10T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "merged_at": "2024-01-15T10:00:00Z",
        "closed_at": "2024-01-15T10:00:00Z",
        "time_to_merge_hours": 120.0,
        "time_to_close_hours": 120.0,
        "num_commits": 3,
        "num_files_changed": 5,
        "num_comments": 8,
        "num_review_comments": 4,
        "num_additions": 150,
        "num_deletions": 20,
        "labels": ["enhancement", "priority:high"],
        "is_draft": False,
        "is_maintainer_can_modify": True,
        "head_ref": "feature-branch",
        "base_ref": "main",
    }


@pytest.fixture
def sample_issue_data():
    """Sample issue data for testing."""
    return {
        "repo_name": "testuser/test-repo",
        "number": 100,
        "title": "Bug in feature X",
        "body": "There is a bug in feature X when doing Y",
        "state": "closed",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-05T10:00:00Z",
        "closed_at": "2024-01-05T10:00:00Z",
        "time_to_close_hours": 96.0,
        "num_comments": 6,
        "labels": ["bug", "priority:high"],
        "author": "reporter",
        "assignees": ["testuser"],
        "is_locked": False,
    }


@pytest.fixture
def sample_raw_data(sample_user_data, sample_repo_data, sample_commit_data, sample_pr_data, sample_issue_data):
    """Complete sample raw data for testing."""
    return {
        "github_handle": "testuser",
        "user": sample_user_data,
        "repos": [sample_repo_data],
        "lang_bytes": {"Python": 100000, "JavaScript": 50000},
        "commits": [sample_commit_data],
        "pull_requests": [sample_pr_data],
        "pr_reviews": [],
        "issues": [sample_issue_data],
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
            "harvested_at": "2024-01-15 10:00:00",
            "errors": [],
            "rate_limits_hit": 0,
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for testing."""
    output_dir = tmp_path / "data"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture(autouse=True)
def clean_env():
    """Clean up environment variables before and after each test."""
    original_token = os.environ.get('GITHUB_TOKEN')
    yield
    # Restore original state
    if original_token:
        os.environ['GITHUB_TOKEN'] = original_token
    elif 'GITHUB_TOKEN' in os.environ:
        del os.environ['GITHUB_TOKEN']
