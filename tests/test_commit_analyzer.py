"""
Tests for Commit Intelligence Engine (Module 2)
==============================================
"""

import pytest
from datetime import datetime
from typing import Any, Dict, List

from modules.commit_analyzer import analyze_commits, CommitIntelligenceEngine
from modules.commit_analyzer.analyzers.cognitive import CognitiveAnalyzer
from modules.commit_analyzer.analyzers.temporal import TemporalAnalyzer
from modules.commit_analyzer.analyzers.hygiene import HygieneAnalyzer
from modules.commit_analyzer.analyzers.problem_solving import ProblemSolvingAnalyzer
from modules.commit_analyzer.analyzers.maturity import MaturityAnalyzer
from modules.commit_analyzer.scoring import CommitScorer
from modules.commit_analyzer.profiles import ProfileClassifier


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_commits() -> List[Dict[str, Any]]:
    """Generate sample commit data for testing."""
    return [
        {
            "sha": f"abc123{i}",
            "message": f"feat: Add feature {i}",
            "message_full": f"feat: Add feature {i}\n\nThis is a test feature",
            "date": f"2024-01-{10+i:02d}T10:30:00Z",
            "author_date": f"2024-01-{10+i:02d}T10:30:00Z",
            "author_name": "Test User",
            "author_email": "test@example.com",
            "verified": i % 2 == 0,
            "num_parents": 1,
            "is_merge": False,
            "commit_type": "feat",
            "hour_of_day": 10,
            "day_of_week": i % 7,
            "year_month": "2024-01",
            "files": [
                {
                    "filename": f"src/module_{j}.py",
                    "additions": 20 + j * 5,
                    "deletions": 5 + j * 2,
                    "status": "modified",
                }
                for j in range(3)
            ],
            "repo_name": "test/repo",
        }
        for i in range(10)
    ]


@pytest.fixture
def multi_module_commits() -> List[Dict[str, Any]]:
    """Generate commits touching multiple modules."""
    return [
        {
            "sha": "multi123",
            "message": "refactor: Cross-module refactoring",
            "message_full": "refactor: Cross-module refactoring",
            "date": "2024-01-15T14:00:00Z",
            "author_date": "2024-01-15T14:00:00Z",
            "author_name": "Test User",
            "verified": True,
            "num_parents": 1,
            "is_merge": False,
            "commit_type": "refactor",
            "hour_of_day": 14,
            "day_of_week": 1,
            "year_month": "2024-01",
            "files": [
                {"filename": "frontend/components/Button.tsx", "additions": 50, "deletions": 30, "status": "modified"},
                {"filename": "backend/api/handler.py", "additions": 40, "deletions": 20, "status": "modified"},
                {"filename": "infra/terraform/main.tf", "additions": 30, "deletions": 10, "status": "modified"},
                {"filename": "data/ml/model.py", "additions": 60, "deletions": 40, "status": "modified"},
            ],
            "repo_name": "test/multi-repo",
        }
    ]


@pytest.fixture
def bug_fix_commits() -> List[Dict[str, Any]]:
    """Generate commits with bug fixes."""
    return [
        {
            "sha": f"fix123{i}",
            "message": f"fix: Resolve issue #{i}",
            "message_full": f"fix: Resolve issue #{i}\n\nThis fixes a bug",
            "date": f"2024-01-{15+i:02d}T22:00:00Z",
            "author_date": f"2024-01-{15+i:02d}T22:00:00Z",
            "author_name": "Test User",
            "verified": True,
            "num_parents": 1,
            "is_merge": False,
            "commit_type": "fix",
            "hour_of_day": 22,
            "day_of_week": 5,  # Saturday
            "year_month": "2024-01",
            "files": [
                {"filename": f"src/bug_{i}.py", "additions": 10, "deletions": 5, "status": "modified"},
            ],
            "repo_name": "test/repo",
        }
        for i in range(5)
    ]


@pytest.fixture
def empty_commits() -> List[Dict[str, Any]]:
    """Empty commit list for edge case testing."""
    return []


# =============================================================================
# Cognitive Analyzer Tests
# =============================================================================

class TestCognitiveAnalyzer:
    """Tests for CognitiveAnalyzer."""

    def test_analyze_basic(self, sample_commits):
        """Test basic analysis of commits."""
        analyzer = CognitiveAnalyzer()
        signals = analyzer.analyze(sample_commits)

        assert "files_per_commit_mean" in signals
        assert "files_per_commit_median" in signals
        assert "architectural_complexity_score" in signals
        assert signals["files_per_commit_mean"] == 3.0

    def test_analyze_empty(self, empty_commits):
        """Test analysis with empty commits."""
        analyzer = CognitiveAnalyzer()
        signals = analyzer.analyze(empty_commits)

        assert signals["files_per_commit_mean"] == 0.0
        assert signals["architectural_complexity_score"] == 0.0

    def test_multi_module_detection(self, multi_module_commits):
        """Test detection of multi-module commits."""
        analyzer = CognitiveAnalyzer()
        signals = analyzer.analyze(multi_module_commits)

        assert signals["files_per_commit_mean"] == 4.0
        assert signals["multi_module_commit_ratio"] == 1.0
        assert signals["cross_boundary_commit_ratio"] > 0

    def test_extract_directories(self):
        """Test directory extraction from file paths."""
        analyzer = CognitiveAnalyzer()
        files = [
            {"filename": "frontend/components/Button.tsx"},
            {"filename": "backend/api/handler.py"},
            {"filename": "README.md"},
        ]
        dirs = analyzer._extract_directories(files)
        assert "frontend" in dirs
        assert "backend" in dirs
        assert "root" in dirs  # Single file goes to root


# =============================================================================
# Temporal Analyzer Tests
# =============================================================================

class TestTemporalAnalyzer:
    """Tests for TemporalAnalyzer."""

    def test_analyze_basic(self, sample_commits):
        """Test basic temporal analysis."""
        analyzer = TemporalAnalyzer()
        signals = analyzer.analyze(sample_commits)

        assert "business_hours_ratio" in signals
        assert "weekend_commit_ratio" in signals
        assert "consistency_score" in signals
        assert "late_night_commit_ratio" in signals

    def test_analyze_empty(self, empty_commits):
        """Test analysis with empty commits."""
        analyzer = TemporalAnalyzer()
        signals = analyzer.analyze(empty_commits)

        assert signals["weekend_commit_ratio"] == 0.0
        assert signals["consistency_score"] == 0.0

    def test_night_owl_detection(self, bug_fix_commits):
        """Test detection of night owl patterns."""
        analyzer = TemporalAnalyzer()
        signals = analyzer.analyze(bug_fix_commits)

        # Hour 22 is night owl (21-24), not late night (0-5)
        assert signals["night_owl_ratio"] == 1.0
        assert signals["weekend_commit_ratio"] == 1.0

    def test_burst_score_calculation(self):
        """Test velocity burst score calculation."""
        analyzer = TemporalAnalyzer()

        # High variance daily counts
        daily_counts = {
            "2024-01-01": 10,
            "2024-01-02": 1,
            "2024-01-03": 12,
            "2024-01-04": 2,
        }
        burst = analyzer._compute_burst_score(daily_counts)
        assert burst > 40  # Should detect some bursts


# =============================================================================
# Hygiene Analyzer Tests
# =============================================================================

class TestHygieneAnalyzer:
    """Tests for HygieneAnalyzer."""

    def test_analyze_basic(self, sample_commits):
        """Test basic hygiene analysis."""
        analyzer = HygieneAnalyzer()
        signals = analyzer.analyze(sample_commits)

        assert "verified_commit_ratio" in signals
        assert "conventional_commit_ratio" in signals
        assert "issue_reference_ratio" in signals
        assert "overall_hygiene_score" in signals

    def test_verified_commit_detection(self, sample_commits):
        """Test verified commit detection."""
        analyzer = HygieneAnalyzer()
        signals = analyzer.analyze(sample_commits)

        # Half the commits are verified
        assert signals["verified_commit_ratio"] == 0.5

    def test_conventional_commit_detection(self, sample_commits):
        """Test conventional commit pattern detection."""
        analyzer = HygieneAnalyzer()
        signals = analyzer.analyze(sample_commits)

        # All commits follow conventional format
        assert signals["conventional_commit_ratio"] == 1.0

    def test_revert_detection(self):
        """Test revert commit detection."""
        analyzer = HygieneAnalyzer()
        commits = [
            {"message": "revert: Undo feature", "num_parents": 1},
            {"message": "Merge branch 'main'", "num_parents": 2},
            {"message": "normal commit", "num_parents": 1},
        ]
        signals = analyzer.analyze(commits)

        assert signals["revert_ratio"] >= 0.33  # At least one revert


# =============================================================================
# Problem Solving Analyzer Tests
# =============================================================================

class TestProblemSolvingAnalyzer:
    """Tests for ProblemSolvingAnalyzer."""

    def test_analyze_basic(self, sample_commits):
        """Test basic problem solving analysis."""
        analyzer = ProblemSolvingAnalyzer()
        signals = analyzer.analyze(sample_commits)

        assert "refactor_ratio" in signals
        assert "fix_ratio" in signals
        assert "feat_ratio" in signals
        assert "avg_churn_ratio" in signals
        assert "problem_solving_score" in signals

    def test_commit_type_detection(self, sample_commits, bug_fix_commits):
        """Test commit type detection."""
        analyzer = ProblemSolvingAnalyzer()

        # All sample commits are features
        signals = analyzer.analyze(sample_commits)
        assert signals["feat_ratio"] == 1.0

        # All bug fix commits are fixes
        signals = analyzer.analyze(bug_fix_commits)
        assert signals["fix_ratio"] == 1.0

    def test_test_file_detection(self):
        """Test test file detection."""
        analyzer = ProblemSolvingAnalyzer()
        assert analyzer._is_test_file("tests/test_main.py") == True
        assert analyzer._is_test_file("src/components/__tests__/Button.spec.tsx") == True
        assert analyzer._is_test_file("src/main.py") == False
        assert analyzer._is_test_file("") == False

    def test_empty_analysis(self, empty_commits):
        """Test analysis with empty commits."""
        analyzer = ProblemSolvingAnalyzer()
        signals = analyzer.analyze(empty_commits)

        assert signals["fix_ratio"] == 0.0
        assert signals["problem_solving_score"] == 0.0


# =============================================================================
# Maturity Analyzer Tests
# =============================================================================

class TestMaturityAnalyzer:
    """Tests for MaturityAnalyzer."""

    def test_analyze_basic(self, sample_commits):
        """Test basic maturity analysis."""
        analyzer = MaturityAnalyzer()
        signals = analyzer.analyze(sample_commits)

        assert "avg_commit_size" in signals
        assert "large_commit_ratio" in signals
        assert "commit_consistency_score" in signals
        assert "merge_commit_ratio" in signals

    def test_commit_size_analysis(self, sample_commits):
        """Test commit size analysis."""
        analyzer = MaturityAnalyzer()
        signals = analyzer.analyze(sample_commits)

        # Each commit has 3 files with additions of 20, 25, 30 = 75 total
        assert signals["avg_commit_size"] > 0

    def test_empty_analysis(self, empty_commits):
        """Test analysis with empty commits."""
        analyzer = MaturityAnalyzer()
        signals = analyzer.analyze(empty_commits)

        assert signals["avg_commit_size"] == 0.0
        assert signals["commit_consistency_score"] == 0.0


# =============================================================================
# Scoring Tests
# =============================================================================

class TestCommitScorer:
    """Tests for CommitScorer."""

    def test_score_dimension(self):
        """Test dimension scoring."""
        scorer = CommitScorer()
        signals = {
            "architectural_complexity_score": 80.0,
            "files_per_commit_mean": 5.0,
            "multi_module_commit_ratio": 0.5,
            "cross_boundary_commit_ratio": 0.2,
            "files_per_commit_std": 2.0,
        }

        score = scorer.score_dimension("cognitive_load", signals)
        assert 0 <= score <= 100

    def test_normalize_signal(self):
        """Test signal normalization."""
        scorer = CommitScorer()

        # Test ratio normalization
        normalized = scorer._normalize_signal("test_coverage_ratio", 0.5)
        assert normalized == 50.0

        # Test already normalized
        normalized = scorer._normalize_signal("consistency_score", 75)
        assert normalized == 75.0

    def test_inverted_signals(self):
        """Test inverted signal handling."""
        scorer = CommitScorer()

        # velocity_burst_score is inverted (lower is better)
        normalized = scorer._normalize_signal("velocity_burst_score", 20)
        assert normalized == 80.0  # 100 - 20


# =============================================================================
# Profile Classifier Tests
# =============================================================================

class TestProfileClassifier:
    """Tests for ProfileClassifier."""

    def test_classify_architect(self):
        """Test architect profile classification."""
        classifier = ProfileClassifier()
        signals = {
            "architectural_complexity_score": 75.0,
            "cross_boundary_commit_ratio": 0.15,
            "multi_module_commit_ratio": 0.4,
        }

        profile = classifier._calculate_archetype_score(
            classifier.ARCHETYPES["architect"],
            signals
        )
        assert profile >= 0.6  # Should match architect profile

    def test_classify_bug_hunter(self):
        """Test bug hunter profile classification."""
        classifier = ProfileClassifier()
        signals = {
            "fix_ratio": 0.3,
            "avg_fix_files": 2,
            "test_coverage_ratio": 0.4,
        }

        profile = classifier._calculate_archetype_score(
            classifier.ARCHETYPES["bug_hunter"],
            signals
        )
        assert profile >= 0.6  # Should match bug hunter profile

    def test_check_match_operators(self):
        """Test match operator handling."""
        classifier = ProfileClassifier()

        assert classifier._check_match(10, 5, ">") == True
        assert classifier._check_match(3, 5, "<") == True
        assert classifier._check_match(5, 5, ">=") == True
        assert classifier._check_match(1.0, 1.0, "~") == True  # Near match


# =============================================================================
# Integration Tests
# =============================================================================

class TestCommitIntelligenceEngine:
    """Integration tests for the full engine."""

    def test_full_analysis(self, sample_commits):
        """Test full analysis pipeline."""
        engine = CommitIntelligenceEngine()
        result = engine.analyze(sample_commits)

        assert result.commit_intelligence_score > 0
        assert result.commits_analyzed == 10
        assert len(result.signals) > 30  # Should have 30+ signals
        assert result.profile is not None

    def test_empty_commits(self, empty_commits):
        """Test analysis with empty commits."""
        engine = CommitIntelligenceEngine()
        result = engine.analyze(empty_commits)

        assert result.commit_intelligence_score == 0.0
        assert result.commits_analyzed == 0

    def test_multi_module_analysis(self, multi_module_commits):
        """Test analysis of cross-module commits."""
        engine = CommitIntelligenceEngine()
        result = engine.analyze(multi_module_commits)

        assert result.cognitive_load_score > 50
        assert result.profile is not None

    def test_analyze_commits_function(self, sample_commits):
        """Test the convenience function."""
        result = analyze_commits(sample_commits)

        assert "commit_intelligence_score" in result
        assert "dimensions" in result
        assert "signals" in result
        assert "profile" in result

    def test_result_serialization(self, sample_commits):
        """Test result serialization to dict."""
        engine = CommitIntelligenceEngine()
        result = engine.analyze(sample_commits)
        result_dict = result.to_dict()

        assert "commit_intelligence_score" in result_dict
        assert "dimensions" in result_dict
        assert "signals" in result_dict
        assert isinstance(result_dict["signals"], dict)


# =============================================================================
# Signal Count Tests
# =============================================================================

class TestSignalCounts:
    """Test that we have the expected number of signals."""

    def test_total_signal_count(self, sample_commits):
        """Verify we have 30+ signals across all dimensions."""
        engine = CommitIntelligenceEngine()
        result = engine.analyze(sample_commits)

        signal_count = len(result.signals)
        assert signal_count >= 30, f"Expected 30+ signals, got {signal_count}"

    def test_dimension_signal_counts(self):
        """Test signal counts per dimension."""
        cognitive = CognitiveAnalyzer()
        temporal = TemporalAnalyzer()
        hygiene = HygieneAnalyzer()
        problem = ProblemSolvingAnalyzer()
        maturity = MaturityAnalyzer()

        # Cognitive should have ~10 signals
        cognitive_signals = cognitive.analyze([])
        assert len(cognitive_signals) >= 8

        # Temporal should have ~10 signals
        temporal_signals = temporal.analyze([])
        assert len(temporal_signals) >= 10

        # Hygiene should have ~15 signals
        hygiene_signals = hygiene.analyze([])
        assert len(hygiene_signals) >= 15

        # Problem solving should have ~20 signals
        problem_signals = problem.analyze([])
        assert len(problem_signals) >= 15

        # Maturity should have ~20 signals
        maturity_signals = maturity.analyze([])
        assert len(maturity_signals) >= 15
