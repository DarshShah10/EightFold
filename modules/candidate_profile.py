"""
Candidate Profile Schema
========================
Unified output schema for the EightFold candidate intelligence system.

All modules produce data that gets assembled into this schema.
This is the contract that all modules must follow.

Example output:
{
    "candidate_id": { "github_handle": "gvanrossum" },
    "identity": { "name": "...", "bio": "..." },
    "languages": { ... },      // Module 3
    "complexity": { ... },     // Module 3
    "dependencies": { ... },   // Module 4
    "velocity": { ... },       // Module 5 (future)
    "commits": { ... },        // Module 2
    "explanation": {
        "reasoning_chains": [...],
        "evidence": {...},
        "confidence_score": 0.85
    }
}
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CandidateID:
    """Unique identifier for the candidate."""
    github_handle: str
    github_id: Optional[int] = None
    name: Optional[str] = None


@dataclass
class IdentityInfo:
    """Basic identity information."""
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    blog: Optional[str] = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    created_at: Optional[str] = None
    account_age_years: float = 0.0
    organizations: list[str] = field(default_factory=list)


@dataclass
class LanguageProfile:
    """Language depth and usage profile (Module 3)."""
    primary_language: str = ""
    depth_scores: dict[str, float] = field(default_factory=dict)  # language -> score 0-1
    total_languages: int = 0
    proportion: dict[str, float] = field(default_factory=dict)  # language -> percentage


@dataclass
class ComplexityProfile:
    """Project complexity and impact profile (Module 3)."""
    project_complexity_score: float = 0.0
    impact_score: float = 0.0
    modernity_score: float = 0.0
    top_repos: list[dict] = field(default_factory=list)
    engineering_maturity: dict = field(default_factory=dict)


@dataclass
class SkillProfile:
    """Comprehensive skill intelligence (Module 3)."""
    skill_level: str = ""  # Junior, Mid, Senior, Staff, Principal
    skill_level_confidence: float = 0.0
    years_experience_estimate: int = 0
    primary_domains: list[str] = field(default_factory=list)
    secondary_domains: list[str] = field(default_factory=list)
    depth_category: str = ""  # specialist, generalist, t-shaped, balanced
    specialist_language: str = ""
    growth_indicators: list[str] = field(default_factory=list)
    organization_ready: bool = False


@dataclass
class DependencyProfile:
    """Dependency fingerprinting profile (Module 4)."""
    philosophy: dict = field(default_factory=dict)
    philosophy_scores: dict = field(default_factory=dict)
    detected_trends: list[str] = field(default_factory=list)
    ecosystem: dict = field(default_factory=dict)


@dataclass
class VelocityProfile:
    """Learning velocity and growth trajectory (Module 5 - future)."""
    velocity_score: float = 0.0
    trajectory: str = ""  # accelerating, stable, declining
    growth_signals: dict = field(default_factory=dict)
    language_adoption: list[str] = field(default_factory=list)


@dataclass
class CommitProfile:
    """Commit intelligence profile (Module 2)."""
    intelligence_score: float = 0.0
    dimension_scores: dict = field(default_factory=dict)
    developer_archetype: str = ""
    archetype_tagline: str = ""
    commit_statistics: dict = field(default_factory=dict)
    top_citations: list[dict] = field(default_factory=list)


@dataclass
class ReasoningChain:
    """Single piece of reasoning for a skill claim."""
    skill: str
    confidence: float
    evidence: str
    source: str  # "dependencies", "repos", "commits", "language"
    weight: float


@dataclass
class Explanation:
    """Explainability data for all skill claims."""
    reasoning_chains: list[ReasoningChain] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    confidence_score: float = 0.0
    warnings: list[str] = field(default_factory=list)
    data_coverage: dict = field(default_factory=dict)  # Which data sources were used


@dataclass
class CandidateProfile:
    """
    Complete candidate profile assembled from all modules.

    This is the final output of the EightFold intelligence system.
    """
    candidate_id: CandidateID = field(default_factory=CandidateID)
    identity: IdentityInfo = field(default_factory=IdentityInfo)
    languages: LanguageProfile = field(default_factory=LanguageProfile)
    complexity: ComplexityProfile = field(default_factory=ComplexityProfile)
    skills: SkillProfile = field(default_factory=SkillProfile)
    dependencies: DependencyProfile = field(default_factory=DependencyProfile)
    velocity: VelocityProfile = field(default_factory=VelocityProfile)
    commits: CommitProfile = field(default_factory=CommitProfile)
    explanation: Explanation = field(default_factory=Explanation)

    # Metadata
    analyzed_at: str = ""
    modules_run: list[str] = field(default_factory=list)
    data_sources_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        def _clean(obj):
            if hasattr(obj, '__dict__'):
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
# Profile Builder
# =============================================================================

class ProfileBuilder:
    """Builds complete candidate profiles from all modules."""

    def __init__(self):
        self.profile = CandidateProfile()

    def with_identity(self, github_handle: str, user_data: dict) -> "ProfileBuilder":
        """Add identity information."""
        self.profile.candidate_id.github_handle = github_handle
        self.profile.candidate_id.github_id = user_data.get("id")
        self.profile.candidate_id.name = user_data.get("name")

        self.profile.identity = IdentityInfo(
            name=user_data.get("name"),
            bio=user_data.get("bio"),
            company=user_data.get("company"),
            location=user_data.get("location"),
            blog=user_data.get("blog"),
            followers=user_data.get("followers", 0),
            following=user_data.get("following", 0),
            public_repos=user_data.get("public_repos", 0),
            created_at=user_data.get("created_at"),
        )

        # Calculate account age
        if user_data.get("created_at"):
            from datetime import datetime
            try:
                created = datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00"))
                age = (datetime.now() - created).days / 365.25
                self.profile.identity.account_age_years = round(age, 1)
            except:
                pass

        return self

    def with_skills(self, skill_result) -> "ProfileBuilder":
        """Add skill intelligence data."""
        self.profile.languages = LanguageProfile(
            primary_language=skill_result.language_depth,
            depth_scores=skill_result.language_depth,
            total_languages=len(skill_result.language_depth),
        )

        self.profile.complexity = ComplexityProfile(
            project_complexity_score=skill_result.skill_profile.modernity_score.overall_score,
            modernity_score=skill_result.skill_profile.modernity_score.overall_score,
            top_repos=skill_result.top_repos,
        )

        self.profile.skills = SkillProfile(
            skill_level=skill_result.skill_profile.skill_level,
            skill_level_confidence=skill_result.skill_profile.skill_level_confidence,
            years_experience_estimate=skill_result.skill_profile.years_experience_estimate,
            primary_domains=skill_result.skill_profile.primary_domains,
            secondary_domains=skill_result.skill_profile.secondary_domains,
            depth_category=skill_result.skill_profile.depth_index.depth_category,
            specialist_language=skill_result.skill_profile.depth_index.specialist_language,
            growth_indicators=skill_result.skill_profile.growth_indicators,
            organization_ready=skill_result.skill_profile.organization_ready,
        )

        return self

    def with_dependencies(self, dep_result) -> "ProfileBuilder":
        """Add dependency fingerprinting data."""
        self.profile.dependencies = DependencyProfile(
            philosophy=dep_result.get("engineering_philosophy", {}),
            philosophy_scores=dep_result.get("philosophy_scores", {}),
            detected_trends=dep_result.get("trends", []),
            ecosystem=dep_result.get("ecosystem", {}),
        )
        return self

    def with_velocity(self, velocity_result) -> "ProfileBuilder":
        """Add learning velocity data."""
        self.profile.velocity = VelocityProfile(
            velocity_score=velocity_result.get("velocity_score", 0),
            trajectory=velocity_result.get("trajectory", "unknown"),
            growth_signals=velocity_result.get("growth_signals", {}),
            language_adoption=velocity_result.get("languages_adopted", []),
        )
        return self

    def with_commits(self, commit_result) -> "ProfileBuilder":
        """Add commit intelligence data."""
        self.profile.commits = CommitProfile(
            intelligence_score=commit_result.get("commit_intelligence_score", 0),
            dimension_scores=commit_result.get("dimensions", {}),
            developer_archetype=commit_result.get("profile", {}).get("archetype", "") if commit_result.get("profile") else "",
            archetype_tagline=commit_result.get("profile", {}).get("tagline", "") if commit_result.get("profile") else "",
            commit_statistics=commit_result.get("metadata", {}),
            top_citations=commit_result.get("citations", [])[:5],
        )
        return self

    def with_explanation(self, chains: list[ReasoningChain], confidence: float) -> "ProfileBuilder":
        """Add explainability data."""
        self.profile.explanation = Explanation(
            reasoning_chains=chains,
            confidence_score=confidence,
        )
        return self

    def build(self) -> CandidateProfile:
        """Build the final profile."""
        return self.profile


def build_candidate_profile(
    github_handle: str,
    raw_data: dict,
    skill_result=None,
    commit_result=None,
    dep_result=None,
) -> dict:
    """
    Convenience function to build complete candidate profile.

    Args:
        github_handle: GitHub handle
        raw_data: Full harvested data
        skill_result: Result from SkillAnalyzer
        commit_result: Result from CommitAnalyzer
        dep_result: Result from DependencyAnalyzer

    Returns:
        Complete candidate profile as dict
    """
    builder = ProfileBuilder()

    # Identity
    user_data = raw_data.get("user", {})
    builder.with_identity(github_handle, user_data)

    # Add organizations
    orgs = raw_data.get("orgs", []) or []
    builder.profile.identity.organizations = [o.get("login", "") for o in orgs]

    # Skills
    if skill_result:
        builder.with_skills(skill_result)

    # Dependencies
    if dep_result:
        builder.with_dependencies(dep_result)

    # Commits
    if commit_result:
        builder.with_commits(commit_result)

    # Track modules run
    modules = []
    if skill_result:
        modules.append("skill_analyzer")
    if commit_result:
        modules.append("commit_analyzer")
    if dep_result:
        modules.append("dependency_analyzer")
    builder.profile.modules_run = modules

    # Track data sources
    sources = []
    if raw_data.get("repos"):
        sources.append("repos")
    if raw_data.get("commits"):
        sources.append("commits")
    if raw_data.get("lang_bytes"):
        sources.append("languages")
    if raw_data.get("dep_files"):
        sources.append("dependencies")
    if raw_data.get("issues"):
        sources.append("issues")
    if raw_data.get("pull_requests"):
        sources.append("pull_requests")
    if raw_data.get("events"):
        sources.append("events")
    builder.profile.data_sources_used = sources

    # Set analyzed timestamp
    from datetime import datetime, timezone
    builder.profile.analyzed_at = datetime.now(timezone.utc).isoformat()

    return builder.build().to_dict()
