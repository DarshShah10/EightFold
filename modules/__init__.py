"""
GitHub Signal Extraction Engine
=============================

A comprehensive toolkit for extracting developer behavioral signals from GitHub.

Modules:
    1. Harvester - Collects all GitHub data (user, repos, commits, PRs, issues, etc.)
    2. Commit Intelligence - Analyzes commit patterns and developer behavior
    3. Skill Intelligence - Extracts semantic skills, domains, and expertise profiles
    4. Dependency Analysis - Determines engineering philosophy from dependencies
    5. Aggregates - Computes comprehensive metrics from harvested data

Usage:
    from modules import harvest
    raw_data = harvest("github_handle")

    from modules.skill_analyzer import SkillAnalyzer
    skill_result = SkillAnalyzer().analyze(raw_data)

    from modules.dependency_analyzer import analyze_dependencies
    dep_result = analyze_dependencies(raw_data)

    from modules import get_github_token
    token = get_github_token()
"""

__version__ = "2.0.0"
__author__ = "Talent Intelligence Team"

# Core exports
from .harvester import harvest
from .client import get_github_client, get_github_token, handle_rate_limit
from .storage import (
    save_harvested_data,
    load_json,
    validate_harvested_data,
    get_file_size_mb,
)
from .aggregates import compute_all_aggregates

# Skill Analyzer exports
from .skill_analyzer import (
    SkillAnalyzer,
    SkillIntelligenceResult,
    SkillProfile,
    TechGraph,
    DomainProfile,
    DepthIndex,
    StackModernity,
)

# Dependency Analyzer exports
from .dependency_analyzer import (
    DependencyAnalyzer,
    analyze_dependencies,
)

# Candidate Profile builder
from .candidate_profile import (
    CandidateProfile,
    ProfileBuilder,
    build_candidate_profile,
)

# Commit Intelligence (for integration bridge)
from .commit_analyzer import (
    CommitIntelligenceEngine,
    analyze_commits,
)

# Explainability exports
from .explainability import (
    ExplainabilityEngine,
    explain_skill_intelligence,
    ExplainableSkill,
    ExplainableResult,
    EvidenceItem,
    EvidenceSource,
    ProjectEvidence,
    ProblemTrace,
)

# Codeforces Intelligence exports
from .codeforces import (
    CodeforcesAnalyzer,
    analyze_codeforces_profile,
    FlagDetector,
    detect_flags,
    is_flagged,
    get_cheated_contests,
    get_rating_tier,
    get_topic_breakdown,
    get_difficulty_breakdown,
    map_cf_topics_to_job_skills,
    get_problem_solving_score,
    get_tier_description,
    CF_TOPIC_TO_JOB_SKILLS,
    RATING_TIER_SCORES,
)

__all__ = [
    # Main harvest function
    "harvest",
    # Client utilities
    "get_github_client",
    "get_github_token",
    "handle_rate_limit",
    # Storage utilities
    "save_harvested_data",
    "load_json",
    "validate_harvested_data",
    "get_file_size_mb",
    # Aggregation
    "compute_all_aggregates",
    # Skill Analyzer
    "SkillAnalyzer",
    "SkillIntelligenceResult",
    "SkillProfile",
    "TechGraph",
    "DomainProfile",
    "DepthIndex",
    "StackModernity",
    # Dependency Analyzer
    "DependencyAnalyzer",
    "analyze_dependencies",
    # Candidate Profile
    "CandidateProfile",
    "ProfileBuilder",
    "build_candidate_profile",
    # Commit Intelligence
    "CommitIntelligenceEngine",
    "analyze_commits",
    # Explainability
    "ExplainabilityEngine",
    "explain_skill_intelligence",
    "ExplainableSkill",
    "ExplainableResult",
    "EvidenceItem",
    "EvidenceSource",
    "ProjectEvidence",
    "ProblemTrace",
    # Codeforces Intelligence
    "CodeforcesAnalyzer",
    "analyze_codeforces_profile",
    "FlagDetector",
    "detect_flags",
    "is_flagged",
    "get_cheated_contests",
    "get_rating_tier",
    "get_topic_breakdown",
    "get_difficulty_breakdown",
    "map_cf_topics_to_job_skills",
    "get_problem_solving_score",
    "get_tier_description",
    "CF_TOPIC_TO_JOB_SKILLS",
    "RATING_TIER_SCORES",
]
