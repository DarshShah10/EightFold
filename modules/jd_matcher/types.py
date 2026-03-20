"""
JD Matcher Types
================
Type definitions for JD matching.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvidenceLink:
    """A traceable link to evidence in GitHub data."""
    url: str  # GitHub URL to the evidence
    type: str  # 'repo', 'commit', 'file', 'dependency', 'topic'
    description: str  # Human-readable description
    weight: float  # How much this evidence contributes
    verified: bool = False  # Whether this has been manually verified


@dataclass
class SkillMatch:
    """Result of matching a JD skill against candidate data."""
    skill: str
    is_match: bool
    confidence: float  # 0-1 how confident we are
    evidence: list[EvidenceLink] = field(default_factory=list)
    evidence_summary: str = ""  # Human-readable summary
    contributing_repos: list[str] = field(default_factory=list)
    supporting_commits: list[str] = field(default_factory=list)
    missing_reason: str = ""  # Why this skill is missing
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class RequirementMatch:
    """Result of matching a full JD requirement."""
    requirement: str  # The original requirement text
    skill_key: str  # Normalized skill key
    category: str  # technical, tool, domain, etc.
    is_mandatory: bool
    match_result: SkillMatch
    overall_score: float  # 0-100 overall fit
    weight: float = 1.0  # Importance weight from JD


@dataclass
class JDMatchResult:
    """Complete JD matching result with full traceability."""
    candidate: str
    job_title: str
    overall_match_score: float  # 0-100

    # Skill matches
    mandatory_skills: list[RequirementMatch] = field(default_factory=list)
    nice_to_have_skills: list[RequirementMatch] = field(default_factory=list)

    # Summary
    matched_count: int = 0
    missing_count: int = 0
    partial_count: int = 0

    # Coverage by category
    category_scores: dict[str, float] = field(default_factory=dict)

    # Candidate strengths
    strengths: list[str] = field(default_factory=list)

    # Gaps/weaknesses
    gaps: list[str] = field(default_factory=list)

    # Missing skills that are critical
    critical_gaps: list[str] = field(default_factory=list)

    # Overall assessment
    recommendation: str = ""  # 'strong_match', 'partial_match', 'poor_match'
    summary: str = ""  # Human-readable summary

    # Traceability
    analysis_timestamp: str = ""


def format_match_result(result: JDMatchResult) -> str:
    """Format match result as human-readable report."""
    lines = []

    lines.append("=" * 70)
    lines.append(f"JD MATCH REPORT: {result.candidate} for {result.job_title}")
    lines.append("=" * 70)
    lines.append("")

    # Overall score
    lines.append(f"Overall Match Score: {result.overall_match_score:.0f}/100")
    lines.append(f"Recommendation: {result.recommendation.upper().replace('_', ' ')}")
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(result.summary)
    lines.append("")

    # Matched skills
    if result.mandatory_skills:
        matched = [m for m in result.mandatory_skills if m.match_result.is_match]
        lines.append(f"MATCHED MANDATORY SKILLS ({len(matched)}/{len(result.mandatory_skills)}):")
        lines.append("-" * 40)
        for match in matched[:10]:
            lines.append(f"  [+] {match.skill_key} ({match.match_result.confidence:.0%} confidence)")
            if match.match_result.evidence:
                for ev in match.match_result.evidence[:2]:
                    lines.append(f"      -> {ev.description}")
                    lines.append(f"        {ev.url}")
            lines.append("")
        lines.append("")

    # Missing skills
    missing = [m for m in result.mandatory_skills if not m.match_result.is_match]
    if missing:
        lines.append(f"MISSING/UNVERIFIED SKILLS ({len(missing)}):")
        lines.append("-" * 40)
        for match in missing[:15]:
            lines.append(f"  [-] {match.skill_key}")
            if match.match_result.missing_reason:
                lines.append(f"      Reason: {match.match_result.missing_reason}")
            lines.append("")
        lines.append("")

    # Nice to have
    nice_matched = [m for m in result.nice_to_have_skills if m.match_result.is_match]
    if result.nice_to_have_skills:
        lines.append(f"NICE TO HAVE ({len(nice_matched)}/{len(result.nice_to_have_skills)} matched):")
        lines.append("-" * 40)
        for match in result.nice_to_have_skills[:10]:
            if match.match_result.is_match:
                lines.append(f"  [+] {match.skill_key}")
            else:
                lines.append(f"  [o] {match.skill_key} (not found)")
        lines.append("")

    # Strengths
    if result.strengths:
        lines.append("STRENGTHS:")
        lines.append("-" * 40)
        for strength in result.strengths[:5]:
            lines.append(f"  * {strength}")
        lines.append("")

    # Critical gaps
    if result.critical_gaps:
        lines.append("CRITICAL GAPS:")
        lines.append("-" * 40)
        for gap in result.critical_gaps[:5]:
            lines.append(f"  ! {gap}")
        lines.append("")

    # Category scores
    if result.category_scores:
        lines.append("CATEGORY BREAKDOWN:")
        lines.append("-" * 40)
        for cat, score in sorted(result.category_scores.items(), key=lambda x: -x[1]):
            bar = "#" * int(score / 10) + "-" * (10 - int(score / 10))
            lines.append(f"  {cat:15} {bar} {score:.0f}%")
        lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)
