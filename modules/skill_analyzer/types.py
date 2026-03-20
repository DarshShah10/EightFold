"""
Type Definitions for Skill Analyzer
=====================================
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TechNode:
    """A technology node in the tech graph."""
    name: str
    category: str
    subcategory: Optional[str] = None
    related_technologies: list[str] = field(default_factory=list)
    stack_tags: list[str] = field(default_factory=list)
    version_signals: list[str] = field(default_factory=list)


@dataclass
class TechGraph:
    """Technology relationship graph."""
    nodes: dict[str, TechNode] = field(default_factory=dict)
    primary_stack: str = ""
    related_stacks: list[str] = field(default_factory=list)


@dataclass
class SkillSignal:
    """Individual skill signal extracted from data."""
    skill: str
    confidence: float
    source: str  # 'language', 'topic', 'dependency', 'repo_name', 'description'
    weight: float = 1.0


@dataclass
class DomainProfile:
    """Profile for a detected problem domain."""
    domain: str
    confidence: float
    signals: list[str] = field(default_factory=list)
    primary_technologies: list[str] = field(default_factory=list)


@dataclass
class DepthIndex:
    """Depth vs breadth analysis."""
    specialist_language: str = ""
    specialist_score: float = 0.0
    breadth_score: float = 0.0
    depth_category: str = ""  # 'specialist', 'generalist', 't-shaped', 'deep-generalist'


@dataclass
class StackModernity:
    """Modernity assessment of a tech stack."""
    overall_score: float = 0.0
    age_score: float = 0.0
    ecosystem_score: float = 0.0
    patterns_score: float = 0.0
    signals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ProjectImpact:
    """Impact metrics for a project."""
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    impact_score: float = 0.0
    recency_weight: float = 0.0
    community_score: float = 0.0


@dataclass
class SkillProfile:
    """Complete skill intelligence profile."""
    primary_domains: list[str] = field(default_factory=list)
    secondary_domains: list[str] = field(default_factory=list)
    depth_index: DepthIndex = field(default_factory=DepthIndex)
    skill_level: str = ""  # 'Junior', 'Mid', 'Senior', 'Staff', 'Principal'
    skill_level_confidence: float = 0.0
    tech_graph: TechGraph = field(default_factory=TechGraph)
    modernity_score: StackModernity = field(default_factory=StackModernity)
    years_experience_estimate: int = 0
    organization_ready: bool = False
    growth_indicators: list[str] = field(default_factory=list)


@dataclass
class SkillIntelligenceResult:
    """Complete skill intelligence result."""
    skill_profile: SkillProfile = field(default_factory=SkillProfile)
    signals: dict[str, float] = field(default_factory=dict)
    language_depth: dict[str, float] = field(default_factory=dict)
    frameworks: list[str] = field(default_factory=list)
    infrastructure: list[str] = field(default_factory=list)
    detected_domains: list[DomainProfile] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    top_repos: list[dict] = field(default_factory=list)
    jd_fit: Optional[dict] = None
    # For backward compatibility - inferred_skills is added by aggregator
    inferred_skills: Optional[list] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization and integration."""
        def _clean(obj):
            if hasattr(obj, '__dict__'):
                # It's a dataclass or object with __dict__
                result = {}
                for k, v in obj.__dict__.items():
                    if v is not None:
                        result[k] = _clean(v)
                return result
            elif isinstance(obj, list):
                return [_clean(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            else:
                return obj
        return _clean(self)


# =============================================================================
# EXPLAINABILITY TYPES
# =============================================================================

from enum import Enum


class EvidenceSource(str, Enum):
    """All possible evidence sources for skill assessment."""
    LANGUAGE_BYTES = "language_bytes"
    COMMIT = "commit"
    DEPENDENCY = "dependency"
    REPOSITORY = "repository"
    TOPIC = "topic"
    DESCRIPTION = "description"
    FILE_PATTERN = "file_pattern"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    FRAMEWORK = "framework"
    INFRASTRUCTURE = "infrastructure"
    COMPLEXITY = "complexity"


@dataclass
class EvidenceItem:
    """A single piece of evidence supporting a skill claim."""
    source: EvidenceSource
    source_id: str  # e.g., "ml-toolkit", "pandas", "commits"
    finding: str  # Human-readable finding
    weight: float = 1.0
    matched_pattern: Optional[str] = None  # What pattern matched
    raw_data_excerpt: Optional[str] = None  # Relevant snippet of raw data


@dataclass
class ExplainableSkill:
    """Skill with full explainability - evidence chain and reasoning."""
    skill: str
    level: str  # "Junior", "Mid", "Senior", "Staff", "Principal"
    confidence: float
    evidence: dict[str, str]  # source → human-readable finding
    reasoning: list[str]  # Human-readable explanations
    gaps: list[str]  # Missing evidence / areas of uncertainty
    contributing_repos: list[str]  # Which repos confirm this skill
    supporting_signals: list[str]  # Technical signal names
    evidence_items: list[EvidenceItem] = field(default_factory=list)  # Full evidence chain


@dataclass
class ProjectEvidence:
    """Evidence from a single project/repository."""
    name: str
    full_name: str
    impact: str  # e.g., "1.2k stars"
    stars: int
    forks: int
    skills_demonstrated: list[str]
    signals: list[str]
    why_it_matters: str  # Human-readable explanation
    complexity_signals: list[str] = field(default_factory=list)
    key_commits: list[str] = field(default_factory=list)


@dataclass
class ProblemTrace:
    """A trace of problem-solving activity."""
    type: str  # "bug_fix", "complex_refactor", "architecture", "feature", "optimization"
    repo: str
    repo_name: str
    commit_hash: str
    summary: str
    quality_signal: str  # e.g., "Included tests and docs"
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    is_verified: bool = False


@dataclass
class ExplainableResult:
    """Complete explainable skill intelligence report."""
    candidate: str
    skill_assessment: dict[str, ExplainableSkill]
    primary_language: str
    primary_language_depth: float
    domains: list[str]
    project_evidence: list[ProjectEvidence]
    problem_solving_traces: list[ProblemTrace]
    summary: str  # Overall assessment summary
    confidence: float  # Overall confidence in assessment
    caveats: list[str] = field(default_factory=list)  # Limitations of this assessment

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        def _clean(obj):
            if hasattr(obj, '__dict__'):
                return {k: _clean(v) for k, v in obj.__dict__.items() if v is not None}
            elif isinstance(obj, list):
                return [_clean(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            else:
                return obj
        return _clean(self)
