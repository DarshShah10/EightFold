"""
Codeforces Analyzer
==================
Analyzes Codeforces data beyond flag detection:
- Rating tiers with color badges
- Problem difficulty breakdown
- Topic/tag analysis
- Rating trajectory
- Contest participation patterns
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .fetcher import (
    get_user_info,
    get_user_status,
    get_user_rating,
    get_contest_list,
)
from .flag_detector import FlagDetector, FlagResult

logger = logging.getLogger(__name__)


# ─── Rating Tier Definitions ──────────────────────────────────────────────────────

RATING_TIERS = {
    (0, 1199): ("Newbie", "⚪"),
    (1200, 1399): ("Pupil", "🟢"),
    (1400, 1599): ("Specialist", "🔵"),
    (1600, 1899): ("Expert", "🔵"),
    (1900, 2099): ("Candidate Master", "🟣"),
    (2100, 2299): ("Master", "🔴"),
    (2300, 2399): ("International Master", "🟠"),
    (2400, 2599): ("Grandmaster", "🔴"),
    (2600, 2999): ("International Grandmaster", "🟠"),
    (3000, 9999): ("Legendary Grandmaster", "🟡"),
}

RATING_COLORS = {
    "Newbie": "#808080",
    "Pupil": "#808080",
    "Specialist": "#008000",
    "Expert": "#0000FF",
    "Candidate Master": "#AA00AA",
    "Master": "#FF0000",
    "International Master": "#FF8C00",
    "Grandmaster": "#FF0000",
    "International Grandmaster": "#FF8C00",
    "Legendary Grandmaster": "#FFD700",
}


def get_rating_tier(rating: int) -> tuple[str, str]:
    """
    Get the rating tier name and emoji for a rating.

    Args:
        rating: Codeforces rating

    Returns:
        (tier_name, emoji)
    """
    for (low, high), (name, emoji) in RATING_TIERS.items():
        if low <= rating <= high:
            return name, emoji
    return "Unrated", "⚪"


def get_rating_color(tier_name: str) -> str:
    """Get hex color for a rating tier."""
    return RATING_COLORS.get(tier_name, "#808080")


# ─── Difficulty Buckets ─────────────────────────────────────────────────────────

DIFFICULTY_BUCKETS = [
    (0, 800, "800 (Warmup)"),
    (801, 1000, "1000 (Easy)"),
    (1001, 1200, "1200 (Easy-Med)"),
    (1201, 1400, "1400 (Medium)"),
    (1401, 1600, "1600 (Medium-Hard)"),
    (1601, 1800, "1800 (Hard)"),
    (1801, 2000, "2000 (Very Hard)"),
    (2001, 2200, "2200 (Expert)"),
    (2201, 2400, "2400 (Master)"),
    (2401, 2600, "2600 (Grandmaster)"),
    (2601, 3000, "2600+ (Grandmaster+)"),
]


def get_difficulty_bucket(rating: int) -> str:
    """Get difficulty bucket name for a problem rating."""
    for low, high, name in DIFFICULTY_BUCKETS:
        if low <= rating <= high:
            return name
    if rating > 3000:
        return f"{rating}+ (Extreme)"
    return "Unrated"


# ─── Data Models ───────────────────────────────────────────────────────────────


@dataclass
class TopicStats:
    """Statistics for a single topic/tag."""
    name: str
    count: int = 0
    solved_count: int = 0
    avg_rating: float = 0.0
    max_rating: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "solved_count": self.solved_count,
            "avg_rating": round(self.avg_rating, 1),
            "max_rating": self.max_rating,
        }


@dataclass
class CodeforcesAnalysis:
    """Complete Codeforces analysis result."""
    handle: str
    # Basic info
    rating: int = 0
    max_rating: int = 0
    rank: str = "unrated"
    max_rank: str = "unrated"
    rating_tier: str = "Unrated"
    rating_emoji: str = "⚪"
    # Flag detection
    flag_result: Optional[FlagResult] = None
    # Submissions
    total_submissions: int = 0
    accepted_count: int = 0
    ac_rate: float = 0.0
    # Problems solved
    problems_solved: int = 0
    # Difficulty breakdown
    difficulty_breakdown: Dict[str, int] = field(default_factory=dict)
    # Topics
    topics: List[TopicStats] = field(default_factory=list)
    top_topics: List[str] = field(default_factory=list)
    # Rating trajectory
    rating_history: List[Dict] = field(default_factory=list)
    rating_trend: str = "stable"  # "improving", "declining", "stable"
    # Contests
    contest_count: int = 0
    avg_rank: int = 0
    # Language stats
    languages: Dict[str, int] = field(default_factory=dict)
    # Problem-solving score (0-1)
    problem_solving_score: float = 0.0
    # Job-relevant skills
    job_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handle": self.handle,
            "rating": self.rating,
            "max_rating": self.max_rating,
            "rank": self.rank,
            "max_rank": self.max_rank,
            "rating_tier": self.rating_tier,
            "rating_emoji": self.rating_emoji,
            "flag_result": self.flag_result.to_dict() if self.flag_result else None,
            "total_submissions": self.total_submissions,
            "accepted_count": self.accepted_count,
            "ac_rate": round(self.ac_rate, 3),
            "problems_solved": self.problems_solved,
            "difficulty_breakdown": self.difficulty_breakdown,
            "topics": [t.to_dict() for t in self.topics],
            "top_topics": self.top_topics,
            "rating_history": self.rating_history,
            "rating_trend": self.rating_trend,
            "contest_count": self.contest_count,
            "avg_rank": self.avg_rank,
            "languages": self.languages,
            "problem_solving_score": round(self.problem_solving_score, 3),
            "job_skills": self.job_skills,
        }


# ─── Main Analyzer ──────────────────────────────────────────────────────────────


class CodeforcesAnalyzer:
    """
    Comprehensive Codeforces profile analyzer.
    """

    def __init__(self):
        self.flag_detector = FlagDetector()

    def analyze(
        self,
        handle: str,
        fetch_submissions: bool = True,
    ) -> CodeforcesAnalysis:
        """
        Run full analysis on a Codeforces profile.

        Args:
            handle: Codeforces username
            fetch_submissions: Whether to fetch all submissions (slower)

        Returns:
            CodeforcesAnalysis with all signals
        """
        analysis = CodeforcesAnalysis(handle=handle)

        # Step 1: User info
        try:
            info = get_user_info(handle)
            analysis.rating = info.get("rating", 0) or 0
            analysis.max_rating = info.get("maxRating", 0) or 0
            analysis.rank = info.get("rank", "unrated") or "unrated"
            analysis.max_rank = info.get("maxRank", "unrated") or "unrated"
            tier, emoji = get_rating_tier(analysis.max_rating)
            analysis.rating_tier = tier
            analysis.rating_emoji = emoji
        except ValueError as e:
            logger.warning(f"Could not fetch user info for {handle}: {e}")
            return analysis

        # Step 2: Flag detection
        try:
            analysis.flag_result = self.flag_detector.detect(handle)
        except ValueError as e:
            logger.warning(f"Flag detection failed for {handle}: {e}")

        # Step 3: Submissions analysis
        submissions = []
        if fetch_submissions:
            try:
                submissions = get_user_status(handle)
            except ValueError as e:
                logger.warning(f"Could not fetch submissions for {handle}: {e}")

        self._analyze_submissions(submissions, analysis)

        # Step 4: Rating history
        try:
            rating_history = get_user_rating(handle)
            analysis.rating_history = self._process_rating_history(rating_history)
            analysis.contest_count = len(rating_history)
            if rating_history:
                ranks = [r.get("rank", 0) for r in rating_history]
                analysis.avg_rank = int(sum(ranks) / len(ranks)) if ranks else 0
        except ValueError as e:
            logger.warning(f"Could not fetch rating history for {handle}: {e}")

        # Step 5: Compute problem-solving score
        analysis.problem_solving_score = self._compute_problem_solving_score(analysis)

        return analysis

    def _analyze_submissions(
        self,
        submissions: List[Dict],
        analysis: CodeforcesAnalysis,
    ) -> None:
        """Analyze submission patterns."""
        if not submissions:
            return

        analysis.total_submissions = len(submissions)

        # AC rate
        ac_count = sum(1 for s in submissions if s.get("verdict") == "OK")
        analysis.accepted_count = ac_count
        analysis.ac_rate = ac_count / len(submissions) if submissions else 0

        # Track unique solved problems
        solved_problems = set()
        difficulty_counter = Counter()
        topic_counter = Counter()
        language_counter = Counter()
        topic_ratings: Dict[str, List[int]] = defaultdict(list)

        for sub in submissions:
            if sub.get("verdict") != "OK":
                continue

            problem = sub.get("problem", {})
            problem_key = f"{problem.get('contestId')}_{problem.get('index')}"

            if problem_key in solved_problems:
                continue
            solved_problems.add(problem_key)

            # Difficulty
            rating = problem.get("rating")
            if rating:
                bucket = get_difficulty_bucket(rating)
                difficulty_counter[bucket] += 1

            # Topics
            tags = problem.get("tags", [])
            for tag in tags:
                topic_counter[tag] += 1
                if rating:
                    topic_ratings[tag].append(rating)

            # Language
            lang = sub.get("programmingLanguage", "Unknown")
            language_counter[lang] += 1

        analysis.problems_solved = len(solved_problems)
        analysis.difficulty_breakdown = dict(difficulty_counter)
        analysis.languages = dict(language_counter)

        # Top topics
        top_tags = [tag for tag, _ in topic_counter.most_common(10)]
        analysis.top_topics = top_tags

        # Topic stats
        analysis.topics = []
        for tag, count in topic_counter.most_common(10):
            ratings = topic_ratings.get(tag, [])
            analysis.topics.append(TopicStats(
                name=tag,
                count=count,
                solved_count=count,
                avg_rating=sum(ratings) / len(ratings) if ratings else 0.0,
                max_rating=max(ratings) if ratings else 0,
            ))

    def _process_rating_history(
        self,
        rating_history: List[Dict]
    ) -> List[Dict]:
        """Process rating history for trajectory analysis."""
        processed = []
        for entry in rating_history:
            ts = entry.get("ratingUpdateTimeSeconds", 0)
            date = datetime.fromtimestamp(ts).strftime("%Y-%m") if ts else "Unknown"
            processed.append({
                "contest_id": entry.get("contestId"),
                "contest_name": entry.get("contestName", ""),
                "rank": entry.get("rank", 0),
                "old_rating": entry.get("oldRating", 0),
                "new_rating": entry.get("newRating", 0),
                "date": date,
            })
        return processed

    def _compute_problem_solving_score(
        self,
        analysis: CodeforcesAnalysis,
    ) -> float:
        """
        Compute a 0-1 problem-solving score based on all signals.
        This feeds into the adaptive scoring engine.
        """
        score = 0.0

        # Flag penalty: hard flag = no score
        if analysis.flag_result:
            flag_score = analysis.flag_result.flag_score
            if flag_score >= 0.8:
                return 0.0  # Definitely cheated
            elif flag_score >= 0.5:
                score *= 0.3  # Heavy penalty

        # Max rating contribution (40%)
        max_rating = analysis.max_rating
        if max_rating >= 2400:
            rating_contrib = 0.40
        elif max_rating >= 1900:
            rating_contrib = 0.32
        elif max_rating >= 1600:
            rating_contrib = 0.24
        elif max_rating >= 1400:
            rating_contrib = 0.16
        elif max_rating >= 1200:
            rating_contrib = 0.10
        elif max_rating > 0:
            rating_contrib = 0.05
        else:
            rating_contrib = 0.0
        score += rating_contrib

        # Problems solved (20%)
        problems = analysis.problems_solved
        if problems >= 500:
            prob_contrib = 0.20
        elif problems >= 200:
            prob_contrib = 0.16
        elif problems >= 100:
            prob_contrib = 0.12
        elif problems >= 50:
            prob_contrib = 0.08
        elif problems >= 20:
            prob_contrib = 0.04
        else:
            prob_contrib = 0.01
        score += prob_contrib

        # Hard problems (difficulty 2000+) (20%)
        hard_count = sum(
            count for bucket, count in analysis.difficulty_breakdown.items()
            if "2000" in bucket or "2200" in bucket or "2400" in bucket or "2600" in bucket or "Extreme" in bucket
        )
        if hard_count >= 20:
            hard_contrib = 0.20
        elif hard_count >= 10:
            hard_contrib = 0.15
        elif hard_count >= 5:
            hard_contrib = 0.10
        elif hard_count >= 1:
            hard_contrib = 0.05
        else:
            hard_contrib = 0.0
        score += hard_contrib

        # Contest participation (10%)
        contests = analysis.contest_count
        if contests >= 50:
            contest_contrib = 0.10
        elif contests >= 20:
            contest_contrib = 0.08
        elif contests >= 10:
            contest_contrib = 0.05
        elif contests >= 5:
            contest_contrib = 0.03
        else:
            contest_contrib = 0.01
        score += contest_contrib

        # AC rate (10%)
        ac_rate = analysis.ac_rate
        if ac_rate >= 0.5:
            ac_contrib = 0.10
        elif ac_rate >= 0.35:
            ac_contrib = 0.07
        elif ac_rate >= 0.20:
            ac_contrib = 0.04
        else:
            ac_contrib = 0.01
        score += ac_contrib

        return min(score, 1.0)


# ─── Convenience functions ───────────────────────────────────────────────────────


def analyze_codeforces_profile(handle: str) -> CodeforcesAnalysis:
    """Quick function to analyze a Codeforces profile."""
    analyzer = CodeforcesAnalyzer()
    return analyzer.analyze(handle)


def get_topic_breakdown(handle: str) -> List[TopicStats]:
    """Get topic/tag breakdown for a user."""
    analyzer = CodeforcesAnalyzer()
    analysis = analyzer.analyze(handle)
    return analysis.topics


def get_difficulty_breakdown(handle: str) -> Dict[str, int]:
    """Get problems solved by difficulty bucket."""
    analyzer = CodeforcesAnalyzer()
    analysis = analyzer.analyze(handle)
    return analysis.difficulty_breakdown
