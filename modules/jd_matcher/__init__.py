"""
JD Matcher Package
=================
Matches candidate GitHub profiles against job descriptions with full traceability.

Usage:
    from modules.jd_matcher import match_jd, parse_job_description, JDMatchResult

    # Parse job description
    parsed_jd = parse_job_description(jd_text)

    # Match candidate (uses dynamic matching)
    result = match_jd(candidate, raw_data, skill_result, jd_text)

    # Print report
    from modules.jd_matcher.types import format_match_result
    print(format_match_result(result))
"""

from modules.jd_matcher.jd_parser import (
    parse_job_description,
    print_parsed_jd,
    ParsedJobDescription,
    SkillRequirement,
    ExperienceRequirement,
)
from modules.jd_matcher.llm_parser import (
    extract_skills_with_llm,
    extract_skills_basic,
    extract_skills_with_context,
)
from modules.jd_matcher.matcher import (
    match_jd,
    JDMatcher,
)
from modules.jd_matcher.matcher_v2 import (
    match_jd_dynamic,
    DynamicMatcher,
)
from modules.jd_matcher.types import (
    JDMatchResult,
    RequirementMatch,
    SkillMatch,
    EvidenceLink,
    format_match_result,
)

__version__ = "2.0.0"

__all__ = [
    # Parser
    "parse_job_description",
    "print_parsed_jd",
    "ParsedJobDescription",
    "SkillRequirement",
    "ExperienceRequirement",
    # LLM Parser
    "extract_skills_with_llm",
    "extract_skills_basic",
    "extract_skills_with_context",
    # Matcher
    "match_jd",
    "JDMatcher",
    "match_jd_dynamic",
    "DynamicMatcher",
    # Types
    "JDMatchResult",
    "RequirementMatch",
    "SkillMatch",
    "EvidenceLink",
    "format_match_result",
]
