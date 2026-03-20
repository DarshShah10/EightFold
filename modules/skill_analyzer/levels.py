"""
Skill Level Inference
=====================
Infers skill level (Junior/Mid/Senior/Staff/Principal) based on complexity,
impact, scope, and domain expertise.
"""

from dataclasses import dataclass
from typing import Optional
from modules.skill_analyzer.types import SkillProfile


@dataclass
class LevelSignals:
    """Signals for level inference."""
    score: float = 0.0
    primary_domains: int = 0
    secondary_domains: int = 0
    has_infrastructure: bool = False
    has_production_ml: bool = False
    open_source_impact: int = 0  # Total stars across repos
    repo_count: int = 0
    language_depth_score: float = 0.0
    has_architecture: bool = False
    has_mentorship: bool = False  # Based on contributions to docs/guides
    multi_stack: bool = False  # Works across frontend/backend/infra
    has_enterprise: bool = False


# =============================================================================
# LEVEL CRITERIA
# =============================================================================

LEVEL_CRITERIA = {
    "Junior": {
        "min_score": 0,
        "max_score": 25,
        "characteristics": [
            "Limited language depth (1-2 primary languages)",
            "Small to medium project contributions",
            "Focused on implementation, not architecture",
            "Few or no infrastructure skills",
            "Single domain focus",
        ],
    },
    "Mid": {
        "min_score": 25,
        "max_score": 50,
        "characteristics": [
            "Good depth in 1-2 languages",
            "Contributes to full feature development",
            "Some infrastructure awareness",
            "2-3 domain areas",
            "Can work independently on features",
        ],
    },
    "Senior": {
        "min_score": 50,
        "max_score": 70,
        "characteristics": [
            "Deep expertise in primary stack",
            "Cross-stack capabilities (frontend + backend)",
            "Strong infrastructure and DevOps skills",
            "3+ domain areas",
            "Architectural contributions",
            "Mentors others",
            "Open source contributions with impact",
        ],
    },
    "Staff": {
        "min_score": 70,
        "max_score": 85,
        "characteristics": [
            "Expert-level in multiple domains",
            "Drives technical decisions",
            "Influences team/company-wide architecture",
            "Significant open source impact",
            "Cross-functional leadership",
            "Production-scale systems",
            "Technical strategy contributions",
        ],
    },
    "Principal": {
        "min_score": 85,
        "max_score": 100,
        "characteristics": [
            "Industry-recognized expertise",
            "Shapes technical direction at scale",
            "Major open source influence",
            "Thought leadership",
            "Organizational impact",
            "Pioneered new approaches/patterns",
        ],
    },
}


class SkillLevelInferrer:
    """Infers developer skill level from signals."""

    def __init__(self):
        self.criteria = LEVEL_CRITERIA

    def infer_level(self, skill_profile: SkillProfile, signals: dict) -> tuple[str, float]:
        """
        Infer skill level from profile and signals.

        Args:
            skill_profile: Aggregated skill profile
            signals: Additional signals dict

        Returns:
            Tuple of (level_name, confidence)
        """
        level_signals = self._extract_level_signals(skill_profile, signals)
        score = self._compute_level_score(level_signals)
        level, confidence = self._map_score_to_level(score, level_signals)

        return level, confidence

    def _extract_level_signals(
        self, profile: SkillProfile, signals: dict
    ) -> LevelSignals:
        """Extract signals relevant to level inference."""
        # Open source impact
        open_source_impact = 0
        repo_count = len(signals.get("top_repos", []))

        for repo in signals.get("top_repos", []):
            impact = repo.get("impact", {})
            open_source_impact += impact.get("stars", 0)

        # Language depth
        lang_depth = profile.depth_index.specialist_score if profile.depth_index else 0.0

        # Multi-stack
        domains = len(profile.primary_domains) + len(profile.secondary_domains)
        infra = len(signals.get("infrastructure", [])) > 0

        return LevelSignals(
            score=0,  # Will be computed
            primary_domains=len(profile.primary_domains),
            secondary_domains=len(profile.secondary_domains),
            has_infrastructure=infra,
            has_production_ml="ML Engineering" in profile.primary_domains or "AI" in profile.primary_domains,
            open_source_impact=open_source_impact,
            repo_count=repo_count,
            language_depth_score=lang_depth,
            has_architecture=any(
                "architecture" in s.lower()
                for s in profile.growth_indicators
            ) if profile.growth_indicators else False,
            multi_stack=domains >= 3,
            has_enterprise=profile.organization_ready,
        )

    def _compute_level_score(self, signals: LevelSignals) -> float:
        """Compute level score from signals."""
        score = 0.0

        # Language depth (max 30 points) - high weight for deep expertise
        score += signals.language_depth_score * 30

        # Domain breadth (max 15 points)
        score += min(15, (signals.primary_domains + signals.secondary_domains) * 5)

        # Multi-stack (max 15 points) - important signal
        if signals.multi_stack:
            score += 15
        elif signals.primary_domains > 0:
            score += 8

        # Open source impact (max 25 points)
        # Log scale: 100 stars = 5, 1000 = 10, 10000 = 15, 50000+ = 20, 100000+ = 25
        if signals.open_source_impact > 0:
            impact_score = min(25, math.log10(signals.open_source_impact + 1) * 4.5)
            score += impact_score

        # Infrastructure skills (max 10 points)
        if signals.has_infrastructure:
            score += 10

        # Repo count (max 5 points)
        score += min(5, signals.repo_count * 0.3)

        # Architecture signals (max 5 points)
        if signals.has_architecture:
            score += 5

        # Enterprise readiness (max 5 points)
        if signals.has_enterprise:
            score += 5

        # Bonus for creating a programming language (extreme signal)
        if signals.open_source_impact > 100000:
            score = min(100, score + 10)

        return min(100, score)

    def _map_score_to_level(
        self, score: float, signals: LevelSignals
    ) -> tuple[str, float]:
        """Map score to level with confidence."""
        # Find appropriate level
        for level_name, criteria in sorted(
            self.criteria.items(),
            key=lambda x: x[1]["min_score"],
            reverse=True
        ):
            if score >= criteria["min_score"]:
                # Calculate confidence based on position in range
                level_range = criteria["max_score"] - criteria["min_score"]
                if level_range > 0:
                    position_in_range = (score - criteria["min_score"]) / level_range
                    # Edge cases
                    if score == criteria["max_score"]:
                        confidence = 0.8  # At upper bound
                    elif score == criteria["min_score"]:
                        confidence = 0.8  # At lower bound
                    else:
                        confidence = 0.7 + position_in_range * 0.2
                else:
                    confidence = 0.8

                # Boost confidence based on clear signals
                if score >= 70 and signals.open_source_impact > 1000:
                    confidence = min(0.95, confidence + 0.1)
                if score >= 50 and signals.has_infrastructure and signals.multi_stack:
                    confidence = min(0.95, confidence + 0.05)

                return level_name, min(0.95, confidence)

        # Fallback
        return "Mid", 0.5

    def get_level_description(self, level: str) -> dict:
        """Get detailed description for a level."""
        criteria = self.criteria.get(level, {})
        return {
            "level": level,
            "description": self._get_level_summary(level),
            "characteristics": criteria.get("characteristics", []),
            "typical_score_range": f"{criteria.get('min_score', 0)}-{criteria.get('max_score', 0)}",
        }

    def _get_level_summary(self, level: str) -> str:
        """Get one-line summary for level."""
        summaries = {
            "Junior": "Learning the fundamentals, focuses on implementation tasks",
            "Mid": "Independent contributor who can own features end-to-end",
            "Senior": "Technical leader driving architecture and mentoring others",
            "Staff": "Multi-team influence shaping technical direction",
            "Principal": "Industry-recognized technical visionary",
        }
        return summaries.get(level, "Unknown level")


import math


def infer_skill_level(skill_profile: SkillProfile, signals: dict) -> tuple[str, float]:
    """
    Convenience function to infer skill level.

    Args:
        skill_profile: Aggregated skill profile
        signals: Additional signals

    Returns:
        Tuple of (level, confidence)
    """
    inferrer = SkillLevelInferrer()
    return inferrer.infer_level(skill_profile, signals)
