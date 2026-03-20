"""
Enhanced Commit Intelligence Engine
==================================
JD-driven and LLM-powered commit analysis for recruitment.

Features:
- Parses job descriptions to customize scoring
- Uses LLM for intelligent insights
- Generates role-specific recommendations
- Provides personalized candidate summaries
- Can load data from SQLite database
"""

import logging
import sqlite3
from typing import Any, Dict, List, Optional

from modules.commit_analyzer.engine import CommitIntelligenceEngine
from modules.commit_analyzer.jd_parser import JDParser, JDParsed
from modules.commit_analyzer.llm_client import LLMClient, get_llm_client
from modules.commit_analyzer.scoring import CommitScorer
from modules.commit_analyzer.types import CommitIntelligenceResult
from modules.skill_analyzer import SkillAnalyzer

logger = logging.getLogger(__name__)


class EnhancedIntelligenceEngine:
    """
    Enhanced engine with JD-driven and LLM-powered analysis.

    This engine:
    1. Parses job descriptions to understand requirements
    2. Adjusts scoring weights based on role priorities
    3. Uses LLM for intelligent insights and recommendations
    4. Generates personalized candidate summaries
    5. Can load data from SQLite database
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize enhanced engine.

        Args:
            llm_client: Optional LLM client (will create default if not provided)
        """
        self.base_engine = CommitIntelligenceEngine()
        self.jd_parser = JDParser()
        self.llm = llm_client or get_llm_client()
        self.scorer = CommitScorer()
        self.skill_analyzer = SkillAnalyzer()

    def load_from_database(self, handle: str) -> Dict[str, Any]:
        """
        Load commits and repos from SQLite database.

        Args:
            handle: GitHub handle

        Returns:
            Dict with 'commits' and 'repos' keys
        """
        try:
            from modules.database import get_connection
            import json

            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Load commits from DB
            cursor.execute("""
                SELECT c.*,
                       (SELECT GROUP_CONCAT(json_object(
                           'filename', cf.filename,
                           'additions', cf.additions,
                           'deletions', cf.deletions,
                           'patch', cf.patch,
                           'status', cf.status,
                           'file_extension', cf.file_extension,
                           'is_test', cf.is_test,
                           'is_docs', cf.is_docs
                       ), '|')
                       FROM commit_files cf WHERE cf.commit_sha = c.sha) as files_json
                FROM commits c
                WHERE c.owner_handle = ?
                ORDER BY c.author_date DESC
            """, (handle,))

            commits = []
            for row in cursor.fetchall():
                commit = dict(row)
                # Parse files from JSON
                if commit.get('files_json'):
                    files = []
                    for file_json in commit['files_json'].split('|'):
                        if file_json:
                            try:
                                files.append(json.loads(file_json))
                            except json.JSONDecodeError:
                                pass
                    commit['files'] = files
                else:
                    commit['files'] = []
                commits.append(commit)

            # Load repos from DB
            cursor.execute("""
                SELECT * FROM repositories WHERE owner_handle = ?
            """, (handle,))
            repos = [dict(row) for row in cursor.fetchall()]

            conn.close()

            return {'commits': commits, 'repos': repos}

        except Exception as e:
            logger.warning(f"Could not load from database: {e}")
            return {'commits': [], 'repos': []}

    def analyze(
        self,
        commits: List[Dict[str, Any]],
        repos: List[Dict[str, Any]] = None,
        jd_text: Optional[str] = None,
        jd_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze commits with optional JD customization and LLM insights.

        Args:
            commits: List of commit dictionaries
            repos: Optional list of repo dictionaries
            jd_text: Optional job description text
            jd_file: Optional path to JD file

        Returns:
            Complete analysis result with JD fit and LLM insights
        """
        # Parse JD if provided
        jd_parsed = None
        if jd_text:
            jd_parsed = self.jd_parser.parse(jd_text)
        elif jd_file:
            jd_parsed = self.jd_parser.parse_from_file(jd_file)

        # Run base analysis
        result = self.base_engine.analyze(commits, repos)
        result_dict = result.to_dict()

        # Run skill intelligence analysis
        if repos:
            logger.info("Running skill intelligence analysis")
            skill_raw_data = {
                "repos": repos,
                "lang_bytes": {},  # Would need to be populated from repo data
            }
            skill_result = self.skill_analyzer.analyze(
                skill_raw_data,
                jd_requirements=jd_parsed.requirements if jd_parsed else None
            )
            result_dict["skill_intelligence"] = {
                "skill_level": skill_result.skill_profile.skill_level,
                "skill_level_confidence": skill_result.skill_profile.skill_level_confidence,
                "primary_domains": skill_result.skill_profile.primary_domains,
                "secondary_domains": skill_result.skill_profile.secondary_domains,
                "depth_index": skill_result.skill_profile.depth_index.__dict__,
                "modernity_score": skill_result.skill_profile.modernity_score.overall_score,
                "framework_count": len(skill_result.frameworks),
                "infrastructure_tools": skill_result.infrastructure[:5],
                "top_repos_by_impact": [
                    {"name": r["name"], "impact_score": r.get("impact", {}).get("impact_score", 0)}
                    for r in skill_result.top_repos[:3]
                ],
                "insights": skill_result.insights,
                "jd_fit": skill_result.jd_fit,
            }

        # Add JD analysis if available
        if jd_parsed:
            result_dict["jd_analysis"] = jd_parsed.to_dict()

            # Adjust scores based on JD
            result_dict = self._adjust_scores_for_jd(result_dict, jd_parsed)

            # Calculate JD fit
            if self.llm.is_available():
                jd_fit = self.llm.analyze_jd_fit(
                    result_dict["signals"],
                    result.profile,
                    jd_parsed.requirements
                )
                if jd_fit:
                    result_dict["jd_fit"] = jd_fit

        # Add LLM insights if available
        if self.llm.is_available():
            # Commit context analysis
            commit_context = self.llm.analyze_commit_context(commits)
            if commit_context:
                result_dict["llm_commit_analysis"] = commit_context

            # Personalized insights
            if result.profile:
                insights = self.llm.generate_personalized_insights(
                    result_dict["signals"],
                    result.profile,
                    jd_parsed.inferred_role_type if jd_parsed else "generalist"
                )
                if insights:
                    result_dict["llm_insights"] = insights

            # Developer summary
            summary = self.llm.generate_developer_summary(
                result_dict["signals"],
                result.profile,
                result_dict.get("citations", []),
                result_dict.get("metadata", {})
            )
            if summary:
                result_dict["llm_summary"] = summary

        return result_dict

    def _adjust_scores_for_jd(
        self,
        result: Dict[str, Any],
        jd_parsed: JDParsed
    ) -> Dict[str, Any]:
        """
        Adjust scores based on JD priorities.

        Args:
            result: Base analysis result
            jd_parsed: Parsed JD

        Returns:
            Adjusted result with modified scores
        """
        # Use JD weights
        weights = jd_parsed.weights

        # Recalculate overall score with JD-adjusted weights
        dimensions = result.get("dimensions", {})

        adjusted_score = (
            dimensions.get("cognitive_load", 0) * weights.cognitive_load +
            dimensions.get("temporal_patterns", 0) * weights.temporal_patterns +
            dimensions.get("code_hygiene", 0) * weights.code_hygiene +
            dimensions.get("problem_solving", 0) * weights.problem_solving +
            dimensions.get("engineering_maturity", 0) * weights.engineering_maturity
        )

        result["jd_adjusted_score"] = round(adjusted_score, 1)
        result["original_score"] = result.get("commit_intelligence_score", 0)
        result["commit_intelligence_score"] = round(adjusted_score, 1)

        # Add role-specific signal highlighting
        if jd_parsed.emphasized_signals:
            signals = result.get("signals", {})
            result["emphasized_signal_values"] = {
                sig: signals.get(sig, 0)
                for sig in jd_parsed.emphasized_signals
                if sig in signals
            }

        # Check minimum thresholds
        if jd_parsed.minimum_thresholds:
            result["threshold_checks"] = self._check_thresholds(
                result.get("signals", {}),
                jd_parsed.minimum_thresholds
            )

        return result

    def _check_thresholds(
        self,
        signals: Dict[str, float],
        thresholds: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """Check if signals meet minimum thresholds."""
        checks = {}

        for threshold_name, min_value in thresholds.items():
            actual_value = signals.get(threshold_name, 0)
            passed = actual_value >= min_value

            checks[threshold_name] = {
                "required": min_value,
                "actual": actual_value,
                "passed": passed,
                "status": "pass" if passed else "fail"
            }

        return checks

    def analyze_with_jd(self, jd_path: str, commits_path: str) -> Dict[str, Any]:
        """
        Convenience method to analyze with JD from files.

        Args:
            jd_path: Path to JD file
            commits_path: Path to commits JSON file

        Returns:
            Complete analysis
        """
        import json

        # Load data
        with open(commits_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        commits = data.get("commits", [])
        repos = data.get("repos", [])

        return self.analyze(commits, repos, jd_file=jd_path)


def analyze_with_jd(
    commits: List[Dict[str, Any]],
    repos: List[Dict[str, Any]],
    jd_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for JD-driven analysis.

    Args:
        commits: List of commit dicts
        repos: List of repo dicts
        jd_text: Job description text

    Returns:
        Analysis result with JD customization
    """
    engine = EnhancedIntelligenceEngine()
    return engine.analyze(commits, repos, jd_text=jd_text)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Enhanced Commit Intelligence Analysis")
    parser.add_argument("handle", help="GitHub handle")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument("--jd-file", help="Path to job description file")
    parser.add_argument("--jd-text", help="Job description text")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    # Load commits
    data_file = f"{args.data_dir}/{args.handle}_raw.json"
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        commits = data.get("commits", [])
        repos = data.get("repos", [])
    except FileNotFoundError:
        print(f"Error: Data file not found: {data_file}")
        sys.exit(1)

    # Analyze
    print(f"Analyzing {len(commits)} commits...")
    engine = EnhancedIntelligenceEngine()
    result = engine.analyze(commits, repos, jd_text=args.jd_text, jd_file=args.jd_file)

    # Output
    output_file = args.output or f"{args.data_dir}/{args.handle}_enhanced_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")
    print(f"Commit Intelligence Score: {result['commit_intelligence_score']}/100")

    if result.get("jd_adjusted_score"):
        print(f"JD-Adjusted Score: {result['jd_adjusted_score']}/100")

    if result.get("llm_summary"):
        print(f"\nLLM Summary:\n{result['llm_summary']}")
