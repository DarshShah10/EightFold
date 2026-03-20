"""
Commit Intelligence Engine - Main Orchestrator
==============================================
State-of-the-art commit analysis with 30+ behavioral signals.

Signals extracted across 5 dimensions:
1. Cognitive Load - complexity, files spread, architectural boundaries
2. Temporal Patterns - time-of-day, day-of-week, velocity patterns
3. Code Hygiene - refactoring discipline, signed commits, message quality
4. Problem Solving - refactor ratio, bug fixing patterns, test coverage
5. Engineering Maturity - commit discipline, merge strategy, release signals

Produces:
- Commit Intelligence Score (0-100)
- Developer personality classification
- Top citations/achievements
"""

import logging
from typing import Any, Dict, List

from modules.commit_analyzer.types import (
    CommitIntelligenceResult,
    DeveloperProfile,
)
from modules.commit_analyzer.analyzers.cognitive import CognitiveAnalyzer
from modules.commit_analyzer.analyzers.temporal import TemporalAnalyzer
from modules.commit_analyzer.analyzers.hygiene import HygieneAnalyzer
from modules.commit_analyzer.analyzers.problem_solving import ProblemSolvingAnalyzer
from modules.commit_analyzer.analyzers.maturity import MaturityAnalyzer
from modules.commit_analyzer.scoring import CommitScorer
from modules.commit_analyzer.profiles import ProfileClassifier
from modules.commit_analyzer.citations import CitationEngine

logger = logging.getLogger(__name__)


class CommitIntelligenceEngine:
    """
    State-of-the-art commit intelligence analysis engine.

    Extracts 30+ signals across 5 behavioral dimensions to produce:
    - Commit Intelligence Score (0-100)
    - Developer personality archetype
    - Notable achievements/citations
    """

    def __init__(self):
        """Initialize all analyzer components."""
        self.cognitive = CognitiveAnalyzer()
        self.temporal = TemporalAnalyzer()
        self.hygiene = HygieneAnalyzer()
        self.problem_solving = ProblemSolvingAnalyzer()
        self.maturity = MaturityAnalyzer()
        self.scorer = CommitScorer()
        self.profiler = ProfileClassifier()
        self.citation_engine = CitationEngine()

    def analyze(self, commits: List[Dict[str, Any]], repos: List[Dict[str, Any]] = None) -> CommitIntelligenceResult:
        """
        Analyze commits and produce complete intelligence report.

        Args:
            commits: List of commit dictionaries from Module 1 (harvester)
            repos: Optional list of repo dictionaries for context

        Returns:
            CommitIntelligenceResult with scores, profile, and citations
        """
        if not commits:
            logger.warning("No commits provided for analysis")
            return CommitIntelligenceResult()

        logger.info(f"Analyzing {len(commits)} commits")

        # Initialize result
        result = CommitIntelligenceResult()
        result.commits_analyzed = len(commits)
        result.repos_analyzed = len(set(c.get("repo_name", "") for c in commits))

        # Calculate date range
        result.date_range_days = self._calculate_date_range(commits)

        # Run all analyzers
        logger.info("Running cognitive load analysis")
        cognitive_signals = self.cognitive.analyze(commits)

        logger.info("Running temporal pattern analysis")
        temporal_signals = self.temporal.analyze(commits)

        logger.info("Running code hygiene analysis")
        hygiene_signals = self.hygiene.analyze(commits)

        logger.info("Running problem-solving analysis")
        problem_signals = self.problem_solving.analyze(commits)

        logger.info("Running engineering maturity analysis")
        maturity_signals = self.maturity.analyze(commits, repos or [])

        # Merge all signals
        all_signals = {**cognitive_signals, **temporal_signals, **hygiene_signals,
                       **problem_signals, **maturity_signals}
        result.signals = all_signals

        # Calculate dimension scores
        result.cognitive_load_score = self.scorer.score_dimension("cognitive_load", cognitive_signals)
        result.temporal_patterns_score = self.scorer.score_dimension("temporal_patterns", temporal_signals)
        result.code_hygiene_score = self.scorer.score_dimension("code_hygiene", hygiene_signals)
        result.problem_solving_score = self.scorer.score_dimension("problem_solving", problem_signals)
        result.engineering_maturity_score = self.scorer.score_dimension("engineering_maturity", maturity_signals)

        # Calculate overall Commit Intelligence Score
        result.commit_intelligence_score = self.scorer.compute_overall_score(result)

        # Classify developer profile
        result.profile = self.profiler.classify(all_signals, result)

        # Extract citations/achievements
        result.citations = self.citation_engine.extract(commits, all_signals, result.profile)

        logger.info(f"Analysis complete. Score: {result.commit_intelligence_score:.1f}")
        return result

    def _calculate_date_range(self, commits: List[Dict[str, Any]]) -> int:
        """Calculate the date range of commits in days."""
        dates = []
        for commit in commits:
            date_str = commit.get("date") or commit.get("author_date")
            if date_str:
                try:
                    from datetime import datetime
                    # Handle various date formats
                    date_str = date_str.replace("Z", "+00:00").split("+")[0]
                    if "." in date_str:
                        date_str = date_str.split(".")[0]
                    dt = datetime.fromisoformat(date_str.replace("T", " "))
                    dates.append(dt)
                except (ValueError, TypeError):
                    continue

        if len(dates) < 2:
            return 0

        delta = max(dates) - min(dates)
        return delta.days


def analyze_commits(
    commits: List[Dict[str, Any]],
    repos: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze commits and return dict.

    Args:
        commits: List of commit dictionaries from Module 1
        repos: Optional list of repo dictionaries

    Returns:
        Dictionary representation of CommitIntelligenceResult
    """
    engine = CommitIntelligenceEngine()
    result = engine.analyze(commits, repos)
    return result.to_dict()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import json
    import os
    import sys

    # Allow running directly for testing
    if len(sys.argv) > 1:
        handle = sys.argv[1]
    else:
        handle = "gvanrossum"

    data_file = os.path.join("data", f"{handle}_raw.json")

    if not os.path.exists(data_file):
        print(f"Error: Raw data file not found: {data_file}")
        print("Run Module 1 (harvester) first to fetch GitHub data.")
        sys.exit(1)

    print(f"Loading data from {data_file}...")
    with open(data_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    commits = raw_data.get("commits", [])
    repos = raw_data.get("repos", [])

    print(f"Analyzing {len(commits)} commits from {len(repos)} repos...")
    result = analyze_commits(commits, repos)

    print("\n" + "=" * 60)
    print("COMMIT INTELLIGENCE REPORT")
    print("=" * 60)
    print(f"\nCommit Intelligence Score: {result['commit_intelligence_score']:.1f}/100")
    print(f"\nDimension Scores:")
    for dim, score in result["dimensions"].items():
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        print(f"  {dim.replace('_', ' ').title():25} [{bar}] {score:.1f}")

    if result.get("profile"):
        p = result["profile"]
        print(f"\nDeveloper Profile: {p['archetype']}")
        print(f"  Tagline: {p['tagline']}")
        print(f"  Confidence: {p['confidence']:.0%}")

    if result.get("citations"):
        print(f"\nNotable Achievements ({len(result['citations'])}):")
        for i, citation in enumerate(result["citations"][:3], 1):
            print(f"  {i}. {citation['title']}")

    print("\n" + "=" * 60)
