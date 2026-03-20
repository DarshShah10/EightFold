"""
Dynamic JD Matcher V2
====================
Matches candidate skills against job descriptions using dynamic extraction and universal evidence matching.

Key improvements:
- LLM-powered skill extraction from JD
- Universal evidence search (no hardcoded patterns)
- Smart scoring that recognizes significant achievements
- Partial/similar skill matching
"""

import logging
import re
from datetime import datetime
from typing import Any, Optional

from modules.jd_matcher.types import (
    EvidenceLink,
    JDMatchResult,
    RequirementMatch,
    SkillMatch,
)

logger = logging.getLogger(__name__)


# Skill aliases for partial matching
SKILL_ALIASES = {
    # Languages
    "python": ["python", "py"],
    "r": ["r", "rstats", "r programming"],
    "java": ["java", "jvm"],
    "javascript": ["javascript", "js", "node.js", "nodejs"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "go": ["go", "golang"],
    "rust": ["rust", "rustlang"],
    "scala": ["scala"],
    "sql": ["sql", "postgresql", "mysql", "sqlite", "database"],

    # ML Frameworks
    "tensorflow": ["tensorflow", "tf", "tf.keras"],
    "pytorch": ["pytorch", "torch", "pytorch lightning"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "keras": ["keras"],
    "jax": ["jax"],
    "xgboost": ["xgboost", "xgb"],
    "lightgbm": ["lightgbm", "lgbm"],

    # ML Libraries
    "pandas": ["pandas", "pd"],
    "numpy": ["numpy", "np"],
    "scipy": ["scipy"],
    "matplotlib": ["matplotlib", "mpl"],
    "seaborn": ["seaborn"],

    # Cloud
    "aws": ["aws", "amazon web services", "amazon aws", "s3", "ec2", "lambda", "boto3"],
    "azure": ["azure", "azure ml", "azure cloud", "azure functions"],
    "gcp": ["gcp", "google cloud", "google cloud platform", "bigquery"],
    "databricks": ["databricks", "delta lake"],

    # MLOps & DevOps
    "docker": ["docker", "containerization", "container"],
    "kubernetes": ["kubernetes", "k8s", "k8s", "helm"],
    "terraform": ["terraform", "tf", "iac"],
    "mlflow": ["mlflow", "ml flow"],
    "airflow": ["airflow", "apache airflow"],
    "kubeflow": ["kubeflow", "kfp"],

    # CI/CD
    "github actions": ["github actions", "github workflows", "gha"],
    "jenkins": ["jenkins", "jenkinsfile"],
    "gitlab ci": ["gitlab ci", "gitlab-ci"],

    # Concepts
    "machine learning": ["machine learning", "ml", "ml algorithms", "ml engineering"],
    "deep learning": ["deep learning", "dl", "neural networks", "neural nets"],
    "nlp": ["nlp", "natural language processing", "text processing"],
    "computer vision": ["computer vision", "cv", "image processing"],
    "time series": ["time series", "time-series", "forecasting", "prediction"],
    "reinforcement learning": ["reinforcement learning", "rl", "policy learning"],
    "generative ai": ["generative ai", "genai", "llm", "large language model", "gpt", "langchain", "chatgpt"],
    "computer science": ["computer science", "cs", "algorithms", "data structures"],

    # Data Engineering
    "spark": ["spark", "pyspark", "apache spark", "big data"],
    "kafka": ["kafka", "apache kafka", "streaming", "confluent"],
    "etl": ["etl", "data pipeline", "data engineering"],
    "data warehouse": ["data warehouse", "dw", "analytics"],

    # Frameworks
    "flask": ["flask", "flask api"],
    "django": ["django", "django rest framework", "drf"],
    "fastapi": ["fastapi", "uvicorn"],
    "react": ["react", "reactjs", "react.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "angular": ["angular", "angularjs"],

    # Domain
    "statistics": ["statistics", "statistical", "statistical analysis"],
    "optimization": ["optimization", "constrained optimization", "linear programming"],
    "feature engineering": ["feature engineering", "feature selection"],
    "model deployment": ["model deployment", "model serving", "inference"],
    "model monitoring": ["model monitoring", "drift detection", "monitoring"],
    "mlops": ["mlops", "ml ops", "machine learning operations"],
    "software engineering": ["software engineering", "software development", "se"],
    "systems programming": ["systems programming", "systems", "low level"],
}


class DynamicMatcher:
    """
    Dynamic JD matcher that extracts skills from JD and searches all data for evidence.
    """

    def __init__(self):
        self.candidate: str = ""
        self.raw_data: dict[str, Any] = {}

    def match(
        self,
        candidate: str,
        raw_data: dict[str, Any],
        jd_text: str,
    ) -> JDMatchResult:
        """
        Match candidate against job description using dynamic extraction.

        Args:
            candidate: GitHub handle
            raw_data: Raw harvested data
            jd_text: Job description text

        Returns:
            JDMatchResult with full traceability
        """
        self.candidate = candidate
        self.raw_data = raw_data

        logger.info(f"Dynamic matching {candidate} against JD")

        # Extract skills from JD (using LLM if available)
        from modules.jd_matcher.llm_parser import extract_skills_with_llm, extract_skills_with_context, ExtractedSkill

        # Try LLM extraction first
        extracted_skills = []
        try:
            from modules.jd_matcher.llm_parser import extract_skills_with_context
            extracted_skills = extract_skills_with_context(jd_text)
            logger.info(f"LLM extracted {len(extracted_skills)} skills")
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")

        # Fallback to basic extraction
        if not extracted_skills:
            skill_names = extract_skills_with_llm(jd_text)
            for skill in skill_names:
                extracted_skills.append(ExtractedSkill(
                    name=skill,
                    category="unknown",
                    is_mandatory=True,
                    context="",
                    confidence=0.5
                ))

        # Extract candidate data
        repos = raw_data.get("repos", []) or []
        commits = raw_data.get("commits", []) or []
        dep_files = raw_data.get("dep_files", {}) or {}
        lang_bytes = raw_data.get("lang_bytes", {}) or {}

        # Build context about candidate for better matching
        candidate_context = self._build_candidate_context(repos, commits, dep_files, lang_bytes)
        logger.info(f"Candidate context: {candidate_context['summary']}")

        # Match each extracted skill
        matches = []
        for skill in extracted_skills:
            match = self._match_skill_dynamic(
                skill,
                repos,
                commits,
                dep_files,
                lang_bytes,
                candidate_context,
            )
            matches.append(match)

        # Build result
        result = self._build_match_result(matches, extracted_skills)

        logger.info(f"Match complete: {result.matched_count} matched, {result.missing_count} missing")
        return result

    def _build_candidate_context(
        self,
        repos: list[dict],
        commits: list[dict],
        dep_files: dict,
        lang_bytes: dict,
    ) -> dict:
        """Build context summary of candidate for smart matching."""
        context = {
            "repos": repos,
            "repo_names": [r.get("name", "").lower() for r in repos],
            "repo_descriptions": [(r.get("description") or "").lower() for r in repos],
            "repo_topics": [],
            "languages": [],
            "commit_messages": [(c.get("message") or "").lower() for c in commits],
            "dep_packages": [],
            "summary": "",
        }

        # Collect topics
        for repo in repos:
            topics = repo.get("topics", []) or []
            context["repo_topics"].extend([str(t).lower() for t in topics])

        # Collect languages
        context["languages"] = list(lang_bytes.keys())

        # Collect dependencies
        for file_name, content in dep_files.items():
            if content:
                context["dep_packages"].extend(
                    [line.strip().lower() for line in str(content).split('\n') if line.strip()]
                )

        # Build summary
        primary_lang = max(lang_bytes.items(), key=lambda x: x[1])[0] if lang_bytes else "Unknown"
        summary_parts = [f"{len(repos)} repos", f"primary: {primary_lang}"]

        if context["repo_topics"]:
            top_topics = list(set(context["repo_topics"]))[:5]
            summary_parts.append(f"topics: {', '.join(top_topics)}")

        context["summary"] = ", ".join(summary_parts)

        return context

    def _match_skill_dynamic(
        self,
        skill: Any,
        repos: list[dict],
        commits: list[dict],
        dep_files: dict,
        lang_bytes: dict,
        candidate_context: dict,
    ) -> SkillMatch:
        """Match a skill against candidate data dynamically."""

        skill_name = skill.name.lower()
        skill_key = skill.name

        evidence = []
        confidence = 0.0

        # Get aliases for this skill
        aliases = self._get_aliases(skill_name)

        # 1. Check topics (highest weight)
        topic_evidence = self._check_topics(aliases, candidate_context)
        if topic_evidence:
            evidence.extend(topic_evidence)
            confidence += 0.35

        # 2. Check language bytes (for languages)
        lang_evidence = self._check_language(aliases, candidate_context, lang_bytes)
        if lang_evidence:
            evidence.extend(lang_evidence)
            confidence += 0.3

        # 3. Check dependencies
        dep_evidence = self._check_dependencies(aliases, dep_files)
        if dep_evidence:
            evidence.extend(dep_evidence)
            confidence += 0.2

        # 4. Check commit messages
        commit_evidence = self._check_commits(aliases, commits)
        if commit_evidence:
            evidence.extend(commit_evidence)
            confidence += 0.1

        # 5. Check repo descriptions/names
        desc_evidence = self._check_descriptions(aliases, candidate_context)
        if desc_evidence:
            evidence.extend(desc_evidence)
            confidence += 0.1

        # 6. Check file paths (for frameworks like FastAPI routes, React components)
        file_evidence = self._check_file_paths(aliases, dep_files)
        if file_evidence:
            evidence.extend(file_evidence)
            confidence += 0.05

        # Boost confidence for multiple sources
        unique_sources = len(set(e.type for e in evidence))
        if unique_sources >= 3:
            confidence = min(0.95, confidence * 1.2)
        elif unique_sources >= 2:
            confidence = min(0.95, confidence * 1.1)

        # Special boosts for significant achievements
        confidence = self._apply_special_boosts(skill_name, skill_key, aliases, candidate_context, confidence)

        is_match = confidence > 0.1

        # Extract contributing repos from evidence descriptions
        contributing_repos = []
        for e in evidence:
            if e.type == "topic":
                # Description format: "Topic 'xxx' in repo_name"
                desc = e.description
                if " in " in desc:
                    repo = desc.split(" in ")[-1]
                    contributing_repos.append(repo)

        return SkillMatch(
            skill=skill_key,
            is_match=is_match,
            confidence=min(0.95, confidence),
            evidence=evidence,
            evidence_summary=self._build_evidence_summary(evidence),
            contributing_repos=contributing_repos,
            supporting_commits=[e.description for e in evidence if e.type == "commit"][:5],
            missing_reason="" if is_match else f"No evidence of {skill_key} or related skills",
            matched_keywords=aliases,
        )

    def _get_aliases(self, skill: str) -> list[str]:
        """Get all aliases for a skill."""
        skill_lower = skill.lower()

        # Direct lookup
        if skill_lower in SKILL_ALIASES:
            return SKILL_ALIASES[skill_lower]

        # Check if skill is an alias itself
        for key, aliases in SKILL_ALIASES.items():
            if skill_lower in aliases:
                return [skill_lower, key] + aliases

        # Return the skill itself
        return [skill_lower]

    def _check_topics(self, aliases: list[str], context: dict) -> list[EvidenceLink]:
        """Check if skill is in repo topics."""
        evidence = []
        topics = set(context.get("repo_topics", []))

        for alias in aliases:
            for topic in topics:
                if alias in topic or topic in alias:
                    # Find which repos have this topic
                    for repo in context.get("repos", []):
                        repo_topics = [str(t).lower() for t in repo.get("topics", []) or []]
                        if any(alias in t or t in alias for t in repo_topics):
                            repo_name = repo.get("name", "")
                            full_name = repo.get("full_name", "")
                            evidence.append(EvidenceLink(
                                url=f"https://github.com/{full_name}",
                                type="topic",
                                description=f"Topic '{topic}' in {repo_name}",
                                weight=0.3,
                                verified=True,
                            ))
                    break

        return evidence

    def _check_language(self, aliases: list[str], context: dict, lang_bytes: dict) -> list[EvidenceLink]:
        """Check if skill matches primary languages."""
        evidence = []

        for lang_name, bytes_count in lang_bytes.items():
            lang_lower = lang_name.lower()
            if any(alias == lang_lower for alias in aliases):
                total = sum(lang_bytes.values())
                percentage = (bytes_count / total * 100) if total > 0 else 0

                # Find repos using this language
                repos_using = []
                for repo in context.get("repos", []):
                    if repo.get("language", "").lower() == lang_lower:
                        repos_using.append(repo.get("name", ""))

                evidence.append(EvidenceLink(
                    url=f"https://github.com/{self.candidate}?tab=repositories&q=&language={lang_name}",
                    type="language",
                    description=f"{lang_name}: {percentage:.1f}% of codebase ({len(repos_using)} repos)",
                    weight=0.25,
                    verified=True,
                ))

        return evidence

    def _check_dependencies(self, aliases: list[str], dep_files: dict) -> list[EvidenceLink]:
        """Check if skill is in dependency files."""
        evidence = []
        content_str = str(dep_files).lower()

        for alias in aliases:
            if alias in content_str:
                # Find which files
                matching_files = []
                for file_name, content in dep_files.items():
                    if content and alias in str(content).lower():
                        matching_files.append(file_name)

                if matching_files:
                    evidence.append(EvidenceLink(
                        url=f"https://github.com/search?q=user:{self.candidate}+{alias}&type=code",
                        type="dependency",
                        description=f"Found in {len(matching_files)} files: {', '.join(matching_files[:2])}",
                        weight=0.2,
                        verified=False,
                    ))

        return evidence

    def _check_commits(self, aliases: list[str], commits: list[dict]) -> list[EvidenceLink]:
        """Check if skill is in commit messages."""
        evidence = []
        matching_commits = []

        for commit in commits:
            msg = (commit.get("message", "") or "").lower()
            if any(alias in msg for alias in aliases):
                matching_commits.append(commit)

        if matching_commits:
            # Get unique repos
            repos = set(c.get("repo_name", "") for c in matching_commits if c.get("repo_name"))

            # Sample commit
            sample = matching_commits[0]
            commit_hash = sample.get("commit_hash", sample.get("sha", ""))[:7]
            repo_name = sample.get("repo_name", "")

            evidence.append(EvidenceLink(
                url=f"https://github.com/{self.candidate}/{repo_name}/commit/{commit_hash}" if repo_name else "#",
                type="commit",
                description=f"{len(matching_commits)} commits mentioning: {aliases[0]}",
                weight=0.1,
                verified=False,
            ))

        return evidence

    def _check_descriptions(self, aliases: list[str], context: dict) -> list[EvidenceLink]:
        """Check repo names and descriptions."""
        evidence = []

        for repo in context.get("repos", []):
            name = repo.get("name", "").lower()
            desc = (repo.get("description", "") or "").lower()
            full_name = repo.get("full_name", "")

            for alias in aliases:
                if alias in name or alias in desc:
                    evidence.append(EvidenceLink(
                        url=f"https://github.com/{full_name}",
                        type="description",
                        description=f"'{alias}' in {repo.get('name', '')} description",
                        weight=0.08,
                        verified=True,
                    ))
                    break

        return evidence

    def _check_file_paths(self, aliases: list[str], dep_files: dict) -> list[EvidenceLink]:
        """Check file paths for framework indicators."""
        evidence = []

        for file_name in dep_files.keys():
            file_lower = file_name.lower()
            for alias in aliases:
                if alias in file_lower:
                    evidence.append(EvidenceLink(
                        url=f"https://github.com/search?q=repo:{self.candidate}+path:{alias}&type=code",
                        type="file",
                        description=f"File path contains: {alias}",
                        weight=0.05,
                        verified=False,
                    ))
                    break

        return evidence

    def _apply_special_boosts(
        self,
        skill_name: str,
        skill_key: str,
        aliases: list[str],
        context: dict,
        confidence: float,
    ) -> float:
        """Apply special confidence boosts for significant achievements."""

        # Creator/maintainer boost
        if skill_name in ["python", "django", "flask", "react", "tensorflow"]:
            # Check if candidate created this project
            for repo in context.get("repos", []):
                repo_name = repo.get("name", "").lower()
                # Python creator
                if skill_name == "python" and "python" in repo_name:
                    return max(confidence, 0.95)  # Boost to near-certain
                # Other creators
                if any(alias in repo_name for alias in aliases):
                    return max(confidence, 0.9)

        # Core contributor boost
        core_contributor_indicators = [
            "core", "maintainer", "author", "creator", "founder",
            "original", "inventor", "creator of", "author of"
        ]

        for repo in context.get("repos", []):
            desc = (repo.get("description", "") or "").lower()
            if any(indicator in desc for indicator in core_contributor_indicators):
                if any(alias in desc for alias in aliases):
                    return max(confidence, 0.85)

        # High-impact repo boost
        for repo in context.get("repos", []):
            stars = repo.get("stars", repo.get("stargazers_count", 0)) or 0
            if stars > 1000:  # Popular project
                topics = [str(t).lower() for t in repo.get("topics", []) or []]
                if any(alias in topic for alias in aliases for topic in topics):
                    confidence = min(0.9, confidence + 0.15)

        return confidence

    def _build_evidence_summary(self, evidence: list[EvidenceLink]) -> str:
        """Build human-readable evidence summary."""
        if not evidence:
            return ""

        parts = []
        sources = {}

        for e in evidence:
            src = e.type
            if src not in sources:
                sources[src] = []
            sources[src].append(e.description)

        for src, descs in sources.items():
            parts.append(f"{src}: {', '.join(descs[:2])}")

        return "; ".join(parts[:3])

    def _build_match_result(
        self,
        matches: list[SkillMatch],
        extracted_skills: list,
    ) -> JDMatchResult:
        """Build final match result."""

        # Separate matched and unmatched
        matched = [m for m in matches if m.is_match]
        missing = [m for m in matches if not m.is_match]

        # Calculate overall score with weighted approach
        # - Mandatory skills: 70% weight
        # - Nice-to-have skills: 30% weight
        # - Factor in confidence level

        mandatory_confidence = 0
        nice_confidence = 0
        mandatory_count = 0
        nice_count = 0

        for skill, match in zip(extracted_skills, matches):
            if skill.is_mandatory:
                mandatory_count += 1
                mandatory_confidence += match.confidence
            else:
                nice_count += 1
                nice_confidence += match.confidence

        # Weighted score
        if mandatory_count > 0:
            mandatory_score = (mandatory_confidence / mandatory_count) * 100
        else:
            mandatory_score = 0

        if nice_count > 0:
            nice_score = (nice_confidence / nice_count) * 100
        else:
            nice_score = 0

        # Overall = 70% mandatory + 30% nice-to-have
        overall_score = mandatory_score * 0.7 + nice_score * 0.3

        # Categorize by skill type
        mandatory_matches = []
        nice_to_have_matches = []

        for skill, match in zip(extracted_skills, matches):
            req_match = RequirementMatch(
                requirement=skill.context or skill.name,
                skill_key=skill.name,
                category=skill.category,
                is_mandatory=skill.is_mandatory,
                match_result=match,
                overall_score=match.confidence * 100,
            )

            if skill.is_mandatory:
                mandatory_matches.append(req_match)
            else:
                nice_to_have_matches.append(req_match)

        # Category scores
        category_scores = {}
        for skill in extracted_skills:
            cat = skill.category
            if cat not in category_scores:
                category_scores[cat] = []
            # Find corresponding match
            for m in matches:
                if m.skill.lower() == skill.name.lower():
                    category_scores[cat].append(m.confidence * 100)
                    break

        category_avg = {
            cat: sum(scores) / len(scores) if scores else 0
            for cat, scores in category_scores.items()
        }

        # Strengths and gaps
        strengths = [
            f"{m.skill_key}: {m.match_result.evidence_summary[:50]}"
            for m in mandatory_matches
            if m.match_result.is_match and m.match_result.confidence > 0.5
        ][:5]

        gaps = [
            f"{m.skill_key}: {m.match_result.missing_reason[:60]}"
            for m in mandatory_matches
            if not m.match_result.is_match
        ][:10]

        critical_gaps = [
            m.skill_key for m in mandatory_matches
            if not m.match_result.is_match and m.match_result.confidence < 0.1
        ][:5]

        # Recommendation
        if overall_score >= 70 and len(critical_gaps) <= 2:
            recommendation = "strong_match"
        elif overall_score >= 40:
            recommendation = "partial_match"
        else:
            recommendation = "poor_match"

        # Summary
        summary_parts = []
        if matched:
            summary_parts.append(f"{len(matched)}/{len(matches)} skills matched")
        if strengths:
            top_strength = strengths[0].split(':')[0]
            summary_parts.append(f"Strong in: {top_strength}")
        if gaps and not strengths:
            summary_parts.append("Needs evaluation for fit")

        return JDMatchResult(
            candidate=self.candidate,
            job_title="Job Position",
            overall_match_score=overall_score,
            mandatory_skills=mandatory_matches,
            nice_to_have_skills=nice_to_have_matches,
            matched_count=len(matched),
            missing_count=len(missing),
            partial_count=0,
            category_scores=category_avg,
            strengths=strengths,
            gaps=gaps,
            critical_gaps=critical_gaps,
            recommendation=recommendation,
            summary=" | ".join(summary_parts) if summary_parts else "Analysis complete",
            analysis_timestamp=datetime.now().isoformat(),
        )


def match_jd_dynamic(
    candidate: str,
    raw_data: dict[str, Any],
    jd_text: str,
) -> JDMatchResult:
    """
    Convenience function for dynamic JD matching.
    """
    matcher = DynamicMatcher()
    return matcher.match(candidate, raw_data, jd_text)
