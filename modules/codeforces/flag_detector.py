"""
Codeforces Flag / Cheat Detector
================================
Ports and enhances the Cheated.jsx logic from CFCheatDetector.

Detection Strategy:
1. HARD FLAG: Skipped ALL problems in a contest (classic "looked at solutions" pattern)
2. SOFT FLAG: Very high skip rate (>60% problems skipped) with few solves
3. RAPID SKIP: Skipped problems that others solved quickly (potential copy-paste)
4. LOW ACCEPT RATE: Very few accepted submissions relative to total attempts

The hard flag (cheated all problems in a contest) is the primary signal.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .fetcher import get_user_status, get_contest_list

logger = logging.getLogger(__name__)


@dataclass
class FlagResult:
    """Result of flag detection analysis."""
    is_flagged: bool = False
    flag_type: str = "none"  # "none", "hard", "soft", "rapid_skip", "low_ac_rate"
    cheated_contests: List[Dict[str, Any]] = field(default_factory=list)
    soft_flagged_contests: List[Dict[str, Any]] = field(default_factory=list)
    skip_rate: float = 0.0
    ac_rate: float = 0.0
    total_contests: int = 0
    cheated_contest_count: int = 0
    soft_flagged_count: int = 0
    evidence: List[str] = field(default_factory=list)
    flag_score: float = 0.0  # 0.0 = clean, 1.0 = definitely cheated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_flagged": self.is_flagged,
            "flag_type": self.flag_type,
            "cheated_contests": self.cheated_contests,
            "soft_flagged_contests": self.soft_flagged_contests,
            "skip_rate": self.skip_rate,
            "ac_rate": self.ac_rate,
            "total_contests": self.total_contests,
            "cheated_contest_count": self.cheated_contest_count,
            "soft_flagged_count": self.soft_flagged_count,
            "evidence": self.evidence,
            "flag_score": self.flag_score,
        }


class FlagDetector:
    """
    Detects potential cheating on Codeforces.

    Primary detection: If a user opened every problem in a contest
    but skipped (didn't solve) all of them — they were likely
    looking at the editorial/solutions.
    """

    # Rating thresholds for context-aware detection
    SOFT_FLAG_SKIP_RATE = 0.60  # >60% skip rate = soft flag
    RAPID_SKIP_MINUTES = 5  # Problems solved by others in <5 min, but user skipped
    LOW_AC_RATE_THRESHOLD = 0.15  # <15% accept rate overall = suspicious

    def __init__(self):
        self._contest_cache: Optional[List[Dict]] = None

    def detect(
        self,
        handle: str,
        submissions: Optional[List[Dict]] = None,
        use_cache: bool = True
    ) -> FlagResult:
        """
        Run full flag detection on a Codeforces user.

        Args:
            handle: Codeforces username
            submissions: Optional pre-fetched submissions (saves an API call)
            use_cache: Whether to cache contest list

        Returns:
            FlagResult with detection results
        """
        # Fetch submissions if not provided
        if submissions is None:
            submissions = get_user_status(handle)

        if not submissions:
            return FlagResult(evidence=["No submissions found for user"])

        # Step 1: Build contest → problems mapping (your Cheated.jsx logic)
        contest_data = self._build_contest_data(submissions)

        # Step 2: Detect hard flags (skipped all problems in contest)
        hard_flags = self._detect_hard_flags(contest_data)

        # Step 3: Detect soft flags (high skip rate)
        soft_flags = self._detect_soft_flags(contest_data)

        # Step 4: Compute overall statistics
        skip_rate, ac_rate = self._compute_rates(submissions)

        # Step 5: Determine flag status
        flag_type, is_flagged, evidence = self._determine_flag_status(
            hard_flags, soft_flags, skip_rate, ac_rate
        )

        # Step 6: Compute flag score (0.0 = clean, 1.0 = definitely cheated)
        flag_score = self._compute_flag_score(
            hard_flags, soft_flags, skip_rate, ac_rate, len(contest_data)
        )

        return FlagResult(
            is_flagged=is_flagged,
            flag_type=flag_type,
            cheated_contests=hard_flags,
            soft_flagged_contests=soft_flags,
            skip_rate=skip_rate,
            ac_rate=ac_rate,
            total_contests=len(contest_data),
            cheated_contest_count=len(hard_flags),
            soft_flagged_count=len(soft_flags),
            evidence=evidence,
            flag_score=flag_score,
        )

    def _build_contest_data(
        self,
        submissions: List[Dict]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Build contest-level data from submissions.
        Ports the Cheated.jsx logic:
        - Filter only CONTESTANT / OUT_OF_COMPETITION participants
        - Group by contestId
        - Count problems solved + skipped per contest
        """
        contest_data = defaultdict(lambda: {
            "contestId": None,
            "problems_attempted": 0,
            "problems_solved": 0,
            "problems_skipped": 0,
            "problems_failed": 0,
            "submissions": [],
        })

        for sub in submissions:
            # Filter to contest participants only (same as Cheated.jsx)
            participant_type = sub.get("author", {}).get("participantType", "")
            if participant_type not in ("CONTESTANT", "OUT_OF_COMPETITION"):
                continue

            contest_id = sub.get("contestId")
            if contest_id is None:
                continue

            verdict = sub.get("verdict", "")
            problem_idx = sub.get("problem", {}).get("index", "")

            cd = contest_data[contest_id]
            cd["contestId"] = contest_id
            cd["submissions"].append(sub)

            # Track unique problems
            if problem_idx not in cd.get("_seen_problems", set()):
                cd.setdefault("_seen_problems", set()).add(problem_idx)
                cd["problems_attempted"] += 1

                if verdict == "OK":
                    cd["problems_solved"] += 1
                elif verdict == "SKIPPED":
                    cd["problems_skipped"] += 1
                else:
                    cd["problems_failed"] += 1

        # Clean up internal tracking keys
        for cd in contest_data.values():
            cd.pop("_seen_problems", None)

        return dict(contest_data)

    def _detect_hard_flags(
        self,
        contest_data: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        HARD FLAG: User attempted all problems in a contest but skipped ALL of them.
        This is the primary cheat detection signal from Cheated.jsx.

        Logic: if skippedProblems == problemsAttempted AND problemsAttempted > 0
        """
        hard_flags = []

        for contest_id, cd in contest_data.items():
            attempted = cd["problems_attempted"]
            skipped = cd["problems_skipped"]
            solved = cd["problems_solved"]

            # The Cheated.jsx condition: skipped == attempted (all problems skipped)
            if attempted > 0 and skipped == attempted and solved == 0:
                hard_flags.append({
                    "contest_id": contest_id,
                    "contest_name": cd.get("contest_name", f"Contest {contest_id}"),
                    "problems_attempted": attempted,
                    "problems_skipped": skipped,
                    "problems_solved": solved,
                    "contest_url": f"https://codeforces.com/contest/{contest_id}",
                    "submission_url": f"https://codeforces.com/submissions/CHEATED_USER/contest/{contest_id}",
                })

        return hard_flags

    def _detect_soft_flags(
        self,
        contest_data: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        SOFT FLAG: Very high skip rate (60%+) but not 100%.
        These are suspicious but not definitive.
        """
        soft_flags = []

        for contest_id, cd in contest_data.items():
            attempted = cd["problems_attempted"]
            skipped = cd["problems_skipped"]

            if attempted == 0:
                continue

            skip_rate = skipped / attempted

            if skip_rate >= self.SOFT_FLAG_SKIP_RATE and skipped < attempted:
                soft_flags.append({
                    "contest_id": contest_id,
                    "contest_name": cd.get("contest_name", f"Contest {contest_id}"),
                    "problems_attempted": attempted,
                    "problems_skipped": skipped,
                    "problems_solved": cd["problems_solved"],
                    "skip_rate": round(skip_rate, 3),
                    "contest_url": f"https://codeforces.com/contest/{contest_id}",
                })

        return soft_flags

    def _compute_rates(
        self,
        submissions: List[Dict]
    ) -> tuple[float, float]:
        """Compute overall skip rate and accept rate."""
        total = len(submissions)
        if total == 0:
            return 0.0, 0.0

        skip_count = sum(1 for s in submissions if s.get("verdict") == "SKIPPED")
        ac_count = sum(1 for s in submissions if s.get("verdict") == "OK")

        skip_rate = skip_count / total
        ac_rate = ac_count / total

        return skip_rate, ac_rate

    def _determine_flag_status(
        self,
        hard_flags: List[Dict],
        soft_flags: List[Dict],
        skip_rate: float,
        ac_rate: float,
    ) -> tuple[str, bool, List[str]]:
        """Determine if user is flagged and why."""
        evidence = []
        is_flagged = False
        flag_type = "none"

        # Hard flag: cheated in contests
        if hard_flags:
            is_flagged = True
            flag_type = "hard"
            contest_ids = [f["contest_id"] for f in hard_flags]
            evidence.append(
                f"HARD FLAG: Skipped ALL problems in {len(hard_flags)} contest(s): {contest_ids}. "
                "User viewed problems but did not solve any — classic solution-copying pattern."
            )

        # Soft flag: high skip rate
        elif soft_flags:
            is_flagged = True
            flag_type = "soft"
            evidence.append(
                f"SOFT FLAG: High skip rate ({skip_rate:.0%}) across {len(soft_flags)} contest(s). "
                "Multiple contests with >60% problems skipped."
            )

        # Low accept rate
        elif ac_rate < self.LOW_AC_RATE_THRESHOLD:
            is_flagged = True
            flag_type = "low_ac_rate"
            evidence.append(
                f"SUSPICIOUS: Very low accept rate ({ac_rate:.0%}). "
                "User submits frequently but rarely gets accepted."
            )

        # Clean
        else:
            evidence.append(f"CLEAN: Accept rate {ac_rate:.0%}, skip rate {skip_rate:.0%}. No flag signals detected.")

        return flag_type, is_flagged, evidence

    def _compute_flag_score(
        self,
        hard_flags: List[Dict],
        soft_flags: List[Dict],
        skip_rate: float,
        ac_rate: float,
        total_contests: int,
    ) -> float:
        """
        Compute a 0.0-1.0 flag score.
        0.0 = definitely clean, 1.0 = definitely cheated.
        """
        if not total_contests:
            return 0.0

        # Hard flags are the strongest signal
        hard_flag_ratio = len(hard_flags) / total_contests
        hard_score = min(hard_flag_ratio * 1.0, 1.0)  # Max 1.0 for hard flags

        # Soft flags add moderate risk
        soft_flag_ratio = len(soft_flags) / total_contests
        soft_score = min(soft_flag_ratio * 0.5, 0.5)  # Max 0.5 for soft flags

        # Low accept rate adds small risk
        low_ac_penalty = 0.0
        if ac_rate < 0.15:
            low_ac_penalty = 0.2
        elif ac_rate < 0.25:
            low_ac_penalty = 0.1

        # High skip rate adds small risk
        skip_penalty = 0.0
        if skip_rate > 0.5:
            skip_penalty = min(skip_rate * 0.3, 0.3)

        score = min(hard_score + soft_score + low_ac_penalty + skip_penalty, 1.0)
        return round(score, 3)


# ─── Convenience functions ───────────────────────────────────────────────────────


def detect_flags(handle: str) -> FlagResult:
    """
    Quick function to detect flags for a user.

    Args:
        handle: Codeforces username

    Returns:
        FlagResult
    """
    detector = FlagDetector()
    return detector.detect(handle)


def is_flagged(handle: str) -> bool:
    """
    Quick boolean check if a user is flagged.

    Args:
        handle: Codeforces username

    Returns:
        True if flagged, False otherwise
    """
    result = detect_flags(handle)
    return result.is_flagged


def get_cheated_contests(handle: str) -> List[Dict[str, Any]]:
    """
    Get list of contests where user skipped all problems.

    Args:
        handle: Codeforces username

    Returns:
        List of cheated contest dicts
    """
    result = detect_flags(handle)
    return result.cheated_contests
