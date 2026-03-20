"""
Citation Engine
===============
Extracts notable achievements and citations from commit patterns.

Citations are notable accomplishments that can be used as:
- Recruiting signals
- Interview talking points
- Portfolio evidence
- Skill verification
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from modules.commit_analyzer.types import CommitCitation, DeveloperProfile


@dataclass
class CitationRule:
    """Rule for extracting a citation."""
    title: str
    description: str
    category: str
    condition: callable  # function(commits, signals, profile) -> bool
    evidence_extractor: callable  # function(commits, signals) -> List[str]


class CitationEngine:
    """
    Extracts notable achievements/citations from commit analysis.

    Categories:
    - Technical Excellence
    - Leadership & Mentorship
    - Consistency & Discipline
    - Innovation & Impact
    - Open Source Contributions
    """

    def __init__(self):
        """Initialize citation rules."""
        self.rules = self._build_rules()

    def extract(
        self,
        commits: List[Dict[str, Any]],
        signals: Dict[str, float],
        profile: DeveloperProfile
    ) -> List[CommitCitation]:
        """
        Extract citations from commits and signals.

        Args:
            commits: List of commit dictionaries
            signals: Extracted signals
            profile: Developer profile

        Returns:
            List of CommitCitation objects
        """
        citations = []

        for rule in self.rules:
            if rule.condition(commits, signals, profile):
                evidence = rule.evidence_extractor(commits, signals)
                citations.append(CommitCitation(
                    title=rule.title,
                    description=rule.description,
                    evidence=evidence,
                    category=rule.category,
                    impact_score=self._calculate_impact(rule.category, signals),
                ))

        # Sort by impact score
        citations.sort(key=lambda c: c.impact_score, reverse=True)

        return citations

    def _calculate_impact(self, category: str, signals: Dict[str, float]) -> float:
        """Calculate impact score for a citation."""
        base_scores = {
            "technical_excellence": 85,
            "leadership": 80,
            "consistency": 75,
            "innovation": 90,
            "open_source": 85,
        }
        base = base_scores.get(category.lower(), 70)

        # Adjust based on magnitude of signals
        return min(100, base + 10)

    def _build_rules(self) -> List[CitationRule]:
        """Build all citation rules."""
        return [
            # Technical Excellence
            CitationRule(
                title="Architectural Master",
                description="Demonstrates exceptional ability to work across system boundaries and refactor complex codebases",
                category="technical_excellence",
                condition=lambda c, s, p: s.get("architectural_complexity_score", 0) > 70,
                evidence_extractor=lambda c, s: [
                    f"Architectural Complexity Score: {s.get('architectural_complexity_score', 0):.0f}",
                    f"Cross-boundary commits: {s.get('cross_boundary_commit_ratio', 0)*100:.0f}%",
                    f"Multi-module ratio: {s.get('multi_module_commit_ratio', 0)*100:.0f}%",
                ]
            ),
            CitationRule(
                title="Cyclomatic Complexity Reducer",
                description="Consistently reduces code complexity, improving maintainability",
                category="technical_excellence",
                condition=lambda c, s, p: s.get("avg_complexity_delta", 0) < -2,
                evidence_extractor=lambda c, s: [
                    f"Average complexity delta: {s.get('avg_complexity_delta', 0):.1f}",
                    f"Refactoring ratio: {s.get('refactor_ratio', 0)*100:.0f}%",
                ]
            ),

            # Consistency & Discipline
            CitationRule(
                title="Consistency Champion",
                description="Maintains remarkably consistent commit patterns over time",
                category="consistency",
                condition=lambda c, s, p: s.get("consistency_score", 0) > 85 and len(c) > 50,
                evidence_extractor=lambda c, s: [
                    f"Consistency Score: {s.get('consistency_score', 0):.0f}",
                    f"Commits analyzed: {len(c)}",
                    f"Weekly Pattern Score: {s.get('weekly_pattern_score', 0):.0f}",
                ]
            ),
            CitationRule(
                title="Commit Hygiene Expert",
                description="Uses conventional commits and proper documentation",
                category="consistency",
                condition=lambda c, s, p: s.get("conventional_commit_ratio", 0) > 0.6,
                evidence_extractor=lambda c, s: [
                    f"Conventional commit ratio: {s.get('conventional_commit_ratio', 0)*100:.0f}%",
                    f"Verified commits: {s.get('verified_commit_ratio', 0)*100:.0f}%",
                    f"Issue references: {s.get('issue_reference_ratio', 0)*100:.0f}%",
                ]
            ),
            CitationRule(
                title="Early Bird Coder",
                description="Shows discipline with consistent early-morning contributions",
                category="consistency",
                condition=lambda c, s, p: s.get("early_bird_ratio", 0) > 0.3,
                evidence_extractor=lambda c, s: [
                    f"Early bird ratio: {s.get('early_bird_ratio', 0)*100:.0f}%",
                    f"Consistency Score: {s.get('consistency_score', 0):.0f}",
                ]
            ),
            CitationRule(
                title="Night Owl Engineer",
                description="Unconventional schedule suggests deep-focus work habits",
                category="consistency",
                condition=lambda c, s, p: s.get("night_owl_ratio", 0) > 0.25 or s.get("late_night_commit_ratio", 0) > 0.2,
                evidence_extractor=lambda c, s: [
                    f"Night owl ratio: {s.get('night_owl_ratio', 0)*100:.0f}%",
                    f"Late night ratio: {s.get('late_night_commit_ratio', 0)*100:.0f}%",
                ]
            ),

            # Problem Solving
            CitationRule(
                title="Refactoring Expert",
                description="Strong focus on improving code quality through refactoring",
                category="innovation",
                condition=lambda c, s, p: s.get("refactor_ratio", 0) > 0.2,
                evidence_extractor=lambda c, s: [
                    f"Refactor ratio: {s.get('refactor_ratio', 0)*100:.0f}%",
                    f"Avg churn ratio: {s.get('avg_churn_ratio', 0):.2f}",
                    f"Large refactor commits: {s.get('large_refactor_commits', 0)}",
                ]
            ),
            CitationRule(
                title="Bug Squashing Expert",
                description="Proven track record of identifying and fixing issues",
                category="innovation",
                condition=lambda c, s, p: s.get("fix_ratio", 0) > 0.15,
                evidence_extractor=lambda c, s: [
                    f"Bug fix ratio: {s.get('fix_ratio', 0)*100:.0f}%",
                    f"Avg fix files: {s.get('avg_fix_files', 0):.1f}",
                    f"Test coverage ratio: {s.get('test_coverage_ratio', 0)*100:.0f}%",
                ]
            ),
            CitationRule(
                title="Performance Optimizer",
                description="Consistently optimizes code for better performance",
                category="innovation",
                condition=lambda c, s, p: s.get("perf_ratio", 0) > 0.05,
                evidence_extractor=lambda c, s: [
                    f"Performance commit ratio: {s.get('perf_ratio', 0)*100:.0f}%",
                ]
            ),

            # Leadership & Mentorship
            CitationRule(
                title="PR Reviewer",
                description="High merge ratio suggests code review and collaboration",
                category="leadership",
                condition=lambda c, s, p: s.get("merge_commit_ratio", 0) > 0.2,
                evidence_extractor=lambda c, s: [
                    f"Merge commit ratio: {s.get('merge_commit_ratio', 0)*100:.0f}%",
                    f"Average parents: {s.get('avg_parents', 1):.1f}",
                ]
            ),
            CitationRule(
                title="Release Manager",
                description="Disciplined release process with version management",
                category="leadership",
                condition=lambda c, s, p: s.get("semantic_versioning_ratio", 0) > 0.2,
                evidence_extractor=lambda c, s: [
                    f"Semantic versioning ratio: {s.get('semantic_versioning_ratio', 0)*100:.0f}%",
                    f"Changelog awareness: {s.get('changelog_awareness', 0)*100:.0f}%",
                    f"Release awareness: {s.get('release_awareness', 0)*100:.0f}%",
                ]
            ),

            # Open Source & Community
            CitationRule(
                title="Open Source Contributor",
                description="Contributes to external projects with high visibility",
                category="open_source",
                condition=lambda c, s, p: s.get("repo_count", 0) > 20 and s.get("avg_repo_stars", 0) > 100,
                evidence_extractor=lambda c, s: [
                    f"Repositories: {s.get('repo_count', 0)}",
                    f"Average stars: {s.get('avg_repo_stars', 0):.0f}",
                    f"Total stars: {s.get('total_stars', 0):,}",
                ]
            ),

            # Test Coverage
            CitationRule(
                title="Test-Driven Developer",
                description="Strong commitment to testing and code quality",
                category="technical_excellence",
                condition=lambda c, s, p: s.get("test_coverage_ratio", 0) > 0.4,
                evidence_extractor=lambda c, s: [
                    f"Test coverage ratio: {s.get('test_coverage_ratio', 0)*100:.0f}%",
                    f"Test commits: {s.get('test_ratio', 0)*100:.0f}%",
                ]
            ),

            # High Volume
            CitationRule(
                title="Prolific Contributor",
                description="Exceptional volume of meaningful contributions",
                category="consistency",
                condition=lambda c, s, p: len(c) > 200,
                evidence_extractor=lambda c, s: [
                    f"Total commits analyzed: {len(c)}",
                    f"Repositories: {s.get('repo_count', 0)}",
                    f"Date range: {s.get('date_range_days', 0)} days",
                ]
            ),
        ]

    def _empty_citations(self) -> List[CommitCitation]:
        """Return empty citations list."""
        return []
