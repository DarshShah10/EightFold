"""
Developer Profile Classifier
============================
Classifies developer personality archetypes from commit patterns.

Archetypes:
- Architect Engineer: High cognitive load, cross-boundary work
- Bug Hunter: High fix ratio, focused commits
- Feature Factory: High feat ratio, consistent commits
- Code Artisan: High refactor ratio, balanced churn
- DevOps Champion: High CI/CD presence, infrastructure work
- Night Owl: Late-night commits, weekend work
- Early Bird: Morning commits, consistent schedule
- Release Manager: Semantic versioning, changelog awareness
- Hybrid: Mixed patterns
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from modules.commit_analyzer.types import DeveloperProfile, CommitIntelligenceResult


@dataclass
class ArchetypeDefinition:
    """Definition of a developer archetype."""
    name: str
    tagline: str
    strengths: List[str]
    growth_areas: List[str]
    thresholds: Dict[str, Tuple[float, str]]  # signal -> (threshold, operator)


class ProfileClassifier:
    """
    Classifies developer personality from commit signals.

    Uses rule-based classification with confidence scoring.
    """

    ARCHETYPES = {
        "architect": ArchetypeDefinition(
            name="Architect Engineer",
            tagline="Thinks in systems, not just code",
            strengths=[
                "Cross-boundary architectural work",
                "Multi-module refactoring",
                "System-level thinking",
            ],
            growth_areas=[
                "Could focus more on incremental features",
                "May over-engineer simple solutions",
            ],
            thresholds={
                "architectural_complexity_score": (60, ">"),
                "cross_boundary_commit_ratio": (0.1, ">"),
                "multi_module_commit_ratio": (0.3, ">"),
            }
        ),
        "bug_hunter": ArchetypeDefinition(
            name="Bug Hunter",
            tagline="Ships with confidence, fixes with precision",
            strengths=[
                "High bug fix ratio",
                "Focused, minimal commits",
                "Quality-first mindset",
            ],
            growth_areas=[
                "Could contribute more features",
                "May be too conservative with changes",
            ],
            thresholds={
                "fix_ratio": (0.2, ">"),
                "avg_fix_files": (3, "<"),
                "test_coverage_ratio": (0.3, ">"),
            }
        ),
        "feature_factory": ArchetypeDefinition(
            name="Feature Factory",
            tagline="Ship it, ship it again",
            strengths=[
                "High feature output",
                "Consistent velocity",
                "Product-focused delivery",
            ],
            growth_areas=[
                "Could improve test coverage",
                "May need more refactoring discipline",
            ],
            thresholds={
                "feat_ratio": (0.4, ">"),
                "consistency_score": (60, ">"),
                "avg_commit_size": (200, "<"),
            }
        ),
        "code_artisan": ArchetypeDefinition(
            name="Code Artisan",
            tagline="Crafts code like poetry",
            strengths=[
                "High refactoring discipline",
                "Balanced churn ratios",
                "Code quality focus",
            ],
            growth_areas=[
                "Could ship more features",
                "May over-optimize existing code",
            ],
            thresholds={
                "refactor_ratio": (0.2, ">"),
                "avg_churn_ratio": (1.0, "~"),  # Near 1.0
                "conventional_commit_ratio": (0.5, ">"),
            }
        ),
        "devops_champion": ArchetypeDefinition(
            name="DevOps Champion",
            tagline="Builds the foundation others stand on",
            strengths=[
                "Strong CI/CD presence",
                "Infrastructure automation",
                "Release management",
            ],
            growth_areas=[
                "Could contribute more to application code",
                "May focus too much on tooling",
            ],
            thresholds={
                "ci_pipeline_ratio": (0.8, ">"),
                "github_actions_ratio": (0.6, ">"),
                "engineering_maturity_score": (70, ">"),
            }
        ),
        "night_owl": ArchetypeDefinition(
            name="Night Owl",
            tagline="When the world sleeps, code flows",
            strengths=[
                "Uninterrupted deep work hours",
                "Flexible schedule adaptability",
                "Handles urgent issues after hours",
            ],
            growth_areas=[
                "Could maintain more regular schedule",
                "May have work-life balance concerns",
            ],
            thresholds={
                "night_owl_ratio": (0.3, ">"),
                "late_night_commit_ratio": (0.15, ">"),
            }
        ),
        "early_bird": ArchetypeDefinition(
            name="Early Bird",
            tagline="Catches the worms, ships by noon",
            strengths=[
                "Consistent morning productivity",
                "Stable work schedule",
                "Available during business hours",
            ],
            growth_areas=[
                "Could leverage night hours for deep work",
                "May miss late-day energy peaks",
            ],
            thresholds={
                "early_bird_ratio": (0.25, ">"),
                "consistency_score": (70, ">"),
                "business_hours_ratio": (0.6, ">"),
            }
        ),
        "release_manager": ArchetypeDefinition(
            name="Release Manager",
            tagline="Orchestrates the symphony of shipping",
            strengths=[
                "Semantic versioning discipline",
                "Changelog awareness",
                "Structured release process",
            ],
            growth_areas=[
                "Could reduce release friction",
                "May be too process-heavy",
            ],
            thresholds={
                "semantic_versioning_ratio": (0.3, ">"),
                "changelog_awareness": (0.1, ">"),
                "release_awareness": (0.5, ">"),
            }
        ),
    }

    def classify(
        self,
        signals: Dict[str, float],
        result: CommitIntelligenceResult
    ) -> DeveloperProfile:
        """
        Classify developer profile from signals.

        Args:
            signals: All extracted signals
            result: Analysis result with dimension scores

        Returns:
            DeveloperProfile with archetype classification
        """
        archetype_scores: Dict[str, float] = {}

        for archetype_id, archetype in self.ARCHETYPES.items():
            score = self._calculate_archetype_score(archetype, signals)
            archetype_scores[archetype_id] = score

        # Get top archetype
        if not archetype_scores:
            return self._default_profile()

        top_archetype_id = max(archetype_scores, key=archetype_scores.get)
        top_score = archetype_scores[top_archetype_id]

        # Check for tie or low confidence
        sorted_scores = sorted(archetype_scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            second_score = sorted_scores[1]
            margin = top_score - second_score
            confidence = min(0.9, margin / 30) if margin > 0 else 0.3
        else:
            confidence = 0.5

        # Also check for hybrid (multiple moderate scores)
        if top_score < 0.4 and len([s for s in archetype_scores.values() if s > 0.3]) >= 2:
            return self._hybrid_profile(signals, archetype_scores)

        archetype = self.ARCHETYPES[top_archetype_id]
        return DeveloperProfile(
            archetype=archetype.name,
            confidence=round(confidence, 2),
            strengths=archetype.strengths.copy(),
            growth_areas=archetype.growth_areas.copy(),
            tagline=archetype.tagline,
        )

    def _calculate_archetype_score(
        self,
        archetype: ArchetypeDefinition,
        signals: Dict[str, float]
    ) -> float:
        """Calculate how well signals match an archetype."""
        matches = 0
        total = len(archetype.thresholds)

        if total == 0:
            return 0.0

        for signal_name, (threshold, operator) in archetype.thresholds.items():
            value = signals.get(signal_name, 0.0)

            match = self._check_match(value, threshold, operator)
            if match:
                matches += 1

        return matches / total if total > 0 else 0.0

    def _check_match(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value matches threshold with operator."""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.1
        elif operator == "~":  # Near (within 20%)
            return abs(value - threshold) / max(1, threshold) < 0.2
        return False

    def _default_profile(self) -> DeveloperProfile:
        """Return default profile when classification fails."""
        return DeveloperProfile(
            archetype="Developer",
            confidence=0.3,
            strengths=["Active contributor"],
            growth_areas=["More commits needed for classification"],
            tagline="Still establishing patterns",
        )

    def _hybrid_profile(
        self,
        signals: Dict[str, float],
        archetype_scores: Dict[str, float]
    ) -> DeveloperProfile:
        """Return hybrid profile for mixed patterns."""
        top_two = sorted(archetype_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        top_archetypes = [self.ARCHETYPES[arch_id].name for arch_id, _ in top_two]

        return DeveloperProfile(
            archetype="Hybrid Developer",
            confidence=0.5,
            strengths=[f"Combines {top_archetypes[0]} and {top_archetypes[1]}"],
            growth_areas=["Could develop more specialized patterns"],
            tagline="Versatile and adaptable",
        )
