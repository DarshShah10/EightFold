"""
Codeforces Intelligence Module
==============================
Integrates Codeforces competitive programming data into the talent intelligence system.

Features:
- Flag/Cheat detection (skipped all problems in contests)
- Rating analysis with tier badges
- Problem difficulty breakdown
- Topic/tag skill mapping to job-relevant skills
- Problem-solving ability scoring

Author: Techkriti '26 x EightFold AI
"""

from .fetcher import (
    get_user_info,
    get_user_status,
    get_contest_list,
    get_user_rating,
    get_user_standings,
)
from .flag_detector import (
    FlagDetector,
    detect_flags,
    is_flagged,
    get_cheated_contests,
)
from .analyzer import (
    CodeforcesAnalyzer,
    analyze_codeforces_profile,
    get_rating_tier,
    get_topic_breakdown,
    get_difficulty_breakdown,
)
from .skills_mapper import (
    map_cf_topics_to_job_skills,
    get_problem_solving_score,
    get_tier_description,
    CF_TOPIC_TO_JOB_SKILLS,
    RATING_TIER_SCORES,
)

__all__ = [
    # Fetcher
    "get_user_info",
    "get_user_status",
    "get_contest_list",
    "get_user_rating",
    "get_user_standings",
    # Flag Detector
    "FlagDetector",
    "detect_flags",
    "is_flagged",
    "get_cheated_contests",
    # Analyzer
    "CodeforcesAnalyzer",
    "analyze_codeforces_profile",
    "get_rating_tier",
    "get_topic_breakdown",
    "get_difficulty_breakdown",
    # Skills Mapper
    "map_cf_topics_to_job_skills",
    "get_problem_solving_score",
    "get_tier_description",
    "CF_TOPIC_TO_JOB_SKILLS",
    "RATING_TIER_SCORES",
]
