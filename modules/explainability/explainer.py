"""
Explainability Engine
=====================
Generates human-readable explanations for skill assessments.

Every claim is backed by traceable evidence with full provenance chains:
"We believe X because Y"

Usage:
    explainable = explain_skill_intelligence(raw_data, skill_result)
"""

import logging
from typing import Any, Optional

from modules.skill_analyzer.types import (
    EvidenceItem,
    EvidenceSource,
    ExplainableSkill,
    ExplainableResult,
    ProjectEvidence,
    ProblemTrace,
)

logger = logging.getLogger(__name__)


# =============================================================================
# COMPLEXITY THRESHOLDS FOR SENIOR DETECTION
# =============================================================================

COMPLEXITY_THRESHOLDS = {
    "junior": 3.0,
    "mid": 5.0,
    "senior": 7.0,
    "staff": 10.0,
    "principal": 15.0,
}

# Skills that indicate production-grade experience
PRODUCTION_FRAMEWORKS = {
    "fastapi", "django", "flask", "express", "koa", "fastify",
    "react", "vue", "angular", "next.js", "nuxt",
    "spring", "spring boot", "rails", "laravel",
    "fastapi", "uvicorn", "gunicorn",
    "pandas", "polars", "dask",
    "pytorch", "tensorflow", "keras",
}

# Skills that indicate infrastructure/enterprise readiness
INFRASTRUCTURE_INDICATORS = {
    "docker", "kubernetes", "terraform", "ansible",
    "aws", "gcp", "azure",
    "jenkins", "github-actions", "gitlab-ci",
    "prometheus", "grafana", "datadog",
    "postgresql", "mysql", "redis", "kafka",
}


class ExplainabilityEngine:
    """
    Generates explainable skill assessments with full provenance.

    Wraps the existing SkillIntelligenceResult and adds:
    - Evidence chains for each skill
    - Human-readable reasoning
    - Identified gaps
    - Project evidence with explanations
    - Problem-solving traces
    """

    def __init__(self):
        self.raw_data: dict[str, Any] = {}
        self.skill_result: Any = None
        self.skills: dict[str, ExplainableSkill] = {}
        self.projects: list[ProjectEvidence] = []
        self.traces: list[ProblemTrace] = []

    def explain(
        self,
        raw_data: dict[str, Any],
        skill_result: Any,
    ) -> ExplainableResult:
        """
        Generate explainable skill assessment.

        Args:
            raw_data: Full harvested data (repos, commits, deps, etc.)
            skill_result: Existing SkillIntelligenceResult from engine

        Returns:
            ExplainableResult with full provenance chains
        """
        self.raw_data = raw_data
        self.skill_result = skill_result

        logger.info("Starting explainability analysis...")

        # Extract base data
        repos = raw_data.get("repos", []) or []
        commits = raw_data.get("commits", []) or []
        dep_files = raw_data.get("dep_files", {}) or {}
        aggregates = raw_data.get("aggregates", {}) or {}
        lang_bytes = raw_data.get("lang_bytes", {}) or {}

        # Step 1: Trace evidence for each inferred skill
        self._trace_all_evidence(repos, commits, dep_files, aggregates, lang_bytes)

        # Step 2: Generate reasoning for each skill
        self._generate_all_reasoning(repos, commits, aggregates)

        # Step 3: Build project evidence
        self._build_project_evidence(repos, commits, aggregates)

        # Step 4: Extract problem-solving traces
        self._extract_problem_traces(repos, commits)

        # Step 5: Build final result
        result = self._build_explainable_result(repos)

        logger.info(f"Explainability analysis complete: {len(self.skills)} skills, "
                   f"{len(self.projects)} projects, {len(self.traces)} traces")

        return result

    def _trace_all_evidence(
        self,
        repos: list[dict],
        commits: list[dict],
        dep_files: dict,
        aggregates: dict,
        lang_bytes: dict,
    ) -> None:
        """Trace evidence from all sources for each detected skill."""

        # Get inferred skills from skill_result
        signals = getattr(self.skill_result, 'signals', {}) or {}
        frameworks = getattr(self.skill_result, 'frameworks', []) or []
        infrastructure = getattr(self.skill_result, 'infrastructure', []) or []
        detected_domains = getattr(self.skill_result, 'detected_domains', []) or []
        skill_profile = getattr(self.skill_result, 'skill_profile', None)

        # Get skill level
        skill_level = ""
        skill_level_confidence = 0.0
        if skill_profile:
            skill_level = skill_profile.skill_level or "Mid"
            skill_level_confidence = skill_profile.skill_level_confidence or 0.5

        # Language-based skills (top languages by byte count)
        language_depth = getattr(self.skill_result, 'language_depth', {}) or {}
        top_languages = sorted(language_depth.items(), key=lambda x: x[1], reverse=True)[:5]

        for lang, depth in top_languages:
            if depth < 0.05:  # Skip negligible languages
                continue

            skill_key = lang
            evidence = {}

            # Trace language evidence
            if lang_bytes:
                total_bytes = sum(lang_bytes.values())
                lang_byte_count = lang_bytes.get(lang, 0)
                byte_mb = round(lang_byte_count / (1024 * 1024), 1)
                repos_with_lang = sum(1 for r in repos if r.get("language", "").lower() == lang.lower())
                evidence["language_bytes"] = (
                    f"{byte_mb}MB in {lang} across {repos_with_lang} repos "
                    f"(total codebase: {round(total_bytes / (1024*1024), 1)}MB)"
                )

            # Trace framework evidence
            relevant_frameworks = [f for f in frameworks if f.lower() in [
                lang.lower(), f"{lang.lower()}-".join([""]), f"-{lang.lower()}"
            ]]
            if relevant_frameworks:
                evidence["frameworks"] = f"Uses: {', '.join(relevant_frameworks[:5])}"

            # Infer level from depth
            if depth > 0.6:
                inferred_level = "Senior" if depth > 0.7 else "Mid"
            elif depth > 0.3:
                inferred_level = "Mid"
            else:
                inferred_level = "Junior"

            # Production framework indicator
            production_indicators = [f for f in frameworks if any(
                pf.lower() in f.lower() for pf in PRODUCTION_FRAMEWORKS
            )]
            if production_indicators:
                evidence["production_quality"] = (
                    f"Uses production-grade frameworks: {', '.join(production_indicators[:3])}"
                )

            self.skills[skill_key] = ExplainableSkill(
                skill=lang,
                level=inferred_level,
                confidence=min(0.95, depth + 0.1),
                evidence=evidence,
                reasoning=[],
                gaps=[],
                contributing_repos=[],
                supporting_signals=[],
                evidence_items=[],
            )

        # Framework-based skills
        for framework in frameworks[:8]:  # Top 8 frameworks
            skill_key = framework
            if skill_key in self.skills:
                continue

            evidence = {
                "framework": f"{framework} detected in dependencies"
            }

            # Find repos using this framework
            repos_with_framework = []
            for repo in repos:
                desc = repo.get("description", "") or ""
                topics = repo.get("topics", []) or []
                if (framework.lower() in desc.lower() or
                    any(framework.lower() in str(t).lower() for t in topics)):
                    repos_with_framework.append(repo.get("name", ""))

            if repos_with_framework:
                evidence["repos"] = f"Found in {len(repos_with_framework)} repos: {', '.join(repos_with_framework[:3])}"

            # Production indicator
            if any(pf.lower() in framework.lower() for pf in PRODUCTION_FRAMEWORKS):
                evidence["production_quality"] = "Production-grade framework"

            self.skills[skill_key] = ExplainableSkill(
                skill=framework,
                level="Mid",  # Default, can be upgraded based on evidence
                confidence=0.75,
                evidence=evidence,
                reasoning=[],
                gaps=[],
                contributing_repos=repos_with_framework[:5],
                supporting_signals=["framework_detected"],
                evidence_items=[],
            )

        # Domain-based skills (from detected_domains)
        for domain in detected_domains[:5]:  # Top 5 domains
            domain_name = domain.domain
            skill_key = domain_name

            if skill_key in self.skills:
                continue

            evidence = {
                "domain_detection": f"Detected with {domain.confidence:.0%} confidence",
            }

            if domain.primary_technologies:
                evidence["technologies"] = (
                    f"Based on technologies: {', '.join(domain.primary_technologies[:5])}"
                )

            if domain.signals:
                evidence["signals"] = f"Signals: {', '.join(domain.signals[:5])}"

            self.skills[skill_key] = ExplainableSkill(
                skill=domain_name,
                level="Mid",
                confidence=domain.confidence,
                evidence=evidence,
                reasoning=[],
                gaps=[],
                contributing_repos=[],
                supporting_signals=domain.signals[:5] if domain.signals else [],
                evidence_items=[],
            )

        # Infrastructure skills
        for infra in infrastructure[:5]:
            skill_key = infra
            evidence = {
                "infrastructure": f"{infra} detected in dependencies or file patterns"
            }

            repos_using_infra = []
            for repo in repos:
                desc = (repo.get("description", "") or "").lower()
                topics = [str(t).lower() for t in (repo.get("topics", []) or [])]
                if infra.lower() in desc or infra.lower() in topics:
                    repos_using_infra.append(repo.get("name", ""))

            if repos_using_infra:
                evidence["repos"] = f"Found in: {', '.join(repos_using_infra[:3])}"

            self.skills[skill_key] = ExplainableSkill(
                skill=infra,
                level="Mid",
                confidence=0.7,
                evidence=evidence,
                reasoning=[],
                gaps=[],
                contributing_repos=repos_using_infra[:5],
                supporting_signals=["infrastructure_detected"],
                evidence_items=[],
            )

    def _generate_all_reasoning(
        self,
        repos: list[dict],
        commits: list[dict],
        aggregates: dict,
    ) -> None:
        """Generate human-readable reasoning for each skill."""

        skill_profile = getattr(self.skill_result, 'skill_profile', None)
        if not skill_profile:
            return

        lang_bytes = self.raw_data.get("lang_bytes", {}) or {}
        language_depth = getattr(self.skill_result, 'language_depth', {}) or {}
        frameworks = getattr(self.skill_result, 'frameworks', []) or []
        detected_domains = getattr(self.skill_result, 'detected_domains', []) or []

        # Get aggregates
        total_commits = aggregates.get("total_commits", 0)
        total_prs = aggregates.get("total_prs", 0)
        test_coverage = aggregates.get("test_coverage_ratio", 0)
        ci_usage = aggregates.get("ci_usage_ratio", 0)

        for skill_name, skill in self.skills.items():
            reasoning = []
            gaps = []
            supporting_signals = []

            # === SKILL LEVEL REASONING ===

            # Check language depth for level
            lang_depth = language_depth.get(skill_name, 0)
            if lang_depth > 0.5:
                reasoning.append(
                    f"Strong {skill_name} depth ({lang_depth:.0%} of codebase) indicates "
                    f"long-term, dedicated usage"
                )
                supporting_signals.append("high_language_depth")

            # Check for production frameworks
            has_production = any(pf.lower() in skill_name.lower() for pf in PRODUCTION_FRAMEWORKS)
            if not has_production:
                has_production = any(
                    pf.lower() in str(skill.evidence.get("frameworks", "")).lower()
                    for pf in PRODUCTION_FRAMEWORKS
                )

            if has_production:
                reasoning.append(
                    "Production-grade framework usage indicates real-world, "
                    "enterprise experience"
                )
                supporting_signals.append("production_framework")

            # Commit volume reasoning
            if total_commits > 500:
                reasoning.append(
                    f"High commit volume ({total_commits}+ commits) suggests "
                    f"consistent, sustained contribution"
                )
                supporting_signals.append("high_commit_volume")
            elif total_commits > 100:
                reasoning.append(
                    f"Moderate commit activity ({total_commits} commits) "
                    f"shows ongoing engagement"
                )
                supporting_signals.append("moderate_commit_volume")

            # Quality signals
            if test_coverage > 0.3:
                reasoning.append(
                    f"Test coverage ({test_coverage:.0%}) indicates "
                    f"quality-focused engineering practices"
                )
                supporting_signals.append("test_coverage")

            if ci_usage > 0.5:
                reasoning.append(
                    f"CI/CD usage ({ci_usage:.0%} of repos) indicates "
                    f"professional development workflows"
                )
                supporting_signals.append("ci_cd_usage")

            # Domain reasoning
            for domain in detected_domains:
                if skill_name.lower() in domain.domain.lower():
                    reasoning.append(
                        f"Primary domain ({domain.domain}) confirmed by: "
                        f"{', '.join(domain.primary_technologies[:3])}"
                    )
                    supporting_signals.append("domain_confirmed")

            # === GAPS IDENTIFICATION ===

            # Check for missing signals
            if not skill.evidence.get("frameworks") and not skill.evidence.get("framework"):
                gaps.append("No framework usage detected - may be early in career")

            if total_commits < 100 and not gaps:
                gaps.append("Limited commit history - assessment based on fewer signals")

            if test_coverage < 0.3:
                gaps.append("Low test coverage - quality practices unclear")

            if ci_usage < 0.3:
                gaps.append("Limited CI/CD usage - development workflow unclear")

            # Missing infrastructure signals
            has_infra = any(
                infra.lower() in skill.evidence.get("infrastructure", "").lower()
                for infra in INFRASTRUCTURE_INDICATORS
            )
            if not has_infra and skill_name.lower() not in ["docker", "kubernetes", "terraform"]:
                gaps.append("No infrastructure/deployment experience detected")

            # Update skill
            skill.reasoning = reasoning if reasoning else [
                f"Based on language analysis and repository patterns"
            ]
            skill.gaps = gaps
            skill.supporting_signals = supporting_signals or skill.supporting_signals

    def _build_project_evidence(
        self,
        repos: list[dict],
        commits: list[dict],
        aggregates: dict,
    ) -> None:
        """Build evidence for individual projects."""

        top_repos = getattr(self.skill_result, 'top_repos', []) or []

        for repo_data in top_repos[:5]:  # Top 5 projects
            repo_name = repo_data.get("name", "")
            stars = repo_data.get("stars", 0)
            forks = repo_data.get("forks", 0)
            impact_score = repo_data.get("impact_score", 0)
            project_type = repo_data.get("project_type", "")

            # Find full repo data
            full_repo = None
            for repo in repos:
                if repo.get("name", "") == repo_name:
                    full_repo = repo
                    break

            if not full_repo:
                continue

            # Determine skills demonstrated
            skills_demo = []
            desc = (full_repo.get("description", "") or "").lower()
            topics = [str(t).lower() for t in (full_repo.get("topics", []) or [])]
            lang = (full_repo.get("language", "") or "").lower()

            if lang:
                skills_demo.append(lang)
            if any(t in desc for t in ["ml", "machine learning", "ai", "deep learning"]):
                skills_demo.append("Machine Learning")
            if any(t in desc for t in ["api", "server", "backend"]):
                skills_demo.append("Backend Development")
            if any(t in desc for t in ["web", "frontend", "ui"]):
                skills_demo.append("Frontend Development")
            if any(t in desc for t in ["data", "pipeline", "etl"]):
                skills_demo.append("Data Engineering")
            if any(t in desc for t in ["devops", "deploy", "ci"]):
                skills_demo.append("DevOps")

            # Determine signals
            signals = []
            if stars > 100:
                signals.append(f"{stars} stars - meaningful community impact")
            if forks > 50:
                signals.append(f"{forks} forks - actively copied/built upon")
            if project_type:
                signals.append(f"Type: {project_type}")
            if full_repo.get("has_issues"):
                signals.append("Open issue tracking")
            if full_repo.get("is_archived"):
                signals.append("Archived (no longer maintained)")

            # Why it matters
            if stars > 1000:
                why_it_matters = (
                    f"High-impact project ({stars} stars) - demonstrates ability to create "
                    f"valuable, widely-used software that the community trusts"
                )
            elif stars > 100:
                why_it_matters = (
                    f"Notable project ({stars} stars) - shows ability to ship and maintain "
                    f"software that others find useful"
                )
            elif impact_score > 30:
                why_it_matters = (
                    f"Complex project (impact score: {impact_score:.0f}) - "
                    f"demonstrates significant technical work"
                )
            else:
                why_it_matters = (
                    f"Personal/maintained project - shows continued engagement and ownership"
                )

            # Complexity signals
            complexity = repo_data.get("complexity_signals", {}) or {}
            complexity_signals = list(complexity.keys())[:5] if complexity else []

            self.projects.append(ProjectEvidence(
                name=repo_name,
                full_name=full_repo.get("full_name", ""),
                impact=f"{stars:,} stars" if stars > 0 else "Private/Unlisted",
                stars=stars,
                forks=forks,
                skills_demonstrated=skills_demo,
                signals=signals,
                why_it_matters=why_it_matters,
                complexity_signals=complexity_signals,
                key_commits=[],
            ))

    def _extract_problem_traces(
        self,
        repos: list[dict],
        commits: list[dict],
    ) -> None:
        """Extract problem-solving traces from commits."""

        if not commits:
            return

        # Group commits by repo
        commits_by_repo: dict[str, list[dict]] = {}
        for commit in commits:
            repo_name = commit.get("repo_name", "")
            if repo_name:
                if repo_name not in commits_by_repo:
                    commits_by_repo[repo_name] = []
                commits_by_repo[repo_name].append(commit)

        # Find interesting commits
        for repo_name, repo_commits in commits_by_repo.items():
            if not repo_commits:
                continue

            # Sort by complexity (files changed, lines modified)
            interesting = []
            for commit in repo_commits:
                num_files = commit.get("num_files", 0)
                total_lines = commit.get("total_lines", 0)
                commit_type = commit.get("commit_type", "other")
                is_verified = commit.get("verified", False)

                # Only include significant commits
                if num_files >= 5 or total_lines >= 200:
                    interesting.append({
                        **commit,
                        "repo_name": repo_name,
                        "quality_score": num_files + (total_lines / 100) + (10 if is_verified else 0),
                    })

            # Take top 3 most complex commits per repo
            interesting.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            for commit in interesting[:3]:
                commit_type = commit.get("commit_type", "other")
                commit_hash = commit.get("commit_hash", commit.get("sha", ""))[:8]

                # Determine trace type
                trace_type = "code_change"
                if commit_type == "bug_fix":
                    trace_type = "bug_fix"
                elif commit_type == "refactor":
                    trace_type = "refactoring"
                elif commit_type == "feature":
                    trace_type = "feature"
                elif num_files := commit.get("num_files", 0) >= 10:
                    trace_type = "complex_refactor"

                # Quality signal
                quality_signal = "Standard commit"
                if commit.get("verified"):
                    quality_signal = "Signed-off commit - professional practice"
                elif commit.get("num_files", 0) >= 10:
                    quality_signal = "Large-scale change - architectural decision"
                elif commit.get("total_lines", 0) >= 500:
                    quality_signal = "Significant refactoring - deep system understanding"

                self.traces.append(ProblemTrace(
                    type=trace_type,
                    repo=commit.get("full_name", repo_name),
                    repo_name=repo_name,
                    commit_hash=commit_hash,
                    summary=commit.get("message", f"{trace_type.replace('_', ' ').title()} - {num_files} files"),
                    quality_signal=quality_signal,
                    files_changed=commit.get("num_files", 0),
                    lines_added=commit.get("lines_added", 0),
                    lines_deleted=commit.get("lines_deleted", 0),
                    is_verified=commit.get("verified", False),
                ))

        # Sort all traces by quality
        self.traces.sort(key=lambda x: x.files_changed, reverse=True)
        self.traces = self.traces[:20]  # Limit to top 20

    def _build_explainable_result(self, repos: list[dict]) -> ExplainableResult:
        """Build the final ExplainableResult."""

        skill_profile = getattr(self.skill_result, 'skill_profile', None)
        detected_domains = getattr(self.skill_result, 'detected_domains', []) or []

        # Primary language
        language_depth = getattr(self.skill_result, 'language_depth', {}) or {}
        primary_lang = max(language_depth.items(), key=lambda x: x[1]) if language_depth else ("Unknown", 0)

        # Primary domains
        primary_domains = [d.domain for d in detected_domains[:3]] if detected_domains else []

        # Overall confidence
        overall_confidence = 0.7
        if skill_profile:
            overall_confidence = min(0.95, skill_profile.skill_level_confidence + 0.1)

        # Caveats
        caveats = []
        if len(repos) < 5:
            caveats.append(f"Limited repository data ({len(repos)} repos) - assessment may miss key areas")
        if not self.traces:
            caveats.append("No commit-level details available - harder to assess problem-solving approach")

        # Generate summary
        summary_parts = []
        if skill_profile:
            level = skill_profile.skill_level
            years = skill_profile.years_experience_estimate
            domains_str = ", ".join(primary_domains[:2]) if primary_domains else "General Software"

            summary_parts.append(
                f"{level}-level developer" if level else "Mid-level developer"
            )
            if years:
                summary_parts.append(f"with ~{years} years estimated experience")
            if primary_domains:
                summary_parts.append(f"focused on {domains_str}")
            summary_parts.append(f"Primary stack: {primary_lang[0]}")
        else:
            summary_parts.append("Developer with Python and general software development skills")

        summary = " ".join(summary_parts) + "."

        # Add confidence caveat
        if overall_confidence < 0.7:
            caveats.append("Lower confidence due to limited evidence signals")

        return ExplainableResult(
            candidate=self.raw_data.get("handle", "unknown"),
            skill_assessment=self.skills,
            primary_language=primary_lang[0],
            primary_language_depth=primary_lang[1],
            domains=primary_domains,
            project_evidence=self.projects,
            problem_solving_traces=self.traces,
            summary=summary,
            confidence=overall_confidence,
            caveats=caveats,
        )


def explain_skill_intelligence(
    raw_data: dict[str, Any],
    skill_result: Any,
) -> ExplainableResult:
    """
    Convenience function to generate explainable skill assessment.

    Args:
        raw_data: Full harvested data (repos, commits, deps, etc.)
        skill_result: Existing SkillIntelligenceResult from engine

    Returns:
        ExplainableResult with full provenance chains

    Example:
        from modules.skill_analyzer import SkillAnalyzer
        from modules.explainability import explain_skill_intelligence

        skill_result = SkillAnalyzer().analyze(raw_data)
        explainable = explain_skill_intelligence(raw_data, skill_result)

        print(f"We believe: {explainable.summary}")
        for skill_name, skill in explainable.skill_assessment.items():
            print(f"  {skill_name}: {skill.level}")
            print(f"    Because: {skill.reasoning}")
    """
    engine = ExplainabilityEngine()
    return engine.explain(raw_data, skill_result)
