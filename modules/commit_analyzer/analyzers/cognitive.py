"""
Cognitive Load Analyzer
=======================
Measures complexity, files spread, and architectural work signals.

Signals extracted:
- files_per_commit_mean, files_per_commit_median
- files_per_commit_p75, files_per_commit_p90
- multi_module_commits (touches multiple directories)
- cross_boundary_commits (frontend/backend/infra)
- avg_files_per_commit_weighted (by commit size)
- max_files_in_single_commit
- architectural_complexity_score
"""

import re
import statistics
from typing import Any, Dict, List, Set


class CognitiveAnalyzer:
    """
    Analyzes cognitive load signals from commit patterns.

    High cognitive load signals:
    - Many files per commit (architectural awareness)
    - Cross-module changes (system thinking)
    - High variance in file counts (adaptable scope)
    """

    # Directory patterns for cross-boundary detection
    BOUNDARY_PATTERNS = {
        "frontend": ["frontend", "client", "ui", "web", "app", "views"],
        "backend": ["backend", "server", "api", "services", "handlers"],
        "infrastructure": ["infra", "devops", "deploy", "ci", "docker", "k8s", "terraform"],
        "data": ["data", "ml", "models", "analytics", "db", "database", "migrations"],
        "config": ["config", "settings", ".github", "scripts"],
    }

    def analyze(self, commits: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract cognitive load signals from commits.

        Args:
            commits: List of commit dictionaries

        Returns:
            Dictionary of signal name -> value
        """
        signals: Dict[str, float] = {}

        if not commits:
            return self._empty_signals()

        # Extract file counts per commit
        file_counts = []
        multi_module_commits = 0
        cross_boundary_commits = 0
        weighted_file_counts = []
        max_files = 0
        all_directories: Set[str] = set()

        for commit in commits:
            files = commit.get("files", [])
            num_files = len(files)
            file_counts.append(num_files)

            if num_files > max_files:
                max_files = num_files

            # Calculate weighted files (normalized by commit size)
            total_lines = sum(
                f.get("additions", 0) + f.get("deletions", 0)
                for f in files
            )
            if total_lines > 0:
                weighted = num_files / (total_lines / 100)  # files per 100 lines
                weighted_file_counts.append(min(weighted, 10))  # cap at 10

            # Check for multi-module commits
            directories = self._extract_directories(files)
            all_directories.update(directories)

            if len(directories) > 1:
                multi_module_commits += 1

            # Check for cross-boundary commits
            if self._is_cross_boundary(commit, files):
                cross_boundary_commits += 1

        # Calculate statistics
        if file_counts:
            sorted_counts = sorted(file_counts)
            n = len(sorted_counts)

            signals["files_per_commit_mean"] = round(statistics.mean(file_counts), 3)
            signals["files_per_commit_median"] = statistics.median(file_counts)
            signals["files_per_commit_std"] = round(statistics.stdev(file_counts), 3) if len(file_counts) > 1 else 0.0
            signals["files_per_commit_p75"] = self._percentile(sorted_counts, 0.75)
            signals["files_per_commit_p90"] = self._percentile(sorted_counts, 0.90)
            signals["max_files_in_single_commit"] = max_files

        if weighted_file_counts:
            signals["avg_files_per_commit_weighted"] = round(statistics.mean(weighted_file_counts), 3)

        total_commits = len(commits)
        signals["multi_module_commit_ratio"] = round(multi_module_commits / total_commits, 4) if total_commits else 0.0
        signals["cross_boundary_commit_ratio"] = round(cross_boundary_commits / total_commits, 4) if total_commits else 0.0

        # Architectural complexity score (0-100)
        signals["architectural_complexity_score"] = self._compute_complexity_score(signals, len(all_directories))

        return signals

    def _extract_directories(self, files: List[Dict[str, Any]]) -> Set[str]:
        """Extract unique top-level directories from file paths."""
        directories: Set[str] = set()

        for file_data in files:
            filepath = file_data.get("filename", "")
            if not filepath:
                continue

            parts = filepath.split("/")
            if len(parts) >= 2:
                directories.add(parts[0])
            elif len(parts) == 1:
                directories.add("root")

        return directories

    def _is_cross_boundary(self, commit: Dict[str, Any], files: List[Dict[str, Any]]) -> bool:
        """Check if commit touches multiple architectural boundaries."""
        touched_boundaries: Set[str] = set()

        for file_data in files:
            filepath = file_data.get("filename", "").lower()
            filename = filepath.split("/")[-1] if "/" in filepath else filepath

            for boundary, patterns in self.BOUNDARY_PATTERNS.items():
                if any(p in filepath for p in patterns) or any(p in filename for p in patterns):
                    touched_boundaries.add(boundary)

        return len(touched_boundaries) >= 2

    def _percentile(self, sorted_data: List, p: float) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        idx = int(len(sorted_data) * p)
        if idx >= len(sorted_data):
            idx = len(sorted_data) - 1
        return sorted_data[idx]

    def _compute_complexity_score(self, signals: Dict[str, float], num_directories: int) -> float:
        """Compute overall architectural complexity score (0-100)."""
        score = 0.0

        # Files spread contributes 40%
        mean_files = signals.get("files_per_commit_mean", 0)
        files_component = min(mean_files / 5, 1.0) * 40

        # Multi-module ratio contributes 30%
        multi_module = signals.get("multi_module_commit_ratio", 0)
        multi_component = min(multi_module / 0.3, 1.0) * 30

        # Cross-boundary ratio contributes 20%
        cross_boundary = signals.get("cross_boundary_commit_ratio", 0)
        cross_component = min(cross_boundary / 0.15, 1.0) * 20

        # Directory diversity contributes 10%
        dir_component = min(num_directories / 10, 1.0) * 10

        return round(files_component + multi_component + cross_component + dir_component, 1)

    def _empty_signals(self) -> Dict[str, float]:
        """Return empty signals dictionary."""
        return {
            "files_per_commit_mean": 0.0,
            "files_per_commit_median": 0.0,
            "files_per_commit_std": 0.0,
            "files_per_commit_p75": 0.0,
            "files_per_commit_p90": 0.0,
            "max_files_in_single_commit": 0,
            "avg_files_per_commit_weighted": 0.0,
            "multi_module_commit_ratio": 0.0,
            "cross_boundary_commit_ratio": 0.0,
            "architectural_complexity_score": 0.0,
        }
