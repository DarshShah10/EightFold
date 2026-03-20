"""
Tests for Configuration Module
==============================
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config import (
    DEPENDENCY_FILES,
    STRUCTURE_PATTERNS,
    LANGUAGE_DOMAINS,
    COMMIT_PATTERNS,
    DEFAULTS,
)


class TestDependencyFiles:
    """Tests for dependency files list."""

    def test_has_common_files(self):
        """Test that common dependency files are present."""
        assert 'requirements.txt' in DEPENDENCY_FILES
        assert 'package.json' in DEPENDENCY_FILES
        assert 'Cargo.toml' in DEPENDENCY_FILES
        assert 'go.mod' in DEPENDENCY_FILES
        assert 'pyproject.toml' in DEPENDENCY_FILES

    def test_has_lock_files(self):
        """Test that lock files are present."""
        assert 'package-lock.json' in DEPENDENCY_FILES
        assert 'poetry.lock' in DEPENDENCY_FILES
        assert 'Cargo.lock' in DEPENDENCY_FILES

    def test_is_list(self):
        """Test that DEPENDENCY_FILES is a list."""
        assert isinstance(DEPENDENCY_FILES, list)

    def test_all_strings(self):
        """Test that all entries are strings."""
        assert all(isinstance(f, str) for f in DEPENDENCY_FILES)


class TestStructurePatterns:
    """Tests for structure patterns."""

    def test_has_expected_keys(self):
        """Test that expected keys are present."""
        expected_keys = [
            'has_tests',
            'has_docs',
            'has_ci',
            'has_dockerfile',
            'has_makefile',
            'has_readme',
            'has_license',
            'has_contributing',
            'has_security',
            'has_dependabot',
        ]
        for key in expected_keys:
            assert key in STRUCTURE_PATTERNS

    def test_has_tests_patterns(self):
        """Test test directory patterns."""
        patterns = STRUCTURE_PATTERNS['has_tests']
        assert 'test/' in patterns
        assert 'tests/' in patterns
        assert 'spec/' in patterns

    def test_has_ci_patterns(self):
        """Test CI patterns."""
        patterns = STRUCTURE_PATTERNS['has_ci']
        assert '.github/workflows/' in patterns
        assert '.travis.yml' in patterns
        assert 'Jenkinsfile' in patterns

    def test_is_dict(self):
        """Test that STRUCTURE_PATTERNS is a dict."""
        assert isinstance(STRUCTURE_PATTERNS, dict)

    def test_values_are_lists(self):
        """Test that all pattern values are lists."""
        assert all(isinstance(v, list) for v in STRUCTURE_PATTERNS.values())


class TestLanguageDomains:
    """Tests for language domain mapping."""

    def test_has_expected_languages(self):
        """Test that expected languages are present."""
        expected_langs = [
            'Python', 'JavaScript', 'TypeScript', 'Java',
            'C++', 'Rust', 'Go', 'Swift', 'Kotlin'
        ]
        for lang in expected_langs:
            assert lang in LANGUAGE_DOMAINS

    def test_python_domains(self):
        """Test Python domain assignments."""
        domains = LANGUAGE_DOMAINS['Python']
        assert 'Backend' in domains
        assert 'ML/AI' in domains

    def test_rust_domains(self):
        """Test Rust domain assignments."""
        domains = LANGUAGE_DOMAINS['Rust']
        assert 'Systems' in domains
        assert 'Performance' in domains

    def test_is_dict(self):
        """Test that LANGUAGE_DOMAINS is a dict."""
        assert isinstance(LANGUAGE_DOMAINS, dict)

    def test_values_are_lists(self):
        """Test that all domain values are lists."""
        assert all(isinstance(v, list) for v in LANGUAGE_DOMAINS.values())


class TestCommitPatterns:
    """Tests for commit patterns."""

    def test_has_expected_types(self):
        """Test that expected commit types are present."""
        expected_types = [
            'feat', 'fix', 'refactor', 'docs', 'test',
            'perf', 'chore', 'security', 'ci', 'revert'
        ]
        for commit_type in expected_types:
            assert commit_type in COMMIT_PATTERNS

    def test_patterns_are_strings(self):
        """Test that all patterns are strings."""
        assert all(isinstance(p, str) for p in COMMIT_PATTERNS.values())

    def test_patterns_are_valid_regex(self):
        """Test that patterns are valid regex."""
        import re
        for pattern in COMMIT_PATTERNS.values():
            re.compile(pattern)  # Should not raise


class TestDefaults:
    """Tests for default configuration."""

    def test_has_expected_keys(self):
        """Test that expected default keys are present."""
        expected_keys = [
            'max_commits_per_repo',
            'max_prs_per_repo',
            'max_issues_per_repo',
            'max_events',
            'max_starred',
            'max_top_repos',
        ]
        for key in expected_keys:
            assert key in DEFAULTS

    def test_reasonable_values(self):
        """Test that values are reasonable."""
        assert DEFAULTS['max_commits_per_repo'] <= 100
        assert DEFAULTS['max_prs_per_repo'] <= 50
        assert DEFAULTS['max_events'] <= 500
        assert 5 <= DEFAULTS['max_top_repos'] <= 20

    def test_is_dict(self):
        """Test that DEFAULTS is a dict."""
        assert isinstance(DEFAULTS, dict)

    def test_values_are_integers(self):
        """Test that all default values are integers."""
        assert all(isinstance(v, int) for v in DEFAULTS.values())
