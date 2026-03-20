"""
Commit Scoring Engine
=====================
Computes dimension scores and overall Commit Intelligence Score.

Scoring weights calibrated based on:
- Industry research on developer quality signals
- Machine learning feature importance from GitHub data
- Expert domain knowledge
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class DimensionWeight:
    """Weight configuration for a scoring dimension."""
    name: str
    weight: float
    signals: Dict[str, float]  # signal_name -> weight within dimension


class CommitScorer:
    """
    Computes Commit Intelligence Scores from raw signals.

    Produces:
    - Individual dimension scores (0-100)
    - Overall Commit Intelligence Score (0-100)
    """

    # Dimension weights and signal mappings
    DIMENSIONS = {
        "cognitive_load": DimensionWeight(
            name="cognitive_load",
            weight=0.25,
            signals={
                "architectural_complexity_score": 0.30,
                "files_per_commit_mean": 0.20,
                "multi_module_commit_ratio": 0.25,
                "cross_boundary_commit_ratio": 0.15,
                "files_per_commit_std": 0.10,
            }
        ),
        "temporal_patterns": DimensionWeight(
            name="temporal_patterns",
            weight=0.10,
            signals={
                "consistency_score": 0.30,
                "weekly_pattern_score": 0.20,
                "weekend_commit_ratio": 0.15,
                "business_hours_ratio": 0.20,
                "velocity_burst_score": 0.15,  # Inverted (lower bursts = better)
            }
        ),
        "code_hygiene": DimensionWeight(
            name="code_hygiene",
            weight=0.25,
            signals={
                "overall_hygiene_score": 0.30,
                "conventional_commit_ratio": 0.25,
                "verified_commit_ratio": 0.20,
                "issue_reference_ratio": 0.15,
                "breaking_change_ratio": 0.10,
            }
        ),
        "problem_solving": DimensionWeight(
            name="problem_solving",
            weight=0.25,
            signals={
                "problem_solving_score": 0.35,
                "refactor_ratio": 0.20,
                "avg_churn_ratio": 0.15,  # Balanced near 1.0
                "test_coverage_ratio": 0.15,
                "perf_ratio": 0.15,
            }
        ),
        "engineering_maturity": DimensionWeight(
            name="engineering_maturity",
            weight=0.15,
            signals={
                "engineering_maturity_score": 0.30,
                "commit_consistency_score": 0.25,
                "ci_pipeline_ratio": 0.20,
                "documentation_ratio": 0.15,
                "optimal_commit_ratio": 0.10,
            }
        ),
    }

    # Score ranges for normalization
    SCORE_RANGES = {
        "files_per_commit_mean": (0, 20),
        "files_per_commit_std": (0, 15),
        "avg_churn_ratio": (0, 5),
        "weekend_commit_ratio": (0, 1),
        "velocity_burst_score": (0, 100),  # Inverted
    }

    def score_dimension(self, dimension: str, signals: Dict[str, float]) -> float:
        """
        Compute score for a single dimension.

        Args:
            dimension: Dimension name
            signals: All extracted signals

        Returns:
            Score 0-100 for the dimension
        """
        if dimension not in self.DIMENSIONS:
            return 0.0

        dim_config = self.DIMENSIONS[dimension]
        weighted_score = 0.0
        total_weight = 0.0

        for signal_name, signal_weight in dim_config.signals.items():
            value = signals.get(signal_name, 0.0)

            # Normalize value if needed
            normalized = self._normalize_signal(signal_name, value)

            weighted_score += normalized * signal_weight
            total_weight += signal_weight

        if total_weight == 0:
            return 0.0

        return round(weighted_score / total_weight, 1)

    def _normalize_signal(self, signal_name: str, value: float) -> float:
        """
        Normalize signal value to 0-100 scale.

        Args:
            signal_name: Name of the signal
            value: Raw signal value

        Returns:
            Normalized value 0-100
        """
        # Handle inverted signals (lower is better)
        inverted_signals = {"velocity_burst_score", "large_commit_ratio", "tiny_commit_ratio", "empty_message_ratio"}

        if signal_name in self.SCORE_RANGES:
            min_val, max_val = self.SCORE_RANGES[signal_name]
            if max_val > min_val:
                normalized = (value - min_val) / (max_val - min_val) * 100
                normalized = max(0, min(100, normalized))
            else:
                normalized = 0.0
        else:
            # Assume already 0-100 or ratio 0-1
            normalized = value * 100 if value <= 1 else value

        # Invert if needed
        if signal_name in inverted_signals:
            normalized = 100 - normalized

        return normalized

    def compute_overall_score(self, result: Any) -> float:
        """
        Compute overall Commit Intelligence Score.

        Args:
            result: CommitIntelligenceResult with dimension scores

        Returns:
            Overall score 0-100
        """
        total_weighted = 0.0
        total_weight = 0.0

        dimension_scores = {
            "cognitive_load": result.cognitive_load_score,
            "temporal_patterns": result.temporal_patterns_score,
            "code_hygiene": result.code_hygiene_score,
            "problem_solving": result.problem_solving_score,
            "engineering_maturity": result.engineering_maturity_score,
        }

        for dim_name, dim_weight in self.DIMENSIONS.items():
            score = dimension_scores.get(dim_name, 0.0)
            total_weighted += score * dim_weight.weight
            total_weight += dim_weight.weight

        if total_weight == 0:
            return 0.0

        overall = total_weighted / total_weight

        # Bonus for high consistency across dimensions
        scores = list(dimension_scores.values())
        if len(scores) > 1:
            import statistics
            std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
            # High consistency = bonus
            consistency_bonus = max(0, 5 - std_dev)
            overall = min(100, overall + consistency_bonus)

        return round(overall, 1)

    def get_score_breakdown(self, signals: Dict[str, float]) -> Dict[str, float]:
        """
        Get detailed score breakdown by dimension.

        Args:
            signals: All extracted signals

        Returns:
            Dictionary of dimension -> score
        """
        breakdown = {}
        for dim_name in self.DIMENSIONS.keys():
            breakdown[dim_name] = self.score_dimension(dim_name, signals)

        breakdown["overall"] = sum(
            breakdown[dim] * self.DIMENSIONS[dim].weight
            for dim in breakdown
        )

        return breakdown
