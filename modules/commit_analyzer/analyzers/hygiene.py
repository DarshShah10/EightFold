"""
Code Hygiene Analyzer
=====================
Analyzes commit quality, message patterns, and signed commits.

Signals extracted:
- signed_commit_ratio
- verified_commit_ratio
- conventional_commit_ratio
- message_length_avg
- message_length_min (indicates care)
- issue_reference_ratio (links to issues)
- pr_reference_ratio (links to PRs)
- revert_ratio (negative signal)
- empty_message_ratio (negative signal)
- cleanup_commit_ratio (chores/formatting)
- test_documentation_ratio
- breaking_change_awareness
"""

import re
import statistics
from typing import Any, Dict, List


class HygieneAnalyzer:
    """
    Analyzes code hygiene signals from commit patterns.

    High hygiene signals:
    - Signed/verified commits
    - Conventional commit messages
    - Meaningful message length
    - References to issues/PRs
    - Low revert ratio
    """

    # Conventional commit pattern: type(scope): description
    CONVENTIONAL_COMMIT_PATTERN = re.compile(
        r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)'
        r'(\([\w\-]+\))?\s*:\s*.+',
        re.IGNORECASE
    )

    # Issue reference patterns
    ISSUE_PATTERNS = [
        re.compile(r'#(\d+)', re.IGNORECASE),
        re.compile(r'(?:closes?|fixes?|resolves?)\s+#(\d+)', re.IGNORECASE),
    ]

    # PR reference patterns
    PR_PATTERNS = [
        re.compile(r'Merge pull request #(\d+)', re.IGNORECASE),
        re.compile(r'!(\d+)', re.IGNORECASE),
    ]

    # Breaking change indicators
    BREAKING_PATTERNS = [
        re.compile(r'BREAKING[- ]CHANGE', re.IGNORECASE),
        re.compile(r'^[^:]+!:', re.MULTILINE),  # type!(): description
    ]

    # Cleanup indicators
    CLEANUP_PATTERNS = [
        re.compile(r'^(chore|ci|build|style|fmt|format|refactor)\s*[:\(]', re.IGNORECASE),
    ]

    def analyze(self, commits: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract code hygiene signals from commits.

        Args:
            commits: List of commit dictionaries

        Returns:
            Dictionary of signal name -> value
        """
        signals: Dict[str, float] = {}

        if not commits:
            return self._empty_signals()

        total = len(commits)
        signed_count = 0
        verified_count = 0
        conventional_count = 0
        issue_ref_count = 0
        pr_ref_count = 0
        revert_count = 0
        empty_count = 0
        cleanup_count = 0
        breaking_count = 0
        message_lengths = []
        test_doc_count = 0

        for commit in commits:
            message = commit.get("message", "") or ""
            message_full = commit.get("message_full", "") or message

            # Signed/verified
            if commit.get("verified", False):
                verified_count += 1
                signed_count += 1  # GitHub shows verified as signed
            elif commit.get("author_email"):  # Has author info = some level of identity
                signed_count += 0.5  # Partial credit

            # Conventional commit
            if self.CONVENTIONAL_COMMIT_PATTERN.match(message.strip()):
                conventional_count += 1

            # Issue references
            for pattern in self.ISSUE_PATTERNS:
                if pattern.search(message_full):
                    issue_ref_count += 1
                    break

            # PR references
            for pattern in self.PR_PATTERNS:
                if pattern.search(message_full):
                    pr_ref_count += 1
                    break

            # Reverts
            if self._is_revert(commit):
                revert_count += 1

            # Breaking changes
            for pattern in self.BREAKING_PATTERNS:
                if pattern.search(message_full):
                    breaking_count += 1
                    break

            # Cleanup commits
            if self._is_cleanup(commit):
                cleanup_count += 1

            # Empty messages
            if not message.strip():
                empty_count += 1

            # Message length
            message_lengths.append(len(message.strip()))

            # Test/documentation commits
            commit_type = commit.get("commit_type", "")
            if commit_type in ("test", "docs"):
                test_doc_count += 1

        # Compute ratios
        signals["signed_commit_ratio"] = round(signed_count / total, 4)
        signals["verified_commit_ratio"] = round(verified_count / total, 4)
        signals["conventional_commit_ratio"] = round(conventional_count / total, 4)
        signals["issue_reference_ratio"] = round(issue_ref_count / total, 4)
        signals["pr_reference_ratio"] = round(pr_ref_count / total, 4)
        signals["revert_ratio"] = round(revert_count / total, 4)
        signals["empty_message_ratio"] = round(empty_count / total, 4)
        signals["cleanup_commit_ratio"] = round(cleanup_count / total, 4)
        signals["breaking_change_ratio"] = round(breaking_count / total, 4)
        signals["test_documentation_ratio"] = round(test_doc_count / total, 4)

        # Message length stats
        if message_lengths:
            signals["message_length_avg"] = round(statistics.mean(message_lengths), 1)
            signals["message_length_min"] = min(message_lengths)
            signals["message_length_max"] = max(message_lengths)
            signals["message_length_std"] = round(statistics.stdev(message_lengths), 1) if len(message_lengths) > 1 else 0.0

        # Hygiene score (0-100)
        signals["overall_hygiene_score"] = self._compute_hygiene_score(signals)

        return signals

    def _is_revert(self, commit: Dict[str, Any]) -> bool:
        """Check if commit is a revert."""
        message = (commit.get("message", "") or "").lower()
        num_parents = commit.get("num_parents", 0)

        if num_parents > 1:
            return True
        if message.startswith("revert"):
            return True
        if "revert" in message and ("this reverts" in message or "reverted" in message):
            return True
        return False

    def _is_cleanup(self, commit: Dict[str, Any]) -> bool:
        """Check if commit is cleanup/chore."""
        message = (commit.get("message", "") or "")
        commit_type = commit.get("commit_type", "")

        if commit_type in ("chore", "ci"):
            return True

        for pattern in self.CLEANUP_PATTERNS:
            if pattern.match(message.strip()):
                return True

        return False

    def _compute_hygiene_score(self, signals: Dict[str, float]) -> float:
        """Compute overall hygiene score (0-100)."""
        score = 0.0

        # Verified commits (25%)
        score += signals.get("verified_commit_ratio", 0) * 25

        # Conventional commits (25%)
        score += signals.get("conventional_commit_ratio", 0) * 25

        # Issue references (15%)
        score += signals.get("issue_reference_ratio", 0) * 15

        # Breaking change awareness (10%)
        score += min(signals.get("breaking_change_ratio", 0) * 2, 10)

        # Low revert ratio (15%)
        revert_ratio = signals.get("revert_ratio", 0)
        score += max(0, 15 - revert_ratio * 100)

        # No empty messages (10%)
        empty_ratio = signals.get("empty_message_ratio", 0)
        score += max(0, 10 - empty_ratio * 50)

        return round(min(score, 100), 1)

    def _empty_signals(self) -> Dict[str, float]:
        """Return empty signals dictionary."""
        return {
            "signed_commit_ratio": 0.0,
            "verified_commit_ratio": 0.0,
            "conventional_commit_ratio": 0.0,
            "message_length_avg": 0.0,
            "message_length_min": 0.0,
            "message_length_max": 0.0,
            "message_length_std": 0.0,
            "issue_reference_ratio": 0.0,
            "pr_reference_ratio": 0.0,
            "revert_ratio": 0.0,
            "empty_message_ratio": 0.0,
            "cleanup_commit_ratio": 0.0,
            "breaking_change_ratio": 0.0,
            "test_documentation_ratio": 0.0,
            "overall_hygiene_score": 0.0,
        }
