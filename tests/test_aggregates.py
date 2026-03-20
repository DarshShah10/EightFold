"""
Tests for Aggregate Computation
===============================
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.aggregates import compute_all_aggregates


class TestComputeAllAggregates:
    """Tests for aggregate computation."""

    def test_empty_data(self):
        """Test computation with empty data."""
        raw_data = {
            "repos": [],
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [],
            "user": {},
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["total_repos"] == 0
        assert aggregates["total_commits"] == 0
        assert aggregates["total_prs"] == 0
        assert aggregates["merge_rate"] == 0.0
        assert aggregates["avg_commit_size"] == 0.0

    def test_pr_aggregates(self, sample_raw_data):
        """Test PR-related aggregate computation."""
        raw_data = {
            "user": {},
            "repos": [],
            "commits": [],
            "pull_requests": [
                {
                    "num_additions": 100,
                    "num_deletions": 20,
                    "merged": True,
                    "num_review_comments": 5,
                    "num_comments": 10,
                    "time_to_merge_hours": 48.0,
                },
                {
                    "num_additions": 50,
                    "num_deletions": 10,
                    "merged": True,
                    "num_review_comments": 2,
                    "num_comments": 3,
                    "time_to_merge_hours": 24.0,
                },
                {
                    "num_additions": 200,
                    "num_deletions": 50,
                    "merged": False,
                    "num_review_comments": 0,
                    "num_comments": 1,
                    "time_to_merge_hours": None,
                },
            ],
            "issues": [],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["total_prs"] == 3
        assert aggregates["avg_pr_size"] == pytest.approx(143.3, rel=0.1)
        assert aggregates["merge_rate"] == pytest.approx(0.667, rel=0.1)
        assert aggregates["avg_review_comments"] == pytest.approx(2.33, rel=0.1)
        assert aggregates["avg_pr_time_to_merge_hours"] == pytest.approx(36.0, rel=0.1)

    def test_commit_aggregates(self, sample_raw_data):
        """Test commit-related aggregate computation."""
        raw_data = {
            "user": {},
            "repos": [],
            "commits": [
                {
                    "total_lines": 100,
                    "num_files": 3,
                    "hour_of_day": 14,
                    "is_weekend": False,
                    "is_merge": False,
                    "verified": True,
                    "commit_type": "feat",
                },
                {
                    "total_lines": 50,
                    "num_files": 1,
                    "hour_of_day": 10,
                    "is_weekend": False,
                    "is_merge": False,
                    "verified": False,
                    "commit_type": "fix",
                },
                {
                    "total_lines": 500,
                    "num_files": 10,
                    "hour_of_day": 23,
                    "is_weekend": True,
                    "is_merge": True,
                    "verified": True,
                    "commit_type": "feat",
                },
            ],
            "pull_requests": [],
            "issues": [],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["total_commits"] == 3
        assert aggregates["avg_commit_size"] == pytest.approx(216.67, rel=0.1)
        assert aggregates["avg_files_per_commit"] == pytest.approx(4.67, rel=0.1)
        assert aggregates["late_night_coding_ratio"] == pytest.approx(0.333, rel=0.1)
        assert aggregates["weekend_coding_ratio"] == pytest.approx(0.333, rel=0.1)
        assert aggregates["merge_commit_ratio"] == pytest.approx(0.333, rel=0.1)
        assert aggregates["signed_commit_ratio"] == pytest.approx(0.667, rel=0.1)

    def test_issue_aggregates(self, sample_raw_data):
        """Test issue-related aggregate computation."""
        raw_data = {
            "user": {},
            "repos": [],
            "commits": [],
            "pull_requests": [],
            "issues": [
                {
                    "state": "closed",
                    "time_to_close_hours": 48.0,
                    "num_comments": 5,
                },
                {
                    "state": "closed",
                    "time_to_close_hours": 24.0,
                    "num_comments": 2,
                },
                {
                    "state": "open",
                    "time_to_close_hours": None,
                    "num_comments": 0,
                },
            ],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["total_issues"] == 3
        assert aggregates["issues_closed_ratio"] == pytest.approx(0.667, rel=0.1)
        assert aggregates["avg_issue_close_hours"] == pytest.approx(36.0, rel=0.1)
        assert aggregates["avg_issue_comments"] == pytest.approx(2.33, rel=0.1)

    def test_repo_structure_aggregates(self, sample_raw_data):
        """Test repository structure aggregate computation."""
        raw_data = {
            "user": {},
            "repos": [
                {"structure": {"has_tests": True, "has_ci": True, "has_dockerfile": False}},
                {"structure": {"has_tests": True, "has_ci": False, "has_dockerfile": True}},
                {"structure": {"has_tests": False, "has_ci": True, "has_dockerfile": True}},
                {"structure": {"has_tests": True, "has_ci": True, "has_dockerfile": True}},
            ],
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["total_repos"] == 4
        assert aggregates["test_coverage_ratio"] == pytest.approx(0.75, rel=0.1)
        assert aggregates["ci_usage_ratio"] == pytest.approx(0.75, rel=0.1)
        # 3 repos have docker files (repos 2, 3, 4)
        assert aggregates["docker_usage_ratio"] == pytest.approx(0.75, rel=0.1)

    def test_social_aggregates(self, sample_raw_data):
        """Test social/engagement aggregate computation."""
        raw_data = {
            "user": {
                "followers": 100,
                "following": 50,
            },
            "repos": [],
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [
                {"stars": 1000},
                {"stars": 500},
                {"stars": 200},
            ],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["follower_following_ratio"] == 2.0
        assert aggregates["avg_starred_repo_stars"] == pytest.approx(566.67, rel=0.1)

    def test_review_aggregates(self, sample_raw_data):
        """Test code review aggregate computation."""
        raw_data = {
            "user": {},
            "repos": [],
            "commits": [],
            "pull_requests": [],
            "issues": [],
            "events": [],
            "pr_reviews": [
                {"state": "APPROVED"},
                {"state": "APPROVED"},
                {"state": "CHANGES_REQUESTED"},
                {"state": "COMMENTED"},
            ],
            "issue_comments": [],
            "starred_repos": [],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["approval_ratio"] == pytest.approx(0.5, rel=0.1)
        assert aggregates["change_request_ratio"] == pytest.approx(0.25, rel=0.1)

    def test_commit_types_distribution(self, sample_raw_data):
        """Test commit types distribution computation."""
        raw_data = {
            "user": {},
            "repos": [],
            "commits": [
                {"commit_type": "feat"},
                {"commit_type": "feat"},
                {"commit_type": "fix"},
                {"commit_type": "docs"},
                {"commit_type": "feat"},
            ],
            "pull_requests": [],
            "issues": [],
            "events": [],
            "pr_reviews": [],
            "issue_comments": [],
            "starred_repos": [],
        }

        aggregates = compute_all_aggregates(raw_data)

        assert aggregates["commit_types_distribution"]["feat"] == 3
        assert aggregates["commit_types_distribution"]["fix"] == 1
        assert aggregates["commit_types_distribution"]["docs"] == 1
