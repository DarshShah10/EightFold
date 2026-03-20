"""
Engineering Maturity Analyzer
==============================
Analyzes commit discipline, release patterns, and overall engineering maturity.

Signals extracted:
- avg_commit_size
- large_commit_ratio (negative)
- tiny_commit_ratio (negative)
- merge_commit_ratio
- commit_size_std
- commit_consistency_score
- release_awareness (has releases)
- semantic_versioning_ratio
- changelog_awareness
- dependency_update_discipline
- ci_pipeline_presence
- documentation_presence
"""

import re
import statistics
from typing import Any, Dict, List


class MaturityAnalyzer:
    """
    Analyzes engineering maturity signals from commit and repo patterns.

    High maturity signals:
    - Consistent, moderate commit sizes
    - Low large commit ratio
    - Semantic versioning awareness
    - CI/CD pipeline presence
    - Documentation discipline
    """

    # Semantic version patterns
    SEMVER_PATTERNS = [
        re.compile(r'\bv?(\d+)\.(\d+)\.(\d+)\b'),  # 1.2.3
        re.compile(r'version\s+(\d+)\.(\d+)\.(\d+)', re.IGNORECASE),
        re.compile(r'release\s+(\d+)\.(\d+)\.(\d+)', re.IGNORECASE),
    ]

    def analyze(self, commits: List[Dict[str, Any]], repos: List[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Extract engineering maturity signals from commits and repos.

        Args:
            commits: List of commit dictionaries
            repos: Optional list of repo dictionaries for context

        Returns:
            Dictionary of signal name -> value
        """
        signals: Dict[str, float] = {}

        if not commits:
            return self._empty_signals()

        # Calculate commit sizes
        commit_sizes = []
        for commit in commits:
            total_lines = 0
            for file_data in commit.get("files", []):
                total_lines += file_data.get("additions", 0)
                total_lines += file_data.get("deletions", 0)
            commit_sizes.append(total_lines)

        total = len(commits)

        # Commit size stats
        if commit_sizes:
            signals["avg_commit_size"] = round(statistics.mean(commit_sizes), 1)
            signals["median_commit_size"] = round(statistics.median(commit_sizes), 1)
            signals["commit_size_std"] = round(statistics.stdev(commit_sizes), 1) if len(commit_sizes) > 1 else 0.0
            signals["max_commit_size"] = max(commit_sizes)

            # Large commits (>500 lines)
            large_count = sum(1 for s in commit_sizes if s > 500)
            signals["large_commit_ratio"] = round(large_count / total, 4)

            # Tiny commits (<10 lines)
            tiny_count = sum(1 for s in commit_sizes if s < 10)
            signals["tiny_commit_ratio"] = round(tiny_count / total, 4)

            # Optimal commits (50-300 lines)
            optimal_count = sum(1 for s in commit_sizes if 50 <= s <= 300)
            signals["optimal_commit_ratio"] = round(optimal_count / total, 4)

        # Merge commits
        merge_count = sum(1 for c in commits if c.get("is_merge", False) or c.get("num_parents", 0) > 1)
        signals["merge_commit_ratio"] = round(merge_count / total, 4)

        # Parent count analysis
        parent_counts = [c.get("num_parents", 1) for c in commits]
        signals["avg_parents"] = round(statistics.mean(parent_counts), 2)

        # Commit consistency score (based on size variance)
        if commit_sizes and len(commit_sizes) > 1:
            mean_size = statistics.mean(commit_sizes)
            if mean_size > 0:
                # Coefficient of variation (lower = more consistent)
                cv = statistics.stdev(commit_sizes) / mean_size
                # Map CV to score: 0 CV = 100, 1 CV = 50, 2+ CV = 0
                signals["commit_consistency_score"] = round(max(0, 100 - cv * 50), 1)
            else:
                signals["commit_consistency_score"] = 100.0
        else:
            signals["commit_consistency_score"] = 100.0

        # Analyze commits for patterns
        semantic_version_count = 0
        changelog_count = 0
        dependency_count = 0

        for commit in commits:
            message = (commit.get("message", "") or "") + " " + (commit.get("message_full", "") or "")

            # Semantic versioning
            for pattern in self.SEMVER_PATTERNS:
                if pattern.search(message):
                    semantic_version_count += 1
                    break

            # Changelog awareness
            if "changelog" in message.lower() or "release notes" in message.lower():
                changelog_count += 1

            # Dependency updates
            files = commit.get("files", [])
            for file_data in files:
                filename = file_data.get("filename", "").lower()
                if any(x in filename for x in ["package.json", "requirements.txt", "pom.xml", "Cargo.toml", "go.mod"]):
                    dependency_count += 1
                    break

        signals["semantic_versioning_ratio"] = round(semantic_version_count / total, 4)
        signals["changelog_awareness"] = round(changelog_count / total, 4)
        signals["dependency_update_discipline"] = round(dependency_count / total, 4)

        # Repository context signals
        if repos:
            signals["repo_count"] = len(repos)

            # CI presence
            ci_count = sum(1 for r in repos if r.get("structure", {}).get("has_ci", False))
            signals["ci_pipeline_ratio"] = round(ci_count / len(repos), 4)

            # Documentation presence
            docs_count = sum(1 for r in repos if r.get("structure", {}).get("has_readme", False))
            signals["documentation_ratio"] = round(docs_count / len(repos), 4)

            # License presence (maturity signal)
            license_count = sum(1 for r in repos if r.get("license"))
            signals["license_presence_ratio"] = round(license_count / len(repos), 4)

            # GitHub Actions usage
            actions_count = sum(1 for r in repos if ".github/workflows" in str(r.get("structure", {})))
            signals["github_actions_ratio"] = round(actions_count / len(repos), 4)

            # Release presence
            has_releases = sum(1 for r in repos if r.get("releases") and len(r.get("releases", [])) > 0)
            signals["release_awareness"] = round(has_releases / len(repos), 4)

            # Stars as quality signal
            total_stars = sum(r.get("stargazers", 0) for r in repos)
            signals["total_stars"] = total_stars
            signals["avg_repo_stars"] = round(total_stars / len(repos), 1)

        # Overall maturity score (0-100)
        signals["engineering_maturity_score"] = self._compute_maturity_score(signals)

        return signals

    def _compute_maturity_score(self, signals: Dict[str, float]) -> float:
        """Compute overall engineering maturity score (0-100)."""
        score = 0.0

        # Commit discipline (30%)
        consistency = signals.get("commit_consistency_score", 0)
        optimal_ratio = signals.get("optimal_commit_ratio", 0)
        commit_discipline = (consistency * 0.5 + optimal_ratio * 100 * 0.5) / 100 * 30
        score += commit_discipline

        # Low large commit ratio (15%)
        large_ratio = signals.get("large_commit_ratio", 0)
        score += max(0, 15 - large_ratio * 100)

        # Merge strategy (10%)
        merge_ratio = signals.get("merge_commit_ratio", 0)
        # Some merges are good (collaboration), too many = messy history
        if 0.05 <= merge_ratio <= 0.25:
            score += 10
        elif merge_ratio < 0.05:
            score += 5  # Might be solo dev
        else:
            score += max(0, 10 - (merge_ratio - 0.25) * 40)

        # Semantic versioning (15%)
        semver_ratio = signals.get("semantic_versioning_ratio", 0)
        score += min(semver_ratio * 100, 15)

        # Documentation (15%)
        docs_ratio = signals.get("documentation_ratio", 0)
        score += min(docs_ratio * 100, 15)

        # CI/CD (15%)
        ci_ratio = signals.get("ci_pipeline_ratio", 0)
        score += min(ci_ratio * 100, 15)

        return round(min(score, 100), 1)

    def _empty_signals(self) -> Dict[str, float]:
        """Return empty signals dictionary."""
        return {
            "avg_commit_size": 0.0,
            "median_commit_size": 0.0,
            "commit_size_std": 0.0,
            "max_commit_size": 0,
            "large_commit_ratio": 0.0,
            "tiny_commit_ratio": 0.0,
            "optimal_commit_ratio": 0.0,
            "merge_commit_ratio": 0.0,
            "avg_parents": 1.0,
            "commit_consistency_score": 0.0,
            "semantic_versioning_ratio": 0.0,
            "changelog_awareness": 0.0,
            "dependency_update_discipline": 0.0,
            "ci_pipeline_ratio": 0.0,
            "documentation_ratio": 0.0,
            "license_presence_ratio": 0.0,
            "github_actions_ratio": 0.0,
            "release_awareness": 0.0,
            "total_stars": 0,
            "avg_repo_stars": 0.0,
            "engineering_maturity_score": 0.0,
        }
