"""
Skill Analyzer Engine
=====================
Main orchestrator for the Developer Skill Intelligence system.
Combines all analyzers to produce comprehensive skill profiles.

Enhanced to use ALL harvested data:
- repos: Project complexity, star impact
- lang_bytes: Language depth scores
- commits: Contribution patterns per repo
- issues: Community engagement signals
- branches: Branching strategy maturity
- releases: Release engineering maturity
- aggregates: Pre-computed metrics
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from modules.skill_analyzer.types import (
    DepthIndex,
    DomainProfile,
    SkillIntelligenceResult,
    SkillProfile,
    StackModernity,
    TechGraph,
)

from modules.skill_analyzer.tech_graph import (
    TechGraphBuilder,
    build_tech_graph,
    detect_stack_patterns,
)
from modules.skill_analyzer.skill_inferrer import (
    SkillInferrer,
    infer_skills,
)
from modules.skill_analyzer.domain_detector import (
    DomainDetector,
    detect_domains,
)
from modules.skill_analyzer.stack_classifier import (
    StackModernityClassifier,
    classify_modernity,
)
from modules.skill_analyzer.project_analyzer import (
    ProjectAnalyzer,
    analyze_projects,
)
from modules.skill_analyzer.skill_aggregator import (
    SkillAggregator,
    aggregate_skills,
)
from modules.skill_analyzer.levels import (
    SkillLevelInferrer,
    infer_skill_level,
)

logger = logging.getLogger(__name__)


class SkillAnalyzer:
    """
    State-of-the-art Developer Skill Intelligence Analyzer.

    Extracts 10+ signals to build comprehensive skill profiles:
    1. Tech Stack Graph - Technology relationships
    2. Semantic Skills - What developers actually built
    3. Domain Fingerprint - Problem spaces (ML, Web3, DevOps)
    4. Modernity Score - How current is their stack
    5. Depth Index - Specialist vs generalist profile
    6. Project Impact - Beyond stars - real significance
    7. Ecosystem Alignment - Enterprise tool alignment
    8. Learning Velocity - Tech adoption speed
    9. Skill Level - Junior/Mid/Senior inference
    10. Tech Maturity - Best practices signals
    """

    def __init__(self):
        """Initialize all sub-analyzers."""
        self.tech_graph_builder = TechGraphBuilder()
        self.skill_inferrer = SkillInferrer()
        self.domain_detector = DomainDetector()
        self.modernity_classifier = StackModernityClassifier()
        self.project_analyzer = ProjectAnalyzer()
        self.skill_aggregator = SkillAggregator()
        self.level_inferrer = SkillLevelInferrer()

    def analyze(
        self,
        raw_data: Dict[str, Any],
        jd_requirements: Optional[List[str]] = None,
    ) -> SkillIntelligenceResult:
        """
        Analyze GitHub data and produce skill intelligence.

        Args:
            raw_data: Dictionary containing harvested data with keys:
                - repos: List of repo dictionaries
                - lang_bytes: Dict of language -> bytes
                - commits: List of commit dictionaries
                - issues: List of issue dictionaries
                - pull_requests: List of PR dictionaries
                - branches: Dict of repo -> branch list
                - releases: Dict of repo -> release list
                - aggregates: Pre-computed aggregate metrics
            jd_requirements: Optional list of JD-required skills for matching

        Returns:
            SkillIntelligenceResult with comprehensive skill profile
        """
        logger.info("Starting skill intelligence analysis")

        # Extract all inputs
        repos = raw_data.get("repos", []) or []
        lang_bytes = raw_data.get("lang_bytes", {}) or {}
        commits = raw_data.get("commits", []) or []
        issues = raw_data.get("issues", []) or []
        pull_requests = raw_data.get("pull_requests", []) or []
        branches = raw_data.get("branches", {}) or {}
        releases = raw_data.get("releases", {}) or {}
        aggregates = raw_data.get("aggregates", {}) or {}

        logger.info(f"Using data: {len(repos)} repos, {len(commits)} commits, "
                   f"{len(issues)} issues, {len(pull_requests)} PRs")

        # Step 1: Compute language depth scores
        logger.info("Computing language depth scores")
        language_depth = self.skill_aggregator.compute_language_depth(lang_bytes)

        # Step 2: Build technology graph
        logger.info("Building technology relationship graph")
        all_technologies = self._extract_technologies(repos, language_depth)
        tech_graph = build_tech_graph(all_technologies)

        # Step 3: Infer semantic skills
        logger.info("Inferring semantic skills")
        skill_signals = infer_skills(repos, dependencies=[], file_paths=[])

        # Extract frameworks and infrastructure from skills
        frameworks = self._extract_frameworks(skill_signals, repos)
        infrastructure = self._extract_infrastructure(repos)

        # Step 4: Detect domains
        logger.info("Detecting problem domains")
        topics = self._extract_topics(repos)
        domains = detect_domains(all_technologies, topics, languages=language_depth)

        # Step 5: Analyze projects with enhanced data
        logger.info("Analyzing projects with commit and release data")
        repo_analyses = analyze_projects(repos, branches, releases, aggregates)

        # Step 6: Extract contribution patterns from commits
        logger.info("Analyzing contribution patterns")
        contribution_patterns = self._analyze_contribution_patterns(commits, repos)

        # Step 7: Extract community engagement from issues/PRs
        logger.info("Analyzing community engagement")
        community_signals = self._analyze_community_engagement(issues, pull_requests)

        # Step 8: Analyze release engineering maturity
        logger.info("Analyzing release engineering")
        release_maturity = self._analyze_release_engineering(releases, branches)

        # Step 9: Classify stack modernity using aggregates
        logger.info("Classifying stack modernity")
        modernity = self._classify_modernity_from_aggregates(
            all_technologies, frameworks, infrastructure, aggregates
        )

        # Step 10: Aggregate into skill profile
        logger.info("Aggregating skill profile")
        skill_profile = aggregate_skills(
            language_depth,
            frameworks,
            infrastructure,
            domains,
            tech_graph,
            repo_analyses,
            aggregates,
        )

        # Step 11: Enhance profile with commit/release/community data
        skill_profile = self._enhance_profile_with_engagement(
            skill_profile, contribution_patterns, community_signals, release_maturity
        )

        # Step 12: Infer skill level
        logger.info("Inferring skill level")
        level_signals = {
            "top_repos": repo_analyses,
            "infrastructure": infrastructure,
            "contribution_patterns": contribution_patterns,
            "community_signals": community_signals,
            "release_maturity": release_maturity,
        }
        level, level_confidence = infer_skill_level(skill_profile, level_signals)
        skill_profile.skill_level = level
        skill_profile.skill_level_confidence = level_confidence

        # Set modernity score
        skill_profile.modernity_score = modernity

        # Step 13: Generate insights
        logger.info("Generating insights")
        insights = self._generate_insights(
            skill_profile, domains, modernity, repo_analyses,
            contribution_patterns, community_signals
        )

        # Step 14: JD matching if provided
        jd_fit = None
        if jd_requirements:
            logger.info("Computing JD fit")
            jd_fit = self._compute_jd_fit(skill_profile, jd_requirements)

        # Build result
        result = SkillIntelligenceResult(
            skill_profile=skill_profile,
            signals=self._build_signals_dict(
                language_depth, frameworks, infrastructure, skill_profile,
                contribution_patterns, community_signals, release_maturity
            ),
            language_depth=language_depth,
            frameworks=frameworks,
            infrastructure=infrastructure,
            detected_domains=domains,
            insights=insights,
            top_repos=repo_analyses[:5],
            jd_fit=jd_fit,
        )

        logger.info(f"Skill analysis complete. Level: {level}, Domains: {skill_profile.primary_domains}")
        return result

    def _analyze_contribution_patterns(
        self,
        commits: list[dict],
        repos: list[dict]
    ) -> dict:
        """Analyze commit patterns to understand contribution style."""
        if not commits:
            return {}

        patterns = {
            "total_commits": len(commits),
            "unique_repos": len(set(c.get("repo_name", "") for c in commits)),
            "avg_files_per_commit": 0,
            "avg_size_per_commit": 0,
            "signed_ratio": 0,
            "commit_types": {},
            "merge_ratio": 0,
            "late_night_ratio": 0,
            "weekend_ratio": 0,
        }

        file_counts = []
        sizes = []
        signed_count = 0
        merge_count = 0
        late_night = 0
        weekend = 0

        type_counts = {}

        for commit in commits:
            files = commit.get("num_files", 0)
            if files > 0:
                file_counts.append(files)

            size = commit.get("total_lines", 0)
            if size > 0:
                sizes.append(size)

            if commit.get("verified", False):
                signed_count += 1

            if commit.get("is_merge", False):
                merge_count += 1

            hour = commit.get("hour_of_day")
            if hour is not None and (hour >= 22 or hour < 6):
                late_night += 1

            if commit.get("is_weekend", False):
                weekend += 1

            commit_type = commit.get("commit_type", "other")
            type_counts[commit_type] = type_counts.get(commit_type, 0) + 1

        total = len(commits)
        if total > 0:
            patterns["avg_files_per_commit"] = sum(file_counts) / len(file_counts) if file_counts else 0
            patterns["avg_size_per_commit"] = sum(sizes) / len(sizes) if sizes else 0
            patterns["signed_ratio"] = signed_count / total
            patterns["merge_ratio"] = merge_count / total
            patterns["late_night_ratio"] = late_night / total
            patterns["weekend_ratio"] = weekend / total
            patterns["commit_types"] = type_counts

        return patterns

    def _analyze_community_engagement(
        self,
        issues: list[dict],
        pull_requests: list[dict]
    ) -> dict:
        """Analyze issues and PRs for community engagement signals."""
        signals = {
            "issues_created": len(issues),
            "issues_closed": sum(1 for i in issues if i.get("state") == "closed"),
            "issues_closed_ratio": 0,
            "avg_issue_close_hours": 0,
            "prs_created": len(pull_requests),
            "prs_merged": sum(1 for pr in pull_requests if pr.get("merged", False)),
            "pr_merge_rate": 0,
            "avg_pr_time_to_merge_hours": 0,
            "avg_review_comments": 0,
            "community_engagement_score": 0,
        }

        if issues:
            closed = signals["issues_closed"]
            signals["issues_closed_ratio"] = closed / len(issues)

            close_times = [i.get("time_to_close_hours", 0) for i in issues if i.get("time_to_close_hours")]
            if close_times:
                signals["avg_issue_close_hours"] = sum(close_times) / len(close_times)

        if pull_requests:
            merged = signals["prs_merged"]
            signals["pr_merge_rate"] = merged / len(pull_requests) if pull_requests else 0

            merge_times = [pr.get("time_to_merge_hours", 0) for pr in pull_requests if pr.get("time_to_merge_hours")]
            if merge_times:
                signals["avg_pr_time_to_merge_hours"] = sum(merge_times) / len(merge_times)

            review_comments = [pr.get("num_review_comments", 0) for pr in pull_requests]
            if review_comments:
                signals["avg_review_comments"] = sum(review_comments) / len(review_comments)

        # Community engagement score (0-1)
        engagement_factors = [
            signals["prs_created"] > 5,
            signals["pr_merge_rate"] > 0.5,
            signals["avg_review_comments"] > 0,
            signals["issues_created"] > 0,
        ]
        signals["community_engagement_score"] = sum(engagement_factors) / len(engagement_factors)

        return signals

    def _analyze_release_engineering(
        self,
        releases: dict,
        branches: dict
    ) -> dict:
        """Analyze release engineering and branching strategy maturity."""
        maturity = {
            "repos_with_releases": 0,
            "total_releases": 0,
            "repos_with_branches": 0,
            "total_branches": 0,
            "protected_branches": 0,
            "release_engineering_score": 0,
            "branching_strategy_score": 0,
        }

        # Count releases
        for repo, repo_releases in releases.items():
            if repo_releases:
                maturity["repos_with_releases"] += 1
                maturity["total_releases"] += len(repo_releases)

        # Count branches
        for repo, repo_branches in branches.items():
            if repo_branches:
                maturity["repos_with_branches"] += 1
                maturity["total_branches"] += len(repo_branches)
                maturity["protected_branches"] += sum(1 for b in repo_branches if b.get("is_protected", False))

        total_repos = len(releases) if releases else 1
        maturity["release_engineering_score"] = maturity["repos_with_releases"] / total_repos
        maturity["branching_strategy_score"] = (
            (maturity["repos_with_branches"] / total_repos) * 0.5 +
            (maturity["protected_branches"] / max(1, maturity["total_branches"]) * 0.5)
        )

        return maturity

    def _classify_modernity_from_aggregates(
        self,
        technologies: list[str],
        frameworks: list[str],
        infrastructure: list[str],
        aggregates: dict
    ) -> StackModernity:
        """Classify stack modernity using pre-computed aggregates."""
        # Use aggregates for engineering maturity signals
        has_tests = aggregates.get("test_coverage_ratio", 0) > 0.3
        has_ci = aggregates.get("ci_usage_ratio", 0) > 0.3
        has_docker = aggregates.get("docker_usage_ratio", 0) > 0.3

        # Combine with tech detection
        all_techs = list(set(technologies + frameworks + infrastructure))

        return classify_modernity(
            all_techs,
            has_tests=has_tests,
            has_ci=has_ci,
            has_docker=has_docker,
        )

    def _enhance_profile_with_engagement(
        self,
        profile: SkillProfile,
        contribution_patterns: dict,
        community_signals: dict,
        release_maturity: dict
    ) -> SkillProfile:
        """Enhance skill profile with engagement and contribution data."""
        # This data is used in skill level inference
        # Add signals that indicate professional maturity

        if community_signals.get("community_engagement_score", 0) > 0.5:
            profile.organization_ready = True

        return profile

    def _extract_technologies(
        self, repos: list[dict], language_depth: dict[str, float]
    ) -> list[str]:
        """Extract all technologies from repos and languages."""
        technologies: set[str] = set()

        # Add languages
        for lang in language_depth.keys():
            technologies.add(lang)

        # Add from repo data
        for repo in repos:
            if repo.get("language"):
                technologies.add(repo["language"])

            topics = repo.get("topics", []) or []
            technologies.update(topics)

        return list(technologies)

    def _extract_frameworks(self, skill_signals: dict, repos: list[dict]) -> list[str]:
        """Extract framework names from skill signals and repo topics."""
        frameworks: set[str] = set()

        known_frameworks = {
            "fastapi", "django", "flask", "express", "nestjs", "fastify",
            "react", "vue", "angular", "svelte", "next.js", "nuxt",
            "rails", "spring", "spring-boot", "gin", "echo", "axum",
            "phoenix", "laravel", "codeigniter", "gatsby", "remix",
            "gatsby", "strapi", "prisma", "typeorm", "sequelize",
            "pytorch", "tensorflow", "keras", "fastai", "scikit-learn",
            "huggingface", "langchain", "transformers",
        }

        for skill in skill_signals.keys():
            for fw in known_frameworks:
                if fw.lower() in skill.lower():
                    frameworks.add(skill)

        for repo in repos:
            topics = repo.get("topics", []) or []
            for topic in topics:
                topic_lower = topic.lower()
                if any(fw in topic_lower for fw in known_frameworks):
                    frameworks.add(topic.title().replace("-", " ").replace("_", " "))

        return list(frameworks)

    def _extract_infrastructure(self, repos: list[dict]) -> list[str]:
        """Extract infrastructure tools from repos."""
        infra: set[str] = set()

        known_infra = {
            "docker", "kubernetes", "terraform", "ansible", "helm",
            "github-actions", "gitlab-ci", "jenkins", "circleci",
            "prometheus", "grafana", "datadog", "newrelic",
            "aws", "azure", "gcp", "vercel", "netlify",
            "nginx", "traefik", "istio", "linkerd",
            "vault", "consul", "etcd", "redis", "rabbitmq",
            "kafka", "nats", "docker-compose", "argocd", "flux",
        }

        for repo in repos:
            topics = repo.get("topics", []) or []
            for topic in topics:
                topic_lower = topic.lower()
                for i in known_infra:
                    if i in topic_lower:
                        infra.add(topic.title().replace("-", " ").replace("_", " "))

            description = (repo.get("description") or "").lower()
            for i in known_infra:
                if i in description:
                    infra.add(i.title())

        return list(infra)

    def _extract_topics(self, repos: list[dict]) -> list[str]:
        """Extract all unique topics from repos."""
        topics: set[str] = set()
        for repo in repos:
            repo_topics = repo.get("topics", []) or []
            topics.update(repo_topics)
        return list(topics)

    def _build_signals_dict(
        self,
        language_depth: dict[str, float],
        frameworks: list[str],
        infrastructure: list[str],
        profile: SkillProfile,
        contribution_patterns: dict = None,
        community_signals: dict = None,
        release_maturity: dict = None,
    ) -> dict[str, float]:
        """Build signals dictionary for scoring."""
        signals: dict[str, float] = {}

        # Language signals
        max_lang = max(language_depth.values()) if language_depth else 1
        for lang, depth in language_depth.items():
            signals[f"lang_{lang.lower()}"] = depth / max_lang if max_lang > 0 else 0

        # Framework signals
        signals["num_frameworks"] = min(1.0, len(frameworks) / 10)
        signals["has_frameworks"] = 1.0 if frameworks else 0.0

        # Infrastructure signals
        signals["num_infra_tools"] = min(1.0, len(infrastructure) / 10)
        signals["has_infra"] = 1.0 if infrastructure else 0.0

        # Domain signals
        for domain in profile.primary_domains:
            signals[f"domain_{domain.lower().replace(' ', '_')}"] = 0.8
        for domain in profile.secondary_domains:
            signals[f"domain_{domain.lower().replace(' ', '_')}"] = 0.5

        # Depth signals
        signals["depth_score"] = profile.depth_index.specialist_score
        signals["breadth_score"] = min(1.0, profile.depth_index.breadth_score / 10)

        # Level signal
        level_scores = {"Junior": 0.2, "Mid": 0.5, "Senior": 0.75, "Staff": 0.9, "Principal": 1.0}
        signals["skill_level_score"] = level_scores.get(profile.skill_level, 0.5)

        # Contribution patterns
        if contribution_patterns:
            signals["signed_commits_ratio"] = contribution_patterns.get("signed_ratio", 0)
            signals["merge_ratio"] = contribution_patterns.get("merge_ratio", 0)
            signals["weekend_work_ratio"] = contribution_patterns.get("weekend_ratio", 0)

        # Community signals
        if community_signals:
            signals["community_engagement"] = community_signals.get("community_engagement_score", 0)
            signals["pr_merge_rate"] = community_signals.get("pr_merge_rate", 0)

        # Release maturity
        if release_maturity:
            signals["release_engineering"] = release_maturity.get("release_engineering_score", 0)
            signals["branching_strategy"] = release_maturity.get("branching_strategy_score", 0)

        return signals

    def _generate_insights(
        self,
        profile: SkillProfile,
        domains: list[DomainProfile],
        modernity: StackModernity,
        repo_analyses: list[dict],
        contribution_patterns: dict = None,
        community_signals: dict = None,
    ) -> list[str]:
        """Generate actionable insights."""
        insights: list[str] = []

        # Primary domain insights
        if profile.primary_domains:
            insights.append(f"Primary expertise in {', '.join(profile.primary_domains[:2])}")

        # Depth insights
        if profile.depth_index.depth_category == "specialist":
            insights.append(f"Deep specialist in {profile.depth_index.specialist_language}")
        elif profile.depth_index.depth_category == "t-shaped":
            insights.append("T-shaped profile with depth in one area and breadth across others")
        elif profile.depth_index.depth_category == "generalist":
            insights.append("Broad generalist with experience across many technologies")

        # Modernity insights
        if modernity.overall_score >= 80:
            insights.append(f"Modern tech stack ({modernity.overall_score:.0f}%) with current best practices")
        elif modernity.overall_score < 50:
            if modernity.warnings:
                insights.append(f"Uses some legacy technologies: {', '.join(set(modernity.warnings))}")

        # Contribution insights
        if contribution_patterns:
            if contribution_patterns.get("signed_ratio", 0) > 0.5:
                insights.append("Consistently signs commits for security")
            if contribution_patterns.get("weekend_ratio", 0) > 0.3:
                insights.append("Active contributor including weekends")
            if contribution_patterns.get("avg_files_per_commit", 0) > 10:
                insights.append("Takes on complex, multi-file changes")

        # Community insights
        if community_signals:
            if community_signals.get("pr_merge_rate", 0) > 0.7:
                insights.append("High PR acceptance rate suggests quality contributions")
            if community_signals.get("avg_review_comments", 0) > 2:
                insights.append("Engages actively in code reviews")

        # Impact insights
        total_stars = sum(r.get("impact", {}).get("stars", 0) for r in repo_analyses)
        if total_stars > 10000:
            insights.append("High-impact open source contributions (10k+ stars)")
        elif total_stars > 1000:
            insights.append("Meaningful open source presence (1k+ stars)")

        # Infrastructure insights
        if profile.organization_ready:
            insights.append("Shows enterprise-ready engineering practices")

        return insights[:5]

    def _compute_jd_fit(
        self,
        profile: SkillProfile,
        jd_requirements: list[str],
    ) -> dict:
        """Compute fit with job description requirements."""
        matched = []
        missing = []
        partial = []

        all_skills = set()
        all_skills.update(profile.primary_domains)
        all_skills.update(profile.secondary_domains)

        for req in jd_requirements:
            req_lower = req.lower()
            matched_req = False
            for skill in all_skills:
                if req_lower in skill.lower() or skill.lower() in req_lower:
                    matched.append(req)
                    matched_req = True
                    break

            if not matched_req:
                related = [s for s in all_skills
                          if any(word in s.lower() for word in req_lower.split() if len(word) > 3)]
                if related:
                    partial.append({"requirement": req, "related": related})
                else:
                    missing.append(req)

        fit_score = len(matched) / len(jd_requirements) if jd_requirements else 0
        partial_score = len(partial) * 0.5 / len(jd_requirements) if jd_requirements else 0
        final_score = (fit_score + partial_score) * 100

        return {
            "score": round(final_score, 1),
            "matched": matched,
            "partial_matches": partial,
            "missing": missing,
            "summary": f"{len(matched)}/{len(jd_requirements)} requirements met",
        }


def analyze_skills(
    raw_data: Dict[str, Any],
    jd_requirements: Optional[List[str]] = None,
) -> SkillIntelligenceResult:
    """Convenience function to analyze skills."""
    analyzer = SkillAnalyzer()
    return analyzer.analyze(raw_data, jd_requirements)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import json

    sample_data = {
        "repos": [
            {
                "name": "awesome-ml-project",
                "full_name": "user/awesome-ml-project",
                "language": "Python",
                "stargazers": 500,
                "forks": 100,
                "topics": ["machine-learning", "python", "pytorch"],
                "description": "A production ML pipeline with PyTorch and Kubernetes",
            },
        ],
        "lang_bytes": {"Python": 80000, "TypeScript": 10000, "Go": 5000},
        "commits": [],
        "aggregates": {},
    }

    print("=" * 60)
    print("Testing Enhanced Skill Analyzer")
    print("=" * 60)

    result = analyze_skills(sample_data)

    print(f"\nSkill Level: {result.skill_profile.skill_level}")
    print(f"Confidence: {result.skill_profile.skill_level_confidence:.0%}")
    print(f"Primary Domains: {result.skill_profile.primary_domains}")
    print(f"Modernity Score: {result.skill_profile.modernity_score.overall_score:.1f}%")
    print(f"Insights: {result.insights}")
    print("\n" + "=" * 60)
