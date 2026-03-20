"""
Commit Analyzer Types
====================
Shared dataclasses for the commit intelligence engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CommitSignal:
    """Individual commit signal with metadata."""
    name: str
    value: float
    category: str
    description: str
    weight: float = 1.0


@dataclass
class DimensionScore:
    """Score for one of the 5 behavioral dimensions."""
    name: str
    score: float
    signals: List[CommitSignal]
    interpretation: str


@dataclass
class DeveloperProfile:
    """Classified developer personality from commit patterns."""
    archetype: str
    confidence: float
    strengths: List[str]
    growth_areas: List[str]
    tagline: str


@dataclass
class CommitCitation:
    """Notable achievement/citation extracted from commits."""
    title: str
    description: str
    evidence: List[str]
    category: str
    impact_score: float


@dataclass
class CommitIntelligenceResult:
    """Complete commit intelligence analysis result."""
    # Overall score
    commit_intelligence_score: float = 0.0
    percentile_rank: float = 0.0

    # Dimension scores
    cognitive_load_score: float = 0.0
    temporal_patterns_score: float = 0.0
    code_hygiene_score: float = 0.0
    problem_solving_score: float = 0.0
    engineering_maturity_score: float = 0.0

    # Raw signals (30+ signals)
    signals: Dict[str, float] = field(default_factory=dict)

    # Developer profile
    profile: Optional[DeveloperProfile] = None

    # Citations/achievements
    citations: List[CommitCitation] = field(default_factory=list)

    # Metadata
    commits_analyzed: int = 0
    repos_analyzed: int = 0
    date_range_days: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "commit_intelligence_score": self.commit_intelligence_score,
            "percentile_rank": self.percentile_rank,
            "dimensions": {
                "cognitive_load": self.cognitive_load_score,
                "temporal_patterns": self.temporal_patterns_score,
                "code_hygiene": self.code_hygiene_score,
                "problem_solving": self.problem_solving_score,
                "engineering_maturity": self.engineering_maturity_score,
            },
            "signals": self.signals,
            "profile": {
                "archetype": self.profile.archetype if self.profile else "unknown",
                "confidence": self.profile.confidence if self.profile else 0.0,
                "strengths": self.profile.strengths if self.profile else [],
                "growth_areas": self.profile.growth_areas if self.profile else [],
                "tagline": self.profile.tagline if self.profile else "",
            } if self.profile else None,
            "citations": [
                {
                    "title": c.title,
                    "description": c.description,
                    "evidence": c.evidence,
                    "category": c.category,
                    "impact_score": c.impact_score,
                }
                for c in self.citations
            ],
            "metadata": {
                "commits_analyzed": self.commits_analyzed,
                "repos_analyzed": self.repos_analyzed,
                "date_range_days": self.date_range_days,
            }
        }
