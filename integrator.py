"""
Talent Intelligence Integrator
==============================
Core bridge that connects EightFold's deep behavioral signals to the
Talent Intelligence adaptive scoring engine.

Flow:
  1. Harvest GitHub data (deep: 13 fetchers, commits, PRs, issues, deps)
  2. Run EightFold analyzers (skill, commit, dependency intelligence)
  3. Normalize outputs → scoring engine format
  4. Run AdaptiveScoringEngine with deep signals
  5. Cross-validate resume claims (if PDF resume provided)
  6. Return unified result with explainability

Author: Techkriti '26 x EightFold AI
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load .env file for API keys and tokens
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import (
    harvest,
    compute_all_aggregates,
    SkillAnalyzer,
    CommitIntelligenceEngine,
    build_candidate_profile,
    ExplainabilityEngine,
    explain_skill_intelligence,
    CodeforcesAnalyzer,
    get_problem_solving_score,
    get_tier_description,
    map_cf_topics_to_job_skills,
)
from modules.commit_analyzer import analyze_commits
from modules.codeforces import FlagDetector
from src import (
    AdaptiveScoringEngine,
    CrossValidator,
    generate_synthetic_profile,
    AdvancedResumeParser,
)
from src.evidence_builder import EvidenceBuilder

# ─── Database helpers ────────────────────────────────────────────────────────

DB_PATH = Path("data/github_signals.db")


def _db_exists(handle: str) -> bool:
    """Check if a user's data is already in the local SQLite DB."""
    if not DB_PATH.exists():
        return False
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE github_handle = ?", (handle,))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except Exception:
        return False


def _load_from_db(handle: str) -> Dict[str, Any]:
    """
    Load all cached GitHub data for a handle from the SQLite DB.
    Reconstructs the raw_data dict that the analyzers expect.
    """
    if not DB_PATH.exists():
        return {}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    def safe_query(table: str, query: str, params=()) -> list:
        """Query a table only if it exists, return empty list otherwise."""
        try:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone() is None:
                return []
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    # ── User ──────────────────────────────────────────────────────────────────
    cursor.execute("SELECT * FROM users WHERE github_handle = ?", (handle,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return {}

    user = dict(user_row)

    # ── Repos ────────────────────────────────────────────────────────────────
    repos = []
    for row in safe_query("repositories", "SELECT * FROM repositories WHERE owner_handle = ?", (handle,)):
        # Parse topics JSON
        if row.get("topics") and isinstance(row["topics"], str):
            try:
                row["topics"] = json.loads(row["topics"])
            except Exception:
                row["topics"] = []
        repos.append(row)

    # ── Commits ─────────────────────────────────────────────────────────────
    commits = safe_query(
        "commits",
        "SELECT * FROM commits WHERE owner_handle = ? ORDER BY author_date DESC LIMIT 2000",
        (handle,)
    )

    # ── Commit files ────────────────────────────────────────────────────────
    commit_files = safe_query(
        "commit_files",
        """SELECT cf.* FROM commit_files cf
           JOIN commits c ON cf.commit_sha = c.sha
           WHERE c.owner_handle = ? LIMIT 5000""",
        (handle,)
    )

    # ── Languages ────────────────────────────────────────────────────────────
    lang_rows = safe_query("languages", "SELECT * FROM languages WHERE owner_handle = ?", (handle,))
    lang_bytes = {}
    for row in lang_rows:
        try:
            langs = json.loads(row["languages"])
            lang_bytes.update(langs)
        except Exception:
            pass

    # ── Pull requests ────────────────────────────────────────────────────────
    pull_requests = safe_query("pull_requests", "SELECT * FROM pull_requests WHERE owner_handle = ?", (handle,))

    # ── Issues ───────────────────────────────────────────────────────────────
    issues = safe_query("issues", "SELECT * FROM issues WHERE owner_handle = ?", (handle,))
    # Normalize: DB uses 'comments', aggregates expect 'num_comments'
    for issue in issues:
        if "num_comments" not in issue:
            issue["num_comments"] = issue.get("comments", 0)

    # ── PR Reviews ──────────────────────────────────────────────────────────
    pr_reviews = safe_query("pr_reviews", "SELECT * FROM pr_reviews WHERE owner_handle = ?", (handle,))

    # ── Issue comments ────────────────────────────────────────────────────────
    issue_comments = safe_query("issue_comments", "SELECT * FROM issue_comments WHERE owner_handle = ?", (handle,))

    # ── Organizations ────────────────────────────────────────────────────────
    orgs = safe_query("organizations", "SELECT * FROM organizations WHERE owner_handle = ?", (handle,))

    # ── Events ───────────────────────────────────────────────────────────────
    events = safe_query("events", "SELECT * FROM events WHERE owner_handle = ?", (handle,))

    # ── Branches ─────────────────────────────────────────────────────────────
    branches_raw = safe_query("branches", "SELECT * FROM branches WHERE owner_handle = ?", (handle,))
    branches = {}
    for b in branches_raw:
        repo = b.get("repo_name", "")
        if repo not in branches:
            branches[repo] = []
        branches[repo].append(b)

    # ── Releases ─────────────────────────────────────────────────────────────
    releases_raw = safe_query("releases", "SELECT * FROM releases WHERE owner_handle = ?", (handle,))
    releases = {}
    for rel in releases_raw:
        repo = rel.get("repo_name", "")
        if repo not in releases:
            releases[repo] = []
        releases[repo].append(rel)

    # ── Dependency files ─────────────────────────────────────────────────────
    dep_files = safe_query("dependency_files", "SELECT * FROM dependency_files WHERE owner_handle = ?", (handle,))

    # ── Starred repos ────────────────────────────────────────────────────────
    starred_repos = safe_query("starred_repos", "SELECT * FROM starred_repos WHERE owner_handle = ?", (handle,))

    conn.close()

    # Build the raw_data dict matching what harvest() returns
    return {
        "user": user,
        "repos": repos,
        "commits": commits,
        "commit_files": commit_files,
        "lang_bytes": lang_bytes,
        "pull_requests": pull_requests,
        "issues": issues,
        "pr_reviews": pr_reviews,
        "issue_comments": issue_comments,
        "orgs": orgs,
        "events": events,
        "branches": branches,
        "releases": releases,
        "dep_files": dep_files,
        "starred_repos": starred_repos,
    }

logger = logging.getLogger(__name__)


class TalentIntelligenceIntegrator:
    """
    Unified integration bridge between EightFold's deep harvesters
    and the adaptive scoring engine from Talent Intelligence.

    This is the main entry point for the unified hackathon submission.

    Data loading priority:
      1. Local SQLite DB (fast, no API calls)
      2. GitHub API (live data, rate-limited)
      3. Synthetic profiles (demo fallback)
    """

    def __init__(self, github_token: str = None):
        """
        Initialize the integrator.

        Args:
            github_token: GitHub personal access token for API access.
                         If None, will try to read from GITHUB_TOKEN env var.
                         If neither available, uses synthetic profile generation.
        """
        self.token = github_token or os.environ.get("GITHUB_TOKEN")
        self.use_synthetic = not bool(self.token)
        self._db_path = DB_PATH

        if self.use_synthetic:
            logger.info("No GitHub token found — will use synthetic profile generation for demo")
        else:
            os.environ["GITHUB_TOKEN"] = self.token

        # Initialize engines
        self.skill_analyzer = SkillAnalyzer()
        self.commit_engine = CommitIntelligenceEngine()
        self.scoring_engine = AdaptiveScoringEngine()
        self.cross_validator = CrossValidator()
        self.explainer = ExplainabilityEngine()
        self.evidence_builder = EvidenceBuilder()

    def is_in_db(self, github_handle: str) -> bool:
        """Check if a user's data is already cached in the local DB."""
        return _db_exists(github_handle)

    def list_cached_users(self) -> list[str]:
        """List all GitHub handles that have cached data in the DB."""
        if not self._db_path.exists():
            return []
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT github_handle, last_harvested FROM users ORDER BY last_harvested DESC")
            rows = cursor.fetchall()
            conn.close()
            return [{"handle": r[0], "last_harvested": r[1]} for r in rows]
        except Exception:
            return []

    def analyze_candidate(
        self,
        github_handle: str,
        job_description: str,
        resume_pdf_path: str = None,
        use_llm: bool = True,
        skip_harvest: bool = False,
        cached_data: Dict = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a single candidate against a job description.

        Data loading priority:
          1. Local SQLite DB (instant, no API calls) — if already harvested
          2. GitHub API — if token available and not in DB (or force_refresh=True)
          3. Synthetic profile — demo fallback

        Args:
            github_handle: GitHub username to analyze
            job_description: Job description text
            resume_pdf_path: Optional path to PDF resume for cross-validation
            use_llm: Use LLM for JD skill extraction (default True)
            skip_harvest: Skip harvester — use cached_data instead
            cached_data: Pre-harvested data dict (if skip_harvest=True)
            force_refresh: Force re-harvest from GitHub even if DB has data

        Returns:
            Unified result dict containing:
            - adaptive_scoring_result: from AdaptiveScoringEngine
            - commit_intelligence: from CommitIntelligenceEngine
            - skill_intelligence: from SkillAnalyzer
            - cross_validation: from CrossValidator (if resume provided)
            - explainability: from ExplainabilityEngine
            - unified_recommendation: merged hiring recommendation
            - data_source: "db_cache" | "live_api" | "synthetic"
        """
        logger.info(f"Analyzing candidate: {github_handle}")

        # ─── Step 1: Harvest or load GitHub data ─────────────────────────────
        data_source = "unknown"

        if skip_harvest and cached_data:
            raw_data = cached_data
            data_source = "cached"
            logger.info("Using provided cached data")
        elif _db_exists(github_handle) and not force_refresh:
            # ✅ Step 1a: Load from local SQLite DB — instant, no API calls!
            raw_data = _load_from_db(github_handle)
            if raw_data.get("commits") or raw_data.get("repos"):
                data_source = "db_cache"
                logger.info(f"Loaded {len(raw_data.get('commits', []))} commits, "
                           f"{len(raw_data.get('repos', []))} repos from local DB cache")
            else:
                # Empty DB entry, fall through to API
                logger.info("DB entry empty, falling back to API")
                data_source = "unknown"
        elif self.use_synthetic:
            # Generate synthetic profile for demo/testing
            logger.info("Generating synthetic profile (no GitHub token)")
            raw_data = self._generate_synthetic_data(github_handle, job_description)
            data_source = "synthetic"
        else:
            # Deep harvest with all 13 fetchers
            logger.info("Harvesting deep GitHub data (this may take ~30s)")
            raw_data = harvest(github_handle)
            data_source = "live_api"
            logger.info("Harvest complete")

        # ─── Step 2: Run EightFold analyzers ─────────────────────────────────
        # Store raw_data for explainability evidence chains
        self._last_raw_data = raw_data

        # Compute aggregates first
        aggregates = compute_all_aggregates(raw_data)
        raw_data["aggregates"] = aggregates

        # Run skill analyzer
        logger.info("Running skill intelligence analysis")
        skill_result = self.skill_analyzer.analyze(raw_data)
        skill_intel = skill_result.to_dict() if hasattr(skill_result, 'to_dict') else skill_result

        # Run commit intelligence
        logger.info("Running commit intelligence analysis")
        commits = raw_data.get("commits", [])
        repos = raw_data.get("repos", [])
        if commits:
            commit_result = analyze_commits(commits, repos)
        else:
            commit_result = {"commit_intelligence_score": 0, "dimensions": {}, "profile": {}, "citations": []}
        commit_intel = commit_result

        # ─── Step 3: Build normalized profile for scoring engine ──────────────
        normalized_profile = self._normalize_to_scoring_format(raw_data, skill_result, commit_result)

        # ─── Step 4: Build deep signals dict ─────────────────────────────────
        deep_signals = {
            "skill_intelligence": skill_intel,
            "commit_intelligence": commit_intel,
            "aggregates": aggregates,
        }

        # ─── Step 5: Run adaptive scoring engine ──────────────────────────────
        logger.info("Running adaptive scoring engine")
        scoring_result = self.scoring_engine.analyze_and_score(
            normalized_profile,
            job_description,
            use_llm=use_llm,
            deep_signals=deep_signals,
        )

        # ─── Step 6: Cross-validate with resume (if provided) ───────────────
        cross_validation = None
        if resume_pdf_path and os.path.exists(resume_pdf_path):
            logger.info("Cross-validating resume claims against GitHub")
            cross_validation = self._cross_validate_resume(
                resume_pdf_path, normalized_profile
            )

        # ─── Step 7: Generate explainability ─────────────────────────────────
        explainability = self._generate_explainability(
            github_handle, skill_result, commit_result, job_description, scoring_result
        )

        # ─── Step 8: Build unified result ────────────────────────────────────
        unified = {
            # Candidate identity
            "candidate": {
                "github_handle": github_handle,
                "name": raw_data.get("user", {}).get("name") or raw_data.get("name", ""),
                "bio": raw_data.get("user", {}).get("bio", "") or raw_data.get("bio", ""),
                "location": raw_data.get("user", {}).get("location", "") or raw_data.get("location", ""),
                "followers": raw_data.get("user", {}).get("followers", 0),
                "public_repos": raw_data.get("user", {}).get("public_repos", 0) or raw_data.get("metrics", {}).get("total_repos", 0),
                "use_mode": "synthetic" if self.use_synthetic else "live",
                "data_source": data_source,
            },
            # Core scoring result
            "scoring": scoring_result,
            # Deep intelligence from EightFold
            "commit_intelligence": {
                "score": commit_intel.get("commit_intelligence_score", 0),
                "archetype": commit_intel.get("profile", {}).get("archetype", "Unknown") if commit_intel.get("profile") else "Unknown",
                "archetype_tagline": commit_intel.get("profile", {}).get("tagline", "") if commit_intel.get("profile") else "",
                "dimensions": commit_intel.get("dimensions", {}),
                "citations": commit_intel.get("citations", [])[:5],
                "commits_analyzed": commit_intel.get("metadata", {}).get("commits_analyzed", 0),
                "repos_analyzed": commit_intel.get("metadata", {}).get("repos_analyzed", 0),
            },
            "skill_intelligence": {
                "skill_level": skill_intel.get("skill_profile", {}).get("skill_level", "Unknown") if skill_intel.get("skill_profile") else "Unknown",
                "skill_level_confidence": skill_intel.get("skill_profile", {}).get("skill_level_confidence", 0) if skill_intel.get("skill_profile") else 0,
                "primary_domains": skill_intel.get("skill_profile", {}).get("primary_domains", []) if skill_intel.get("skill_profile") else [],
                "depth_category": skill_intel.get("skill_profile", {}).get("depth_index", {}).get("depth_category", "") if skill_intel.get("skill_profile") else "",
                "primary_language": skill_intel.get("language_depth", {}),
                "inferred_skills": self._extract_inferred_skills(skill_intel),
                "project_impact": skill_intel.get("project_impact", []),
            },
            # Cross-validation (resume vs GitHub)
            "cross_validation": cross_validation,
            # Explainability
            "explainability": explainability,
            # Aggregated metrics summary
            "metrics_summary": {
                "total_repos": aggregates.get("total_repos", 0),
                "total_commits": aggregates.get("total_commits", 0),
                "total_prs": aggregates.get("total_prs", 0),
                "total_stars": aggregates.get("total_stars", 0),
                "total_forks": aggregates.get("total_forks", 0),
            },
            # Unified recommendation
            "unified_recommendation": self._build_unified_recommendation(scoring_result, cross_validation, commit_intel),
        }

        logger.info(f"Analysis complete for {github_handle}")
        return unified

    def analyze_multiple_candidates(
        self,
        github_handles: List[str],
        job_description: str,
        resume_pdf_paths: List[str] = None,
        use_llm: bool = True,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple candidates and return ranked results.

        Args:
            github_handles: List of GitHub usernames
            job_description: Job description text
            resume_pdf_paths: Optional list of PDF resume paths (parallel to handles)
            use_llm: Use LLM for JD skill extraction
            force_refresh: Force re-harvest even if data is in DB

        Returns:
            List of unified results, sorted by match_score descending
        """
        results = []
        for i, handle in enumerate(github_handles):
            resume_path = None
            if resume_pdf_paths and i < len(resume_pdf_paths):
                resume_path = resume_pdf_paths[i]

            result = self.analyze_candidate(
                github_handle=handle,
                job_description=job_description,
                resume_pdf_path=resume_path,
                use_llm=use_llm,
                force_refresh=force_refresh,
            )
            results.append(result)

        # Sort by match score
        results.sort(key=lambda x: x["scoring"]["match_score"], reverse=True)

        # Add ranking
        for i, result in enumerate(results):
            result["ranking"] = i + 1

        return results

    def _generate_synthetic_data(self, github_handle: str, job_description: str) -> Dict:
        """
        Generate synthetic GitHub data for demo/testing when no token is available.
        Uses JD text to seed skill-appropriate synthetic profiles.
        """
        from src.jd_extractor import extract_skills_fallback

        # Extract relevant skills from JD to seed the synthetic profile
        try:
            jd_skills = extract_skills_fallback(job_description)
            skill_focus = jd_skills.get("must_have", [])[:7]
            if not skill_focus:
                skill_focus = jd_skills.get("nice_to_have", [])[:7]
            if not skill_focus:
                skill_focus = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL"]
        except Exception:
            skill_focus = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL"]

        synthetic = generate_synthetic_profile(github_handle, skill_focus)

        # Convert to raw_data format expected by analyzers
        return {
            "user": {
                "login": github_handle,
                "name": synthetic.get("name", f"Candidate {github_handle}"),
                "bio": synthetic.get("bio", ""),
                "location": synthetic.get("location", "Remote"),
                "followers": synthetic.get("account_metrics", {}).get("followers", 0),
                "following": synthetic.get("account_metrics", {}).get("following", 0),
                "public_repos": synthetic.get("metrics", {}).get("total_repos", 0),
                "created_at": None,
            },
            "repos": synthetic.get("repositories", []),
            "commits": [],
            "metrics": synthetic.get("metrics", {}),
            "raw_skills_list": synthetic.get("raw_skills_list", []),
            "seniority_indicators": synthetic.get("seniority_indicators", []),
            "name": synthetic.get("name"),
            "bio": synthetic.get("bio"),
            "location": synthetic.get("location"),
            "account_metrics": synthetic.get("account_metrics", {}),
        }

    def _normalize_to_scoring_format(
        self,
        raw_data: Dict,
        skill_result,
        commit_result,
    ) -> Dict:
        """
        Normalize EightFold's deep data into the format expected by AdaptiveScoringEngine.

        AdaptiveScoringEngine expects:
        - username, name
        - raw_skills_list: List[str]
        - repositories: List[Dict] with name, description, language, stars, forks, topics
        - metrics: total_stars, total_forks, avg_stars_per_repo, activity_consistency,
                   recent_activity_count, total_repos
        - seniority_indicators: List[str]
        - account_metrics: account_age_days, followers, following
        """
        repos = raw_data.get("repos", [])

        # Compute metrics from aggregates
        aggregates = raw_data.get("aggregates", {})
        metrics = raw_data.get("metrics", {})

        # Normalize skill list
        skill_list = self._extract_inferred_skills(
            skill_result.to_dict() if hasattr(skill_result, 'to_dict') else skill_result
        )
        if not skill_list:
            skill_list = raw_data.get("raw_skills_list", [])

        # Normalize repos to scoring format
        normalized_repos = []
        for repo in repos[:30]:  # Cap at 30 for scoring
            normalized_repos.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", "") or "",
                "language": repo.get("language", "") or "",
                "stars": repo.get("stars", 0) or repo.get("stargazers_count", 0) or repo.get("watchers_count", 0),
                "forks": repo.get("forks", 0),
                "topics": repo.get("topics", []) or repo.get("tags", []),
            })

        # Build seniority indicators from commit intelligence
        seniority = []
        if commit_result.get("commit_intelligence_score", 0) > 60:
            seniority.append("high_quality_repos")
        if commit_result.get("profile", {}).get("archetype") in ["Architect", "Senior Developer", "Tech Lead"]:
            seniority.append("recognized_projects")

        # Compute activity metrics
        total_stars = sum(r.get("stars", 0) for r in normalized_repos)
        total_forks = sum(r.get("forks", 0) for r in normalized_repos)
        avg_stars = total_stars / len(normalized_repos) if normalized_repos else 0

        return {
            "username": raw_data.get("user", {}).get("login", ""),
            "name": raw_data.get("user", {}).get("name") or raw_data.get("name", ""),
            "raw_skills_list": skill_list,
            "repositories": normalized_repos,
            "metrics": {
                "total_stars": metrics.get("total_stars", 0) or total_stars,
                "total_forks": metrics.get("total_forks", 0) or total_forks,
                "avg_stars_per_repo": round(avg_stars, 2),
                "activity_consistency": metrics.get("activity_consistency", 0.7),
                "recent_activity_count": metrics.get("recent_activity_count", len(normalized_repos)),
                "total_repos": metrics.get("total_repos", len(normalized_repos)),
            },
            "seniority_indicators": seniority or ["community_contributor"],
            "account_metrics": {
                "account_age_days": raw_data.get("account_metrics", {}).get("account_age_days", 365),
                "followers": raw_data.get("user", {}).get("followers", 0),
                "following": raw_data.get("user", {}).get("following", 0),
            },
            "bio": raw_data.get("user", {}).get("bio", ""),
            "location": raw_data.get("user", {}).get("location", ""),
        }

    def _extract_inferred_skills(self, skill_intel: Dict) -> List[str]:
        """Extract a flat list of skills from skill intelligence result."""
        skills = []

        # From language depth
        lang_depth = skill_intel.get("language_depth", {})
        if isinstance(lang_depth, dict):
            skills.extend(lang_depth.keys())

        # From inferred skills
        inferred = skill_intel.get("inferred_skills", [])
        if isinstance(inferred, list):
            for item in inferred:
                if isinstance(item, str):
                    skills.append(item)
                elif isinstance(item, dict):
                    skills.append(item.get("skill", ""))

        # From skill profile
        sp = skill_intel.get("skill_profile", {})
        if isinstance(sp, dict):
            for domain_list in [sp.get("primary_domains", []), sp.get("secondary_domains", [])]:
                if isinstance(domain_list, list):
                    skills.extend(domain_list)

        return list(set(skills))

    def _cross_validate_resume(self, resume_pdf_path: str, github_profile: Dict) -> Optional[Dict]:
        """Cross-validate resume claims against GitHub profile."""
        try:
            parser = AdvancedResumeParser()
            resume_data = parser.parse_resume(resume_pdf_path)
        except Exception as e:
            logger.warning(f"Resume parsing failed: {e}")
            return None

        claimed_skills = resume_data.get("skills", [])
        if not claimed_skills:
            return None

        result = self.cross_validator.cross_validate_resume(
            claimed_skills=claimed_skills,
            github_profile=github_profile,
        )

        return {
            "resume_skills_claimed": claimed_skills,
            "github_profiles_found": resume_data.get("github_profiles", []),
            "linkedin_profiles_found": resume_data.get("linkedin_profiles", []),
            "validation_result": result,
        }

    def _generate_explainability(
        self,
        github_handle: str,
        skill_result,
        commit_result,
        job_description: str,
        scoring_result: Dict,
    ) -> Dict:
        """
        Generate explainability: evidence chains + LLM reasoning + caveats.
        Uses EvidenceBuilder for repo/commit links.
        """
        raw_data = getattr(self, '_last_raw_data', {}) or {}

        try:
            # Get skill_dict
            if hasattr(skill_result, 'to_dict'):
                skill_dict = skill_result.to_dict()
            else:
                skill_dict = skill_result

            # Build evidence chains with EvidenceBuilder
            skill_evidence = self.evidence_builder.build_evidence_chains(
                github_handle, raw_data, skill_dict, scoring_result
            )

            # Try EightFold's explainability engine for additional context
            explain_dict = {}
            try:
                explainable = explain_skill_intelligence(raw_data, skill_dict)
                if hasattr(explainable, 'to_dict'):
                    explain_dict = explainable.to_dict()
            except Exception:
                pass

            # Build summary using LLM if available
            summary = self._build_llm_summary(
                github_handle, scoring_result, skill_evidence, job_description
            )

            return {
                "reasoning_chains": skill_evidence,
                "confidence_score": scoring_result.get("match_score", 0),
                "warnings": [],
                "caveats": explain_dict.get("caveats", []),
                "summary": summary or explain_dict.get("summary", ""),
            }
        except Exception as e:
            logger.warning(f"Explainability generation failed: {e}")
            return {
                "reasoning_chains": [],
                "confidence_score": scoring_result.get("match_score", 0) * 0.8,
                "warnings": [f"Explainability engine error: {str(e)[:100]}"],
            }

    def _build_llm_summary(
        self,
        github_handle: str,
        scoring_result: Dict,
        evidence_chains: List[Dict],
        job_description: str,
    ) -> str:
        """
        Build a human-readable summary using the LLM.
        Falls back to template-based summary if LLM unavailable.
        """
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key or api_key in ("your-codemax-api-key-here", "", "none", "null"):
                raise ValueError("No LLM key")

            import requests
            jd_skills = scoring_result.get("jd_skills_extracted", {})
            matched = scoring_result.get("matched_skills", [])
            missing = scoring_result.get("missing_skills", [])
            score = scoring_result.get("match_score", 0)

            matched_str = ", ".join([m.get("skill", "") if isinstance(m, dict) else str(m) for m in matched]) or "None"
            missing_str = ", ".join([m.get("skill", "") if isinstance(m, dict) else str(m) for m in missing]) or "None"

            prompt = f"""Analyze this candidate for a hiring decision.

GitHub: @{github_handle}
Match Score: {score:.0%}
Matched Skills: {matched_str}
Missing/Gap Skills: {missing_str}
Top Evidence: {', '.join([c['skill'] for c in evidence_chains[:5]])}

JD Snippet: {job_description[:300]}

Provide a 2-sentence hiring recommendation. Format: "HIRE/CONSIDER/MAYBE/PASS: [reason]" """

            resp = requests.post(
                "https://api.codemax.pro/v1/messages",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": os.getenv("OPENAI_MODEL", "claude-opus-4-6"),
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                text_content = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text_content = block.get("text", "").strip()
                        break
                # If no text block, try thinking blocks (they sometimes contain useful info)
                if not text_content:
                    for block in data.get("content", []):
                        if block.get("type") == "thinking":
                            thinking = block.get("thinking", "") or block.get("text", "")
                            if thinking:
                                # Use first 200 chars of thinking as fallback
                                text_content = thinking[:200].strip()
                                break
                if text_content:
                    # Strip markdown code blocks
                    text_content = text_content.strip()
                    if text_content.startswith("```"):
                        lines = text_content.split("\n", 1)
                        if len(lines) > 1:
                            text_content = lines[1]
                        text_content = text_content.strip()
                    if text_content.endswith("```"):
                        text_content = text_content[:-3].strip()
                    return text_content
        except Exception:
            pass

        # Fallback: template summary
        matched = scoring_result.get("matched_skills", [])
        score = scoring_result.get("match_score", 0)
        rec = "CONSIDER" if score >= 0.60 else ("MAYBE" if score >= 0.45 else "PASS")
        top_skills = ", ".join([c["skill"] for c in evidence_chains[:3]])
        matched_count = len([m for m in matched if isinstance(m, dict) and m.get("status") == "matched"])
        return f"{rec}: {matched_count}/{len(matched)} skill(s) matched. Top evidence: {top_skills or 'see reasoning chains'}."



    def _build_unified_recommendation(
        self,
        scoring_result: Dict,
        cross_validation: Optional[Dict],
        commit_intel: Dict,
    ) -> Dict:
        """Build a unified hiring recommendation from all signals."""
        base_score = scoring_result.get("match_score", 0)

        authenticity_boost = 0.0
        if cross_validation and cross_validation.get("validation_result"):
            val_result = cross_validation["validation_result"]
            auth_score = val_result.get("authenticity_score", 0.5)
            authenticity_boost = (auth_score - 0.5) * 0.1

        commit_score = commit_intel.get("score", 0) / 100.0
        commit_boost = 0.05 if commit_score > 0.7 else (-0.05 if commit_score < 0.3 else 0.0)

        final_score = min(max(base_score + authenticity_boost + commit_boost, 0), 1)

        if final_score >= 0.75:
            recommendation, rationale = "STRONG HIRE", "Excellent match with verified skills and strong commit intelligence"
        elif final_score >= 0.60:
            recommendation, rationale = "CONSIDER", "Good match with solid technical depth"
        elif final_score >= 0.45:
            recommendation, rationale = "MAYBE", "Partial match — review gaps and time-to-productivity"
        else:
            recommendation, rationale = "PASS", "Significant skill gaps or low verification confidence"

        if cross_validation and cross_validation.get("validation_result"):
            rating = cross_validation["validation_result"].get("authenticity_rating", "")
            if rating:
                rationale += f". Authenticity rating: {rating}"

        archetype = commit_intel.get("archetype", "")
        if archetype and archetype != "Unknown":
            rationale += f". Developer archetype: {archetype}"

        return {
            "unified_score": round(final_score, 3),
            "recommendation": recommendation,
            "rationale": rationale,
            "confidence": round((base_score + commit_score) / 2, 3),
        }

    def analyze_codeforces(
        self,
        cf_handle: str,
        job_description: str = "",
        jd_skills: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a Codeforces profile for competitive programming verification.

        This runs independently of GitHub analysis and provides:
        - Flag/Cheat detection (HARD FLAG: skipped all problems in contests)
        - Rating tier and color badge
        - Problem difficulty breakdown
        - Topic strengths (DP, graphs, math, etc.)
        - Problem-solving score for scoring engine integration
        - Job-relevant skill mapping

        Args:
            cf_handle: Codeforces username
            job_description: Optional JD text for skill relevance scoring
            jd_skills: Optional list of JD skills for direct comparison

        Returns:
            Codeforces analysis result dict
        """
        logger.info(f"Analyzing Codeforces profile: {cf_handle}")

        try:
            # Run full Codeforces analysis
            cf_analyzer = CodeforcesAnalyzer()
            cf_result = cf_analyzer.analyze(cf_handle)
            cf_dict = cf_result.to_dict()

            # Get flag result
            flag_result = cf_dict.get("flag_result", {}) or {}

            # Map topics to job skills
            cf_topics = cf_dict.get("top_topics", [])
            job_skills = []
            if jd_skills:
                job_skills = jd_skills
            elif job_description:
                from src.jd_extractor import extract_skills_fallback
                try:
                    skills_data = extract_skills_fallback(job_description)
                    job_skills = (
                        skills_data.get("must_have", []) +
                        skills_data.get("nice_to_have", [])
                    )
                except Exception:
                    job_skills = []

            # Get JD relevance
            jd_relevance = {}
            if job_skills:
                from modules.codeforces.skills_mapper import get_jd_relevance as _get_jd_relevance
                jd_relevance = _get_jd_relevance(cf_topics, job_skills)

            # Build Codeforces-specific result
            result = {
                "handle": cf_handle,
                "profile_url": f"https://codeforces.com/profile/{cf_handle}",
                # Flag status
                "is_flagged": flag_result.get("is_flagged", False),
                "flag_type": flag_result.get("flag_type", "none"),
                "flag_score": flag_result.get("flag_score", 0.0),
                "flag_evidence": flag_result.get("evidence", []),
                "cheated_contests": flag_result.get("cheated_contests", []),
                # Rating
                "rating": cf_dict.get("rating", 0),
                "max_rating": cf_dict.get("max_rating", 0),
                "rating_tier": cf_dict.get("rating_tier", "Unrated"),
                "rating_emoji": cf_dict.get("rating_emoji", "⚪"),
                "rank": cf_dict.get("rank", "unrated"),
                "max_rank": cf_dict.get("max_rank", "unrated"),
                # Problems
                "problems_solved": cf_dict.get("problems_solved", 0),
                "difficulty_breakdown": cf_dict.get("difficulty_breakdown", {}),
                # Topics
                "top_topics": cf_topics,
                "topics_detail": cf_dict.get("topics", []),
                # Stats
                "total_submissions": cf_dict.get("total_submissions", 0),
                "accepted_count": cf_dict.get("accepted_count", 0),
                "ac_rate": cf_dict.get("ac_rate", 0.0),
                "contest_count": cf_dict.get("contest_count", 0),
                "languages": cf_dict.get("languages", {}),
                # Scores
                "problem_solving_score": cf_dict.get("problem_solving_score", 0.0),
                # JD relevance
                "jd_relevance": jd_relevance,
                # Description
                "tier_description": get_tier_description(cf_dict.get("rating_tier", "unrated")),
                # Verdict
                "verdict": self._build_cf_verdict(flag_result, cf_dict),
            }

            logger.info(f"Codeforces analysis complete for {cf_handle}: "
                       f"flagged={flag_result.get('is_flagged', False)}, "
                       f"rating={cf_dict.get('max_rating', 0)}, "
                       f"problems={cf_dict.get('problems_solved', 0)}")

            return result

        except ValueError as e:
            logger.warning(f"Codeforces user not found: {cf_handle}")
            return {
                "handle": cf_handle,
                "error": str(e),
                "is_flagged": False,
                "flag_type": "not_found",
                "problem_solving_score": 0.0,
                "verdict": "NOT FOUND: Codeforces user does not exist",
            }
        except Exception as e:
            logger.error(f"Codeforces analysis error for {cf_handle}: {e}")
            return {
                "handle": cf_handle,
                "error": str(e),
                "is_flagged": False,
                "flag_type": "error",
                "problem_solving_score": 0.0,
                "verdict": f"ERROR: {str(e)[:100]}",
            }

    def _build_cf_verdict(self, flag_result: Dict, cf_dict: Dict) -> str:
        """Build a human-readable verdict for Codeforces profile."""
        is_flagged = flag_result.get("is_flagged", False)
        flag_type = flag_result.get("flag_type", "none")
        max_rating = cf_dict.get("max_rating", 0)
        problems = cf_dict.get("problems_solved", 0)
        tier = cf_dict.get("rating_tier", "Unrated")

        if is_flagged:
            if flag_type == "hard":
                return f"🚨 FLAGGED: Skipped all problems in contests. Do NOT rely on Codeforces data."
            elif flag_type == "soft":
                return f"⚠️ SOFT FLAG: High skip rate detected. Use with caution."
            elif flag_type == "low_ac_rate":
                return f"⚠️ SUSPICIOUS: Very low accept rate. Verify skills manually."
            else:
                return f"⚠️ FLAGGED: {flag_type}. Use with caution."

        if max_rating == 0:
            return "⚪ UNRATED: No competitive programming history."

        return f"✅ VERIFIED: {tier} ({max_rating}) — {problems} problems solved. Codeforces skills verified."


# ─── Convenience functions ────────────────────────────────────────────────────

def analyze(
    github_handle: str,
    job_description: str,
    resume_pdf_path: str = None,
    github_token: str = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Quick analysis function — the main public API.

    Args:
        github_handle: GitHub username
        job_description: Job description text
        resume_pdf_path: Optional PDF resume path
        github_token: Optional GitHub token (reads from env if not provided)
        force_refresh: Force re-harvest even if data is in DB

    Returns:
        Unified analysis result
    """
    integrator = TalentIntelligenceIntegrator(github_token=github_token)
    return integrator.analyze_candidate(
        github_handle=github_handle,
        job_description=job_description,
        resume_pdf_path=resume_pdf_path,
        force_refresh=force_refresh,
    )


def analyze_batch(
    github_handles: List[str],
    job_description: str,
    github_token: str = None,
    force_refresh: bool = False,
) -> List[Dict[str, Any]]:
    """
    Batch analysis with automatic ranking.

    Args:
        github_handles: List of GitHub usernames
        job_description: Job description text
        github_token: Optional GitHub token
        force_refresh: Force re-harvest even if data is in DB

    Returns:
        Ranked list of analysis results
    """
    integrator = TalentIntelligenceIntegrator(github_token=github_token)
    return integrator.analyze_multiple_candidates(
        github_handles=github_handles,
        job_description=job_description,
        force_refresh=force_refresh,
    )


def analyze_codeforces(
    cf_handle: str,
    job_description: str = "",
    jd_skills: List[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a Codeforces profile for competitive programming verification.

    Args:
        cf_handle: Codeforces username
        job_description: Optional JD text for skill relevance
        jd_skills: Optional list of JD skills

    Returns:
        Codeforces analysis result dict
    """
    integrator = TalentIntelligenceIntegrator()
    return integrator.analyze_codeforces(cf_handle, job_description, jd_skills)


def analyze_full(
    github_handle: str,
    cf_handle: str,
    job_description: str,
    resume_pdf_path: str = None,
    github_token: str = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Full analysis: GitHub + Codeforces combined.

    Args:
        github_handle: GitHub username
        cf_handle: Codeforces username
        job_description: Job description text
        resume_pdf_path: Optional PDF resume path
        github_token: Optional GitHub token
        force_refresh: Force re-harvest GitHub data

    Returns:
        Combined analysis result with GitHub + Codeforces signals
    """
    integrator = TalentIntelligenceIntegrator(github_token=github_token)

    # Run GitHub analysis
    github_result = integrator.analyze_candidate(
        github_handle=github_handle,
        job_description=job_description,
        resume_pdf_path=resume_pdf_path,
        force_refresh=force_refresh,
    )

    # Run Codeforces analysis
    cf_result = integrator.analyze_codeforces(cf_handle, job_description)

    # Combine results
    github_result["codeforces"] = cf_result

    # Update unified recommendation with CF signal
    cf_score = cf_result.get("problem_solving_score", 0.0)
    cf_flagged = cf_result.get("is_flagged", False)
    unified = github_result.get("unified_recommendation", {})

    if cf_flagged:
        # Penalize heavily if flagged
        unified["rationale"] += " ⚠️ Codeforces flagged."
        unified["unified_score"] = round(unified.get("unified_score", 0) * 0.7, 3)
        unified["recommendation"] = "PASS"
    elif cf_score > 0:
        # Boost if verified good CF profile
        boost = min(cf_score * 0.1, 0.1)
        unified["unified_score"] = round(min(unified.get("unified_score", 0) + boost, 1.0), 3)
        unified["rationale"] += f" ✅ Codeforces verified: {cf_result.get('rating_tier', 'Unrated')}."

    github_result["unified_recommendation"] = unified

    return github_result
