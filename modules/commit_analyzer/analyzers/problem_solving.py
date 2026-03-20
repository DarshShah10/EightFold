"""
Problem Solving Analyzer
========================
Analyzes bug fixing, refactoring, and test coverage patterns.

Signals extracted:
- refactor_ratio
- fix_ratio
- feat_ratio
- perf_ratio
- avg_churn_ratio
- refactor_churn_ratio (churn near 1.0 indicates understanding)
- test_coverage_ratio (test files touched)
- bug_fix_to_feature_ratio
- hotfix_ratio (urgent fixes)
- large_refactor_commits
- churn_variance (diverse problem types)
- fix_complexity (files per fix commit)
"""

import re
import statistics
from typing import Any, Dict, List


class ProblemSolvingAnalyzer:
    """
    Analyzes problem-solving patterns from commit types and churn.

    High problem-solving signals:
    - High refactor ratio (code understanding)
    - Balanced churn (adds ≈ deletes)
    - Bug fix to feature ratio
    - Test coverage awareness
    - Performance optimization commits
    """

    # Hotfix indicators (urgent fixes)
    HOTFIX_PATTERNS = [
        re.compile(r'hotfix', re.IGNORECASE),
        re.compile(r'urgent', re.IGNORECASE),
        re.compile(r'critical', re.IGNORECASE),
        re.compile(r'emergency', re.IGNORECASE),
    ]

    def analyze(self, commits: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract problem-solving signals from commits.

        Args:
            commits: List of commit dictionaries

        Returns:
            Dictionary of signal name -> value
        """
        signals: Dict[str, float] = {}

        if not commits:
            return self._empty_signals()

        total = len(commits)

        # Count commit types
        type_counts = {
            "fix": 0,
            "feat": 0,
            "refactor": 0,
            "perf": 0,
            "test": 0,
            "docs": 0,
            "security": 0,
            "chore": 0,
            "ci": 0,
            "other": 0,
        }

        churn_ratios = []
        refactor_churns = []
        fix_churns = []
        hotfix_count = 0
        test_files_touched = 0
        total_files_touched = 0
        fix_files_per_commit = []
        large_refactors = 0

        for commit in commits:
            commit_type = commit.get("commit_type", "other")
            if commit_type in type_counts:
                type_counts[commit_type] += 1
            else:
                type_counts["other"] += 1

            # Check for hotfix
            message = commit.get("message", "") or ""
            for pattern in self.HOTFIX_PATTERNS:
                if pattern.search(message):
                    hotfix_count += 1
                    break

            # Calculate churn from files
            files = commit.get("files", [])
            additions = 0
            deletions = 0

            for file_data in files:
                additions += file_data.get("additions", 0)
                deletions += file_data.get("deletions", 0)
                total_files_touched += 1

                # Track test files
                filename = file_data.get("filename", "")
                if self._is_test_file(filename):
                    test_files_touched += 1

            # Compute churn ratio
            if additions > 0 or deletions > 0:
                churn = additions / max(1, deletions)
                churn_ratios.append(churn)

                # Refactor churns (ratio near 1.0)
                if 0.5 <= churn <= 1.5 and additions > 50 and deletions > 50:
                    refactor_churns.append(churn)

                # Fix churns
                if commit_type == "fix":
                    fix_churns.append(churn)
                    fix_files_per_commit.append(len(files))

            # Large refactor commits (>10 files, significant changes)
            if commit_type == "refactor" and len(files) > 10:
                large_refactors += 1

        # Compute type ratios
        signals["fix_ratio"] = round(type_counts["fix"] / total, 4)
        signals["feat_ratio"] = round(type_counts["feat"] / total, 4)
        signals["refactor_ratio"] = round(type_counts["refactor"] / total, 4)
        signals["perf_ratio"] = round(type_counts["perf"] / total, 4)
        signals["test_ratio"] = round(type_counts["test"] / total, 4)
        signals["docs_ratio"] = round(type_counts["docs"] / total, 4)
        signals["security_ratio"] = round(type_counts["security"] / total, 4)
        signals["chore_ratio"] = round(type_counts["chore"] / total, 4)
        signals["ci_ratio"] = round(type_counts["ci"] / total, 4)

        # Bug fix to feature ratio
        if type_counts["feat"] > 0:
            signals["bug_fix_to_feature_ratio"] = round(type_counts["fix"] / type_counts["feat"], 2)
        else:
            signals["bug_fix_to_feature_ratio"] = type_counts["fix"]

        # Hotfix ratio
        signals["hotfix_ratio"] = round(hotfix_count / total, 4)

        # Churn statistics
        if churn_ratios:
            signals["avg_churn_ratio"] = round(statistics.mean(churn_ratios), 3)
            signals["churn_ratio_std"] = round(statistics.stdev(churn_ratios), 3) if len(churn_ratios) > 1 else 0.0
            signals["churn_ratio_median"] = round(statistics.median(churn_ratios), 3)

            # Variance in churn (diverse problem types)
            sorted_churns = sorted(churn_ratios)
            if len(sorted_churns) > 1:
                q75, q25 = sorted_churns[int(len(sorted_churns) * 0.75)], sorted_churns[int(len(sorted_churns) * 0.25)]
                signals["churn_variance"] = round(q75 - q25, 3)
            else:
                signals["churn_variance"] = 0.0

        # Refactor churn (indicates code understanding)
        if refactor_churns:
            signals["refactor_churn_ratio"] = round(statistics.mean(refactor_churns), 3)
            signals["refactor_commits"] = len(refactor_churns)
        else:
            signals["refactor_churn_ratio"] = 0.0
            signals["refactor_commits"] = type_counts["refactor"]

        # Fix analysis
        if fix_churns:
            signals["avg_fix_churn"] = round(statistics.mean(fix_churns), 3)
        else:
            signals["avg_fix_churn"] = 0.0

        if fix_files_per_commit:
            signals["avg_fix_files"] = round(statistics.mean(fix_files_per_commit), 1)
        else:
            signals["avg_fix_files"] = 0.0

        # Test coverage ratio
        signals["test_coverage_ratio"] = round(test_files_touched / max(1, total_files_touched), 4)

        # Large refactors
        signals["large_refactor_commits"] = large_refactors

        # Problem solving score (0-100)
        signals["problem_solving_score"] = self._compute_problem_solving_score(signals, type_counts)

        return signals

    def _is_test_file(self, filename: str) -> bool:
        """Check if file is a test file."""
        if not filename:
            return False
        lower = filename.lower()
        return (
            "test" in lower or
            "spec" in lower or
            "__tests__" in lower or
            "/tests/" in lower or
            "\\tests\\" in lower
        )

    def _compute_problem_solving_score(self, signals: Dict[str, float], type_counts: Dict[str, int]) -> float:
        """Compute problem-solving score (0-100)."""
        score = 0.0

        # Refactoring discipline (25%)
        refactor_ratio = signals.get("refactor_ratio", 0)
        if refactor_ratio >= 0.15:
            score += 25
        elif refactor_ratio >= 0.08:
            score += 15
        elif refactor_ratio > 0:
            score += 5

        # Balanced churn (20%) - ratio near 1.0
        avg_churn = signals.get("avg_churn_ratio", 0)
        if avg_churn > 0:
            churn_score = max(0, 20 - abs(1.0 - avg_churn) * 10)
            score += churn_score

        # Test coverage (15%)
        test_ratio = signals.get("test_coverage_ratio", 0)
        score += min(test_ratio * 30, 15)

        # Bug fix quality (15%)
        fix_ratio = signals.get("fix_ratio", 0)
        avg_fix_files = signals.get("avg_fix_files", 0)
        # Good fixes are focused (low files) and there's a balance of fixes
        if fix_ratio > 0 and avg_fix_files > 0:
            fix_focus = max(0, 15 - (avg_fix_files - 1) * 2)
            score += fix_focus

        # Feature development (15%)
        feat_ratio = signals.get("feat_ratio", 0)
        score += min(feat_ratio * 30, 15)

        # Performance focus (10%)
        perf_ratio = signals.get("perf_ratio", 0)
        score += min(perf_ratio * 100, 10)

        return round(min(score, 100), 1)

    def _empty_signals(self) -> Dict[str, float]:
        """Return empty signals dictionary."""
        return {
            "fix_ratio": 0.0,
            "feat_ratio": 0.0,
            "refactor_ratio": 0.0,
            "perf_ratio": 0.0,
            "test_ratio": 0.0,
            "docs_ratio": 0.0,
            "security_ratio": 0.0,
            "chore_ratio": 0.0,
            "ci_ratio": 0.0,
            "bug_fix_to_feature_ratio": 0.0,
            "hotfix_ratio": 0.0,
            "avg_churn_ratio": 0.0,
            "churn_ratio_std": 0.0,
            "churn_ratio_median": 0.0,
            "churn_variance": 0.0,
            "refactor_churn_ratio": 0.0,
            "refactor_commits": 0,
            "avg_fix_churn": 0.0,
            "avg_fix_files": 0.0,
            "test_coverage_ratio": 0.0,
            "large_refactor_commits": 0,
            "problem_solving_score": 0.0,
        }
