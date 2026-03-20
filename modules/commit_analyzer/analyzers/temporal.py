"""
Temporal Pattern Analyzer
=========================
Analyzes time-of-day, day-of-week, and velocity patterns.

Signals extracted:
- hour_of_day_distribution (peak hours)
- weekend_commit_ratio
- late_night_commit_ratio (midnight-5am)
- early_bird_ratio (5am-8am)
- night_owl_ratio (9pm-12am)
- consistency_score (std dev of daily commits)
- velocity_burst_score (sudden spikes in activity)
- activity_concentration (Gini coefficient of hourly distribution)
- weekly_pattern_type (weekday/weekend/mixed)
"""

import math
import statistics
from collections import Counter
from typing import Any, Dict, List, Tuple


class TemporalAnalyzer:
    """
    Analyzes temporal patterns in commit behavior.

    Temporal signals reveal:
    - Work schedule preferences (early bird vs night owl)
    - Work-life balance indicators
    - Consistency and discipline
    - Velocity patterns and bursts
    """

    # Hour buckets
    LATE_NIGHT_START = 0   # midnight - 5am
    EARLY_BIRD_END = 8     # 5am - 8am
    BUSINESS_START = 9     # 9am - 5pm
    BUSINESS_END = 17
    EVENING_END = 21       # 6pm - 9pm
    NIGHT_OWL_START = 21   # 9pm - midnight

    def analyze(self, commits: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract temporal patterns from commits.

        Args:
            commits: List of commit dictionaries with datetime info

        Returns:
            Dictionary of signal name -> value
        """
        signals: Dict[str, float] = {}

        if not commits:
            return self._empty_signals()

        # Extract temporal data
        hours = []
        weekdays = []
        daily_counts: Dict[str, int] = {}

        for commit in commits:
            # Get hour of day
            hour = commit.get("hour_of_day")
            if hour is not None:
                hours.append(int(hour))

            # Get day of week
            dow = commit.get("day_of_week")
            if dow is not None:
                weekdays.append(int(dow))

            # Track daily activity
            date_key = commit.get("year_month", "")
            if date_key:
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

        # Compute hour-based signals
        total = len(commits)
        signals["late_night_commit_ratio"] = self._count_in_range(hours, self.LATE_NIGHT_START, self.EARLY_BIRD_END) / total if total else 0.0
        signals["early_bird_ratio"] = self._count_in_range(hours, self.EARLY_BIRD_END, self.BUSINESS_START) / total if total else 0.0
        signals["business_hours_ratio"] = self._count_in_range(hours, self.BUSINESS_START, self.BUSINESS_END) / total if total else 0.0
        signals["evening_ratio"] = self._count_in_range(hours, self.BUSINESS_END, self.EVENING_END) / total if total else 0.0
        signals["night_owl_ratio"] = self._count_in_range(hours, self.NIGHT_OWL_START, 24) / total if total else 0.0

        # Weekend analysis
        if weekdays:
            weekend_count = sum(1 for d in weekdays if d >= 5)
            signals["weekend_commit_ratio"] = round(weekend_count / len(weekdays), 4)

        # Consistency score (lower std dev = more consistent)
        if daily_counts:
            daily_values = list(daily_counts.values())
            if len(daily_values) > 1:
                std_dev = statistics.stdev(daily_values)
                mean_activity = statistics.mean(daily_values)
                # Normalize: 0 std dev = 100, higher std dev = lower score
                signals["consistency_score"] = round(max(0, 100 - std_dev * 5), 1)
            else:
                signals["consistency_score"] = 100.0

        # Velocity burst score (detects sudden activity spikes)
        signals["velocity_burst_score"] = self._compute_burst_score(daily_counts)

        # Activity concentration (Gini coefficient - lower = more evenly distributed)
        if hours:
            signals["activity_concentration"] = self._gini_coefficient(hours)

        # Peak hour identification
        if hours:
            hour_counts = Counter(hours)
            most_common_hour, _ = hour_counts.most_common(1)[0]
            signals["peak_hour"] = float(most_common_hour)
            signals["peak_hour_ratio"] = round(most_common_hour / total, 4) if total else 0.0

        # Weekly pattern classification
        signals["weekly_pattern_score"] = self._compute_weekly_pattern(weekdays)

        # Time zone inference (based on typical activity hours)
        if hours:
            avg_hour = statistics.mean(hours)
            signals["inferred_timezone_offset"] = round(avg_hour - 14, 1)  # Rough estimate from UTC

        return signals

    def _count_in_range(self, values: List[int], start: int, end: int) -> int:
        """Count values within a range (inclusive start, exclusive end)."""
        return sum(1 for v in values if start <= v < end)

    def _compute_burst_score(self, daily_counts: Dict[str, int]) -> float:
        """
        Compute velocity burst score (0-100).
        Higher score = more unpredictable/bursty activity.
        """
        if len(daily_counts) < 3:
            return 0.0

        values = list(daily_counts.values())
        mean = statistics.mean(values)

        if mean == 0:
            return 0.0

        # Calculate coefficient of variation (CV)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        cv = std_dev / mean

        # Map CV to burst score: CV of 0 = 0 burst, CV of 2+ = 100 burst
        burst_score = min(cv * 50, 100)
        return round(burst_score, 1)

    def _gini_coefficient(self, values: List[int]) -> float:
        """
        Compute Gini coefficient for activity distribution.
        Lower = more evenly distributed across hours.
        Higher = concentrated in specific hours.
        """
        if not values:
            return 0.0

        # Count occurrences per hour
        hour_counts = Counter(values)
        hours = list(range(24))

        # Create distribution
        distribution = [hour_counts.get(h, 0) for h in hours]
        n = len(distribution)
        total = sum(distribution)

        if total == 0:
            return 0.0

        # Normalize
        distribution = [x / total for x in distribution]

        # Gini formula
        sorted_dist = sorted(distribution)
        cumsum = 0
        for i, val in enumerate(sorted_dist):
            cumsum += (2 * (i + 1) - n - 1) * val

        gini = cumsum / n
        return round(abs(gini), 4)

    def _compute_weekly_pattern(self, weekdays: List[int]) -> float:
        """
        Compute weekly pattern score (0-100).
        100 = perfect weekday worker (Mon-Fri)
        0 = pure weekend worker
        """
        if not weekdays:
            return 50.0

        weekday_count = sum(1 for d in weekdays if 0 <= d <= 4)
        weekend_count = sum(1 for d in weekdays if d >= 5)

        total = len(weekdays)
        weekday_ratio = weekday_count / total

        # Ideal is 100% weekday, but some weekend work is healthy
        # Penalize pure weekend work, reward balanced Mon-Fri
        if weekend_count == 0 and weekday_count > 0:
            return 100.0
        elif weekday_count > 0 and weekend_count > 0:
            # Mixed pattern - score based on weekday ratio
            return round(weekday_ratio * 100, 1)
        else:
            return 0.0

    def _empty_signals(self) -> Dict[str, float]:
        """Return empty signals dictionary."""
        return {
            "late_night_commit_ratio": 0.0,
            "early_bird_ratio": 0.0,
            "business_hours_ratio": 0.0,
            "evening_ratio": 0.0,
            "night_owl_ratio": 0.0,
            "weekend_commit_ratio": 0.0,
            "consistency_score": 0.0,
            "velocity_burst_score": 0.0,
            "activity_concentration": 0.0,
            "peak_hour": 0.0,
            "peak_hour_ratio": 0.0,
            "weekly_pattern_score": 0.0,
            "inferred_timezone_offset": 0.0,
        }
