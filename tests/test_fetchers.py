"""
Tests for Fetcher Modules
==========================
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.fetchers.user import (
    fetch_user_metadata,
    fetch_starred_repos,
    fetch_orgs,
    fetch_gists,
)
from modules.fetchers.repos import (
    fetch_repos,
    fetch_languages,
    fetch_repo_structure,
    fetch_dependency_files,
    fetch_branches,
    fetch_releases,
)
from modules.fetchers.commits import (
    fetch_commits,
    classify_commit_message,
)


class TestFetchUserMetadata:
    """Tests for fetch_user_metadata."""

    def test_fetch_user_success(self, mock_github_client):
        """Test successful user metadata fetch."""
        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_user.name = "Test User"
        mock_user.bio = "A test user"
        mock_user.company = "TestCorp"
        mock_user.location = "San Francisco"
        mock_user.blog = "https://test.dev"
        mock_user.email = "test@test.dev"
        mock_user.hireable = True
        mock_user.public_repos = 42
        mock_user.followers = 100
        mock_user.following = 50
        mock_user.created_at = Mock()
        mock_user.created_at.__str__ = Mock(return_value="2020-01-01")
        mock_user.updated_at = Mock()
        mock_user.updated_at.__str__ = Mock(return_value="2024-01-01")
        mock_user.type = "User"
        mock_user.site_admin = False
        mock_user.twitter_username = "testuser"
        mock_user.public_gists = 5

        mock_github_client.get_user.return_value = mock_user

        result = fetch_user_metadata(mock_github_client, "testuser")

        assert result["login"] == "testuser"
        assert result["name"] == "Test User"
        assert result["public_repos"] == 42
        assert result["followers"] == 100

    def test_fetch_user_not_found(self, mock_github_client):
        """Test handling of user not found."""
        from github import GithubException
        mock_github_client.get_user.side_effect = GithubException(404, "Not Found")

        result = fetch_user_metadata(mock_github_client, "nonexistent")

        assert "error" in result
        assert result["login"] == "nonexistent"


class TestFetchStarredRepos:
    """Tests for fetch_starred_repos."""

    def test_fetch_starred_success(self, mock_github_client):
        """Test successful starred repos fetch."""
        mock_user = MagicMock()
        mock_repo = MagicMock()
        mock_repo.name = "starred-repo"
        mock_repo.full_name = "other/starred-repo"
        mock_repo.language = "Python"
        mock_repo.stargazers_count = 100
        mock_repo.description = "A starred repo"
        mock_repo.get_topics = MagicMock(return_value=["python", "testing"])

        mock_user.get_starred.return_value = [mock_repo]
        mock_github_client.get_user.return_value = mock_user

        result = fetch_starred_repos(mock_github_client, "testuser", max_stars=10)

        assert len(result) == 1
        assert result[0]["name"] == "starred-repo"
        assert result[0]["stars"] == 100


class TestFetchRepos:
    """Tests for fetch_repos."""

    def test_fetch_repos_excludes_forks(self, mock_github_client):
        """Test that fork repos are excluded."""
        mock_user = MagicMock()

        # Create mock repos
        regular_repo = MagicMock()
        regular_repo.fork = False
        regular_repo.name = "regular-repo"
        regular_repo.full_name = "testuser/regular-repo"
        regular_repo.language = "Python"
        regular_repo.stargazers_count = 50
        regular_repo.forks_count = 10
        regular_repo.watchers_count = 5
        regular_repo.created_at = Mock()
        regular_repo.created_at.__str__ = Mock(return_value="2021-01-01")
        regular_repo.updated_at = Mock()
        regular_repo.updated_at.__str__ = Mock(return_value="2024-01-01")
        regular_repo.pushed_at = Mock()
        regular_repo.pushed_at.__str__ = Mock(return_value="2024-01-01")
        regular_repo.size = 1000
        regular_repo.description = "A regular repo"
        regular_repo.homepage = None
        regular_repo.get_topics = MagicMock(return_value=[])
        regular_repo.license = None
        regular_repo.open_issues_count = 2
        regular_repo.default_branch = "main"
        regular_repo.archived = False
        regular_repo.disabled = False
        regular_repo.has_issues = True
        regular_repo.has_wiki = True
        regular_repo.has_projects = False
        regular_repo.has_pages = False
        regular_repo.has_downloads = False
        regular_repo.allow_forking = True
        regular_repo.visibility = "public"
        regular_repo.mirror_url = None
        regular_repo.archived_at = None

        fork_repo = MagicMock()
        fork_repo.fork = True
        fork_repo.name = "fork-repo"

        mock_user.get_repos.return_value = [regular_repo, fork_repo]
        mock_github_client.get_user.return_value = mock_user

        result = fetch_repos(mock_github_client, "testuser")

        assert len(result) == 1
        assert result[0]["name"] == "regular-repo"


class TestFetchLanguages:
    """Tests for fetch_languages."""

    def test_fetch_languages_aggregates(self, mock_github_client):
        """Test that languages are aggregated across repos."""
        repos = [
            {"full_name": "testuser/repo1"},
            {"full_name": "testuser/repo2"},
        ]

        mock_repo1 = MagicMock()
        mock_repo1.get_languages.return_value = {"Python": 1000, "JavaScript": 500}

        mock_repo2 = MagicMock()
        mock_repo2.get_languages.return_value = {"Python": 2000, "Go": 300}

        mock_github_client.get_repo.side_effect = [mock_repo1, mock_repo2]

        result = fetch_languages(mock_github_client, repos)

        assert result["Python"] == 3000  # 1000 + 2000
        assert result["JavaScript"] == 500
        assert result["Go"] == 300


class TestFetchRepoStructure:
    """Tests for fetch_repo_structure."""

    def test_fetch_repo_structure(self, mock_github_client):
        """Test repository structure detection."""
        mock_repo = MagicMock()
        mock_repo.default_branch = "main"

        mock_tree = MagicMock()
        mock_tree.tree = [
            MagicMock(path="src/main.py", type="blob"),
            MagicMock(path="test/test_main.py", type="blob"),
            MagicMock(path="README.md", type="blob"),
        ]

        mock_repo.get_git_tree.return_value = mock_tree
        mock_github_client.get_repo.return_value = mock_repo

        result = fetch_repo_structure(mock_github_client, "testuser/repo")

        assert result["has_tests"] is True
        assert result["has_readme"] is True


class TestFetchBranches:
    """Tests for fetch_branches."""

    def test_fetch_branches(self, mock_github_client):
        """Test branch fetching."""
        mock_repo = MagicMock()
        mock_repo.default_branch = "main"

        mock_branch = MagicMock()
        mock_branch.name = "feature-branch"
        mock_branch.protected = True
        mock_branch.commit.sha = "abc123def456789"

        mock_repo.get_branches.return_value = [mock_branch]
        mock_github_client.get_repo.return_value = mock_repo

        result = fetch_branches(mock_github_client, "testuser/repo")

        assert len(result) == 1
        assert result[0]["name"] == "feature-branch"
        assert result[0]["is_protected"] is True


class TestFetchCommits:
    """Tests for fetch_commits."""

    def test_fetch_commits_with_metrics(self, mock_github_client):
        """Test commit fetching with deep metrics."""
        mock_repo = MagicMock()

        mock_commit = MagicMock()
        mock_commit.sha = "abc123"
        mock_commit.commit.message = "feat: add feature"
        mock_commit.commit.author.date = Mock()
        mock_commit.commit.author.date.weekday.return_value = 0
        mock_commit.commit.author.date.hour = 10
        mock_commit.commit.author.date.year = 2024
        mock_commit.commit.author.date.month = 1
        mock_commit.commit.author.name = "Test User"
        mock_commit.commit.author.email = "test@test.dev"
        mock_commit.commit.committer.date = Mock()
        mock_commit.commit.committer.name = "Test User"
        mock_commit.commit.verification.verified = True
        mock_commit.parents = []

        mock_commit.stats.additions = 50
        mock_commit.stats.deletions = 5
        mock_commit.stats.total = 55

        mock_commit.files = []

        mock_repo.get_commits.return_value = [mock_commit]
        mock_github_client.get_repo.return_value = mock_repo

        result = fetch_commits(mock_github_client, "testuser/repo", max_commits=5)

        assert len(result) == 1
        assert result[0]["sha"] == "abc123"
        assert result[0]["commit_type"] == "feat"
        assert result[0]["additions"] == 50


class TestClassifyCommitMessage:
    """Tests for commit message classification (imported from test_commits)."""

    def test_feat_classification(self):
        """Test feature commit classification."""
        assert classify_commit_message("feat: add new button") == "feat"
        assert classify_commit_message("Add new feature") == "feat"

    def test_fix_classification(self):
        """Test fix commit classification."""
        assert classify_commit_message("fix: resolve issue") == "fix"
        assert classify_commit_message("Bugfix: null error") == "fix"

    def test_refactor_classification(self):
        """Test refactor commit classification."""
        assert classify_commit_message("refactor: simplify logic") == "refactor"
        assert classify_commit_message("Restructure code") == "refactor"
