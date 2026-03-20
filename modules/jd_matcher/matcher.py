"""
JD Matcher Engine
=================
Matches candidate GitHub profiles against job descriptions with full traceability.

For each JD requirement:
- Searches candidate data for evidence
- Creates traceable links (repo URLs, commit hashes, file paths)
- Calculates confidence scores
- Identifies gaps with reasons
"""

import logging
from datetime import datetime
from typing import Any, Optional

from modules.jd_matcher.jd_parser import (
    ParsedJobDescription,
    SkillRequirement,
    parse_job_description,
)
from modules.jd_matcher.types import (
    EvidenceLink,
    JDMatchResult,
    RequirementMatch,
    SkillMatch,
    format_match_result,
)

logger = logging.getLogger(__name__)


# Skill to GitHub evidence patterns
SKILL_TO_PATTERNS = {
    # Languages
    "python": {
        "topics": ["python", "py"],
        "deps": ["numpy", "pandas", "scipy", "scikit-learn", "pytest", "fastapi", "django", "flask"],
        "files": ["requirements.txt", "setup.py", "pyproject.toml"],
        "keywords": ["python", "pandas", "numpy"],
    },
    "r": {
        "topics": ["r", "rstats", "r-programming"],
        "deps": ["dplyr", "ggplot2", "tidyr", "caret"],
        "files": ["requirements.r", "DESCRIPTION"],
        "keywords": ["r programming", "rstudio", "tidyverse"],
    },
    "sql": {
        "topics": ["sql", "postgresql", "mysql", "database"],
        "deps": ["psycopg2", "sqlalchemy", "pymysql"],
        "files": ["*.sql", "migrations/"],
        "keywords": ["sql", "postgres", "mysql", "database query"],
    },

    # ML Frameworks
    "tensorflow": {
        "topics": ["tensorflow", "tf"],
        "deps": ["tensorflow", "tf-keras"],
        "keywords": ["tensorflow", "tf.keras"],
    },
    "pytorch": {
        "topics": ["pytorch", "torch"],
        "deps": ["torch", "pytorch", "torchvision"],
        "keywords": ["pytorch", "torch"],
    },
    "scikit-learn": {
        "topics": ["scikit-learn", "sklearn"],
        "deps": ["scikit-learn", "sklearn"],
        "keywords": ["scikit-learn", "sklearn", "machine learning"],
    },

    # MLOps & DevOps
    "mlops": {
        "topics": ["mlops", "ml-pipeline", "model-deployment"],
        "deps": ["mlflow", "kubeflow", "airflow"],
        "files": ["Dockerfile", "docker-compose.yml", ".github/workflows/"],
        "keywords": ["mlops", "model registry", "model versioning", "experiment tracking"],
    },
    "docker": {
        "topics": ["docker", "container"],
        "deps": [],
        "files": ["Dockerfile", "docker-compose.yml", ".dockerignore"],
        "keywords": ["docker", "containerization", "container"],
    },
    "kubernetes": {
        "topics": ["kubernetes", "k8s", "helm"],
        "deps": [],
        "files": ["k8s/", "kubernetes/", "helm/", "Chart.yaml"],
        "keywords": ["kubernetes", "k8s", "helm chart"],
    },
    "ci/cd": {
        "topics": ["ci-cd", "cicd", "github-actions"],
        "files": [".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile", "Jenkinsfile"],
        "keywords": ["github actions", "gitlab ci", "jenkins", "cicd", "continuous integration"],
    },

    # Cloud
    "azure": {
        "topics": ["azure", "azure-ml"],
        "deps": ["azure", "azure-ml", "azure-storage"],
        "keywords": ["azure", "azure ml", "azure functions", "azure storage"],
    },
    "aws": {
        "topics": ["aws", "amazon-web-services"],
        "deps": ["boto3", "aws-sam"],
        "keywords": ["aws", "amazon s3", "ec2", "lambda", "sagemaker"],
    },

    # Data
    "spark": {
        "topics": ["spark", "pyspark", "apache-spark"],
        "deps": ["pyspark", "spark"],
        "keywords": ["spark", "pyspark", "dataframe"],
    },
    "kafka": {
        "topics": ["kafka", "apache-kafka"],
        "deps": ["confluent-kafka", "kafka-python"],
        "keywords": ["kafka", "streaming", "confluent"],
    },
    "data pipeline": {
        "topics": ["data-pipeline", "etl", "data-engineering"],
        "deps": ["airflow", "luigi", "dagster", "pandas"],
        "keywords": ["etl", "data pipeline", "data flow"],
    },

    # ML Domains
    "time-series": {
        "topics": ["time-series", "forecasting", "prediction"],
        "deps": ["sktime", "prophet", "statsmodels", "pmdarima"],
        "keywords": ["time series", "forecasting", "arima", "lstm", "prediction"],
        "files": ["arima", "lstm", "forecasting", "prediction"],
    },
    "deep learning": {
        "topics": ["deep-learning", "neural-networks"],
        "deps": ["tensorflow", "pytorch", "keras"],
        "keywords": ["deep learning", "neural network", "cnn", "rnn", "lstm", "transformer"],
    },
    "machine learning": {
        "topics": ["machine-learning", "ml"],
        "deps": ["scikit-learn", "xgboost", "lightgbm", "catboost"],
        "keywords": ["machine learning", "ml", "classification", "regression", "clustering"],
    },
    "feature engineering": {
        "topics": ["feature-engineering"],
        "deps": [],
        "files": ["feature", "features", "preprocessing"],
        "keywords": ["feature engineering", "feature selection", "preprocessing"],
    },
    "model deployment": {
        "topics": ["model-deployment", "serving", "inference"],
        "deps": ["fastapi", "flask", "uvicorn", "seldon", "triton"],
        "files": ["api/", "serve/", "inference/"],
        "keywords": ["model serving", "rest api", "inference", "deployment"],
    },
    "model monitoring": {
        "topics": ["model-monitoring", "ml-monitoring"],
        "deps": ["evidently", "prometheus", "grafana", "sentry"],
        "keywords": ["model monitoring", "drift detection", "evidently", "prometheus"],
    },

    # GenAI
    "genai": {
        "topics": ["genai", "llm", "gpt", "langchain"],
        "deps": ["openai", "anthropic", "langchain", "llamaindex", "huggingface"],
        "keywords": ["llm", "gpt", "langchain", "rag", "agent", "generative ai", "openai"],
    },

    # Optimization
    "optimization": {
        "topics": ["optimization", "operations-research"],
        "deps": ["scipy", "pulp", "ortools", "cvxpy"],
        "keywords": ["optimization", "linear programming", "constraint", "lp", "milp"],
    },
    "reinforcement learning": {
        "topics": ["reinforcement-learning", "rl"],
        "deps": ["gymnasium", "ray", "stable-baselines"],
        "keywords": ["reinforcement learning", "policy gradient", "q-learning", "rl"],
    },
}


class JDMatcher:
    """
    Matches candidate GitHub profiles against job descriptions.

    Provides full traceability for every match decision.
    """

    def __init__(self):
        self.candidate: str = ""
        self.raw_data: dict[str, Any] = {}
        self.explainable_result: Any = None
        self.parsed_jd: Optional[ParsedJobDescription] = None

    def match(
        self,
        candidate: str,
        raw_data: dict[str, Any],
        explainable_result: Any,
        jd_text: str,
    ) -> JDMatchResult:
        """
        Match candidate against job description.

        Args:
            candidate: GitHub handle
            raw_data: Raw harvested data (repos, commits, deps, etc.)
            explainable_result: Existing explainability result
            jd_text: Job description text

        Returns:
            JDMatchResult with full traceability
        """
        self.candidate = candidate
        self.raw_data = raw_data
        self.explainable_result = explainable_result

        logger.info(f"Matching {candidate} against job description")

        # Parse JD
        self.parsed_jd = parse_job_description(jd_text)

        # Extract candidate data
        repos = raw_data.get("repos", []) or []
        commits = raw_data.get("commits", []) or []
        dep_files = raw_data.get("dep_files", {}) or {}
        lang_bytes = raw_data.get("lang_bytes", {}) or {}

        # Match each requirement
        mandatory_matches = []
        nice_to_have_matches = []

        for skill_req in self.parsed_jd.mandatory_skills:
            match = self._match_skill(
                skill_req,
                repos,
                commits,
                dep_files,
                lang_bytes,
            )
            mandatory_matches.append(RequirementMatch(
                requirement=skill_req.context,
                skill_key=skill_req.skill,
                category=skill_req.category,
                is_mandatory=True,
                match_result=match,
                overall_score=match.confidence * 100,
                weight=skill_req.weight,
            ))

        for skill_req in self.parsed_jd.nice_to_have_skills:
            match = self._match_skill(
                skill_req,
                repos,
                commits,
                dep_files,
                lang_bytes,
            )
            nice_to_have_matches.append(RequirementMatch(
                requirement=skill_req.context,
                skill_key=skill_req.skill,
                category=skill_req.category,
                is_mandatory=False,
                match_result=match,
                overall_score=match.confidence * 100,
                weight=skill_req.weight,
            ))

        # Calculate overall scores
        result = self._build_match_result(
            mandatory_matches,
            nice_to_have_matches,
        )

        logger.info(
            f"Match complete: {result.matched_count}/{result.missing_count + result.matched_count} skills matched"
        )

        return result

    def _match_skill(
        self,
        skill_req: SkillRequirement,
        repos: list[dict],
        commits: list[dict],
        dep_files: dict,
        lang_bytes: dict,
    ) -> SkillMatch:
        """Match a single skill requirement against candidate data."""

        skill_key = skill_req.skill.lower()
        patterns = SKILL_TO_PATTERNS.get(skill_key, {})

        evidence = []
        contributing_repos = []
        supporting_commits = []
        matched_keywords = []
        total_weight = 0.0

        # 1. Check topics across repos
        topic_evidence = self._check_topics(skill_key, patterns, repos)
        if topic_evidence:
            evidence.extend(topic_evidence)
            for ev in topic_evidence:
                contributing_repos.extend(ev.description.split(', '))
            total_weight += 0.4

        # 2. Check dependencies
        dep_evidence = self._check_dependencies(skill_key, patterns, dep_files, repos)
        if dep_evidence:
            evidence.extend(dep_evidence)
            total_weight += 0.3

        # 3. Check language bytes
        lang_evidence = self._check_language_bytes(skill_key, repos, lang_bytes)
        if lang_evidence:
            evidence.extend(lang_evidence)
            total_weight += 0.2

        # 4. Check commit messages/patterns
        commit_evidence = self._check_commits(skill_key, patterns, commits, repos)
        if commit_evidence:
            evidence.extend(commit_evidence)
            for ev in commit_evidence:
                supporting_commits.append(ev.description)
            total_weight += 0.1

        # Calculate confidence
        is_match = len(evidence) > 0
        confidence = min(0.95, total_weight) if is_match else 0.0

        # Build evidence summary
        if evidence:
            evidence_summary_parts = []
            if topic_evidence:
                topic_repos = [e.description for e in topic_evidence if 'topic' in e.type]
                if topic_repos:
                    evidence_summary_parts.append(f"Topics: {', '.join(topic_repos[:3])}")
            if dep_evidence:
                dep_names = [e.description for e in dep_evidence[:5]]
                evidence_summary_parts.append(f"Dependencies: {', '.join(dep_names)}")
            evidence_summary = "; ".join(evidence_summary_parts)
        else:
            evidence_summary = ""

        # Determine missing reason
        if not is_match:
            missing_reason = self._get_missing_reason(skill_key, patterns, repos, dep_files)
        else:
            missing_reason = ""

        return SkillMatch(
            skill=skill_req.skill,
            is_match=is_match,
            confidence=confidence,
            evidence=evidence,
            evidence_summary=evidence_summary,
            contributing_repos=list(set(contributing_repos))[:10],
            supporting_commits=supporting_commits[:10],
            missing_reason=missing_reason,
            matched_keywords=matched_keywords,
        )

    def _check_topics(
        self,
        skill_key: str,
        patterns: dict,
        repos: list[dict],
    ) -> list[EvidenceLink]:
        """Check if skill is mentioned in repo topics."""
        evidence = []
        topics = patterns.get("topics", [])

        for repo in repos:
            repo_name = repo.get("name", "")
            repo_topics = [str(t).lower() for t in (repo.get("topics", []) or [])]
            full_name = repo.get("full_name", "")

            matched_topics = []
            for topic in topics:
                if topic.lower() in repo_topics:
                    matched_topics.append(topic)

            if matched_topics:
                evidence.append(EvidenceLink(
                    url=f"https://github.com/{full_name}",
                    type="repo_topic",
                    description=f"{repo_name}: {', '.join(matched_topics)}",
                    weight=0.3,
                    verified=True,
                ))

        return evidence

    def _check_dependencies(
        self,
        skill_key: str,
        patterns: dict,
        dep_files: dict,
        repos: list[dict],
    ) -> list[EvidenceLink]:
        """Check if skill is in dependency files."""
        evidence = []
        deps = patterns.get("deps", [])

        if not deps:
            return evidence

        # Search in dependency files
        for file_name, content in dep_files.items():
            if not content:
                continue

            content_lower = str(content).lower()
            matched_deps = []

            for dep in deps:
                if dep.lower() in content_lower:
                    matched_deps.append(dep)

            if matched_deps:
                # Find which repo this belongs to
                repo_name = "unknown"
                for repo in repos:
                    if repo.get("name", "") in file_name or file_name.startswith(repo.get("name", "")):
                        repo_name = repo.get("name", "")
                        break

                evidence.append(EvidenceLink(
                    url=f"https://github.com/search?q=repo:{self.candidate}%2F{repo_name}+{matched_deps[0]}&type=code",
                    type="dependency",
                    description=f"{matched_deps[0]} in {file_name}",
                    weight=0.25,
                    verified=False,
                ))

        return evidence

    def _check_language_bytes(
        self,
        skill_key: str,
        repos: list[dict],
        lang_bytes: dict,
    ) -> list[EvidenceLink]:
        """Check if skill matches primary languages."""
        evidence = []

        # Language to language name mapping
        lang_map = {
            "python": "Python",
            "r": "R",
            "java": "Java",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "c++": "C++",
            "scala": "Scala",
            "go": "Go",
            "rust": "Rust",
        }

        if skill_key in lang_map:
            lang_name = lang_map[skill_key]
            lang_bytes_val = lang_bytes.get(lang_name, 0)

            if lang_bytes_val > 0:
                total = sum(lang_bytes.values())
                percentage = (lang_bytes_val / total * 100) if total > 0 else 0

                # Find repos using this language
                repos_using = []
                for repo in repos:
                    if repo.get("language", "") == lang_name:
                        repos_using.append(repo.get("name", ""))

                if repos_using:
                    evidence.append(EvidenceLink(
                        url=f"https://github.com/{self.candidate}?tab=repositories&q=&language={lang_name}",
                        type="language",
                        description=f"{lang_name}: {percentage:.1f}% of codebase across {len(repos_using)} repos",
                        weight=0.2,
                        verified=True,
                    ))

        return evidence

    def _check_commits(
        self,
        skill_key: str,
        patterns: dict,
        commits: list[dict],
        repos: list[dict],
    ) -> list[EvidenceLink]:
        """Check if skill is mentioned in commit messages."""
        evidence = []
        keywords = patterns.get("keywords", [])

        if not keywords or not commits:
            return evidence

        # Count commits matching keywords
        matching_commits = []
        for commit in commits:
            message = (commit.get("message", "") or "").lower()
            if any(kw.lower() in message for kw in keywords):
                matching_commits.append(commit)

        if matching_commits:
            # Get unique repos with matching commits
            repos_with_matches = set()
            for commit in matching_commits[:5]:
                repo_name = commit.get("repo_name", "")
                if repo_name:
                    repos_with_matches.add(repo_name)

            if repos_with_matches:
                # Get sample commit hash
                sample = matching_commits[0]
                commit_hash = sample.get("commit_hash", sample.get("sha", ""))[:7]
                repo_name = sample.get("repo_name", "")

                evidence.append(EvidenceLink(
                    url=f"https://github.com/{self.candidate}/{repo_name}/commit/{commit_hash}",
                    type="commit",
                    description=f"{len(matching_commits)} commits mentioning: {', '.join(keywords[:3])}",
                    weight=0.1,
                    verified=False,
                ))

        return evidence

    def _get_missing_reason(
        self,
        skill_key: str,
        patterns: dict,
        repos: list[dict],
        dep_files: dict,
    ) -> str:
        """Generate reason why skill is missing."""
        reasons = []

        # Check if related skills exist
        related_skills = {
            "azure": ["aws", "gcp"],
            "mlops": ["docker", "kubernetes"],
            "time-series": ["machine learning", "forecasting"],
            "genai": ["machine learning", "deep learning"],
        }

        related = related_skills.get(skill_key, [])
        found_related = []

        for repo in repos:
            topics = [str(t).lower() for t in (repo.get("topics", []) or [])]
            for rel in related:
                if rel.lower() in topics:
                    found_related.append(rel)

        if found_related:
            reasons.append(f"Related skills found: {', '.join(found_related)}, but not {skill_key} specifically")

        if not reasons:
            reasons.append(f"No evidence of {skill_key} in topics, dependencies, or commit history")

        return "; ".join(reasons)

    def _build_match_result(
        self,
        mandatory_matches: list[RequirementMatch],
        nice_to_have_matches: list[RequirementMatch],
    ) -> JDMatchResult:
        """Build final match result with scores and summary."""

        matched = [m for m in mandatory_matches if m.match_result.is_match]
        missing = [m for m in mandatory_matches if not m.match_result.is_match]

        # Calculate overall score
        if mandatory_matches:
            total_weight = sum(m.weight for m in mandatory_matches)
            weighted_score = sum(
                m.overall_score * m.weight for m in mandatory_matches
            ) / total_weight if total_weight > 0 else 0
        else:
            weighted_score = 50  # Neutral if no mandatory skills

        # Bonus for nice-to-have
        nice_matched = [m for m in nice_to_have_matches if m.match_result.is_match]
        if nice_to_have_matches:
            nice_bonus = len(nice_matched) / len(nice_to_have_matches) * 10
            weighted_score = min(100, weighted_score + nice_bonus)

        # Category scores
        category_scores = {}
        for match in mandatory_matches:
            cat = match.category
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(match.overall_score)

        category_avg = {
            cat: sum(scores) / len(scores)
            for cat, scores in category_scores.items()
        }

        # Identify strengths and gaps
        strengths = []
        gaps = []
        critical_gaps = []

        for match in mandatory_matches:
            if match.match_result.is_match and match.match_result.confidence > 0.6:
                strengths.append(
                    f"{match.skill_key}: {match.match_result.evidence_summary[:60]}"
                )
            else:
                gaps.append(
                    f"{match.skill_key}: {match.match_result.missing_reason[:60]}"
                )
                if match.match_result.confidence < 0.3:
                    critical_gaps.append(match.skill_key)

        # Generate summary
        summary_parts = []

        if len(matched) >= len(mandatory_matches) * 0.7:
            summary_parts.append(
                f"Strong match with {len(matched)}/{len(mandatory_matches)} mandatory skills found"
            )
        elif len(matched) >= len(mandatory_matches) * 0.4:
            summary_parts.append(
                f"Partial match with {len(matched)}/{len(mandatory_matches)} mandatory skills found"
            )
        else:
            summary_parts.append(
                f"Weak match with only {len(matched)}/{len(mandatory_matches)} mandatory skills found"
            )

        if nice_matched:
            summary_parts.append(
                f"Plus {len(nice_matched)}/{len(nice_to_have_matches)} nice-to-have skills"
            )

        # Recommendation
        if weighted_score >= 75 and len(critical_gaps) == 0:
            recommendation = "strong_match"
            summary_parts.append("- Recommended for interview")
        elif weighted_score >= 50:
            recommendation = "partial_match"
            summary_parts.append("- Consider for interview with skills assessment")
        else:
            recommendation = "poor_match"
            summary_parts.append("- Does not meet core requirements")

        return JDMatchResult(
            candidate=self.candidate,
            job_title=self.parsed_jd.title or "Unknown Position",
            overall_match_score=weighted_score,
            mandatory_skills=mandatory_matches,
            nice_to_have_skills=nice_to_have_matches,
            matched_count=len(matched),
            missing_count=len(missing),
            partial_count=len([m for m in mandatory_matches if 0 < m.match_result.confidence < 0.6]),
            category_scores=category_avg,
            strengths=strengths[:5],
            gaps=gaps[:10],
            critical_gaps=critical_gaps[:5],
            recommendation=recommendation,
            summary=" ".join(summary_parts),
            analysis_timestamp=datetime.now().isoformat(),
        )


def match_jd(
    candidate: str,
    raw_data: dict[str, Any],
    explainable_result: Any,
    jd_text: str,
) -> JDMatchResult:
    """
    Convenience function to match candidate against job description.

    Args:
        candidate: GitHub handle
        raw_data: Raw harvested data
        explainable_result: Existing explainability result
        jd_text: Job description text

    Returns:
        JDMatchResult with full traceability
    """
    matcher = JDMatcher()
    return matcher.match(candidate, raw_data, explainable_result, jd_text)
