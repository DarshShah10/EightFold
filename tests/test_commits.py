"""
Tests for Commit Classification
===============================
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.fetchers.commits import classify_commit_message


class TestClassifyCommitMessage:
    """Tests for commit message classification."""

    def test_classify_feature(self):
        """Test feature commit classification."""
        assert classify_commit_message("feat: add new button") == "feat"
        assert classify_commit_message("Add new feature") == "feat"
        assert classify_commit_message("Implement login") == "feat"
        assert classify_commit_message("new: add support for X") == "feat"

    def test_classify_fix(self):
        """Test fix commit classification."""
        assert classify_commit_message("fix: resolve issue #123") == "fix"
        assert classify_commit_message("Bugfix: null pointer error") == "fix"
        assert classify_commit_message("hotfix: urgent patch") == "fix"
        assert classify_commit_message("Fix memory leak") == "fix"

    def test_classify_refactor(self):
        """Test refactor commit classification."""
        assert classify_commit_message("refactor: simplify logic") == "refactor"
        assert classify_commit_message("Restructure codebase") == "refactor"
        assert classify_commit_message("cleanup: remove dead code") == "refactor"
        assert classify_commit_message("Clean up imports") == "refactor"

    def test_classify_docs(self):
        """Test docs commit classification."""
        assert classify_commit_message("docs: update README") == "docs"
        assert classify_commit_message("Documentation updates") == "docs"
        assert classify_commit_message("Update changelog") == "docs"

    def test_classify_test(self):
        """Test test commit classification - messages containing 'test' keyword."""
        # Note: Priority order means 'add' in feat pattern beats 'test' pattern
        # So messages with 'add' return 'feat'
        # Messages without 'add' that contain 'test' return 'test'
        assert classify_commit_message("test suite coverage update") == "test"
        assert classify_commit_message("testsuite for module") == "test"
        assert classify_commit_message("coverage for module") == "test"

    def test_classify_performance(self):
        """Test performance commit classification."""
        assert classify_commit_message("perf: optimize query") == "perf"
        assert classify_commit_message("Optimize performance") == "perf"
        assert classify_commit_message("Speed up rendering") == "perf"

    def test_classify_chore(self):
        """Test chore commit classification."""
        assert classify_commit_message("chore: update dependencies") == "chore"
        assert classify_commit_message("bump: version bump") == "chore"
        assert classify_commit_message("deps: upgrade packages") == "chore"

    def test_classify_security(self):
        """Test security commit classification."""
        assert classify_commit_message("security: fix vulnerability") == "security"
        assert classify_commit_message("secur: patch auth") == "security"
        assert classify_commit_message("Address CVE-2024-1234") == "security"

    def test_classify_ci(self):
        """Test CI commit classification."""
        assert classify_commit_message("ci: github action setup") == "ci"
        assert classify_commit_message("pipeline: configure CI") == "ci"
        assert classify_commit_message("Jenkinsfile updates") == "ci"

    def test_classify_revert(self):
        """Test revert commit classification."""
        assert classify_commit_message("revert: undo last change") == "revert"
        assert classify_commit_message("Revert commit abc123") == "revert"
        assert classify_commit_message("Undo changes") == "revert"

    def test_classify_other(self):
        """Test unknown commit classification."""
        # Messages that don't match any pattern
        assert classify_commit_message("magic commit") == "other"
        assert classify_commit_message("WIP") == "other"
        assert classify_commit_message("minor tweaks") == "other"

    def test_case_insensitive(self):
        """Test that classification is case insensitive."""
        assert classify_commit_message("FEAT: Add feature") == "feat"
        assert classify_commit_message("Fix: bug fix") == "fix"
        assert classify_commit_message("REFACTOR: cleanup") == "refactor"

    def test_priority_order(self):
        """Test that security takes priority over fix."""
        assert classify_commit_message("security fix for bug") == "security"

    def test_priority_order_fix_before_feat(self):
        """Test that fix takes priority over feat."""
        assert classify_commit_message("fix and add new feature") == "fix"
