"""
Skill Aggregator
================
Aggregates signals into overall skill profiles.
Computes depth index, breadth score, and primary domains.
"""

import math
from typing import Optional
from modules.skill_analyzer.types import (
    DepthIndex,
    DomainProfile,
    SkillProfile,
    TechGraph,
)


class SkillAggregator:
    """Aggregates skill signals into comprehensive profiles."""

    def __init__(self):
        # Thresholds for depth categorization
        self.SPECIALIST_THRESHOLD = 0.6  # 60%+ in one tech
        self.BREADTH_THRESHOLD = 5  # 5+ different domains
        self.T_SHAPED_MIN_DEPTH = 0.4  # Min depth for T-shaped

    def aggregate(
        self,
        languages: dict[str, float],
        frameworks: list[str],
        infrastructure: list[str],
        domains: list[DomainProfile],
        tech_graph: TechGraph,
        repo_analyses: list[dict],
        aggregates: Optional[dict] = None,
    ) -> SkillProfile:
        """
        Aggregate skill signals into a comprehensive profile.

        Args:
            languages: Language depth scores (0-1)
            frameworks: Detected frameworks
            infrastructure: Detected infrastructure tools
            domains: Detected domain profiles
            tech_graph: Technology relationship graph
            repo_analyses: Individual repo analysis results
            aggregates: Optional pre-computed aggregates from harvest

        Returns:
            Comprehensive SkillProfile
        """
        aggregates = aggregates or {}

        # Calculate depth index
        depth_index = self._calculate_depth_index(languages)

        # Identify primary and secondary domains
        primary_domains, secondary_domains = self._categorize_domains(domains)

        # Estimate experience
        years_experience = self._estimate_experience(
            languages, frameworks, repo_analyses, aggregates
        )

        # Check organization readiness
        org_ready = self._check_organization_ready(
            frameworks, infrastructure, repo_analyses, aggregates
        )

        # Identify growth indicators
        growth_indicators = self._identify_growth_indicators(
            languages, frameworks, domains, repo_analyses, aggregates
        )

        return SkillProfile(
            primary_domains=primary_domains,
            secondary_domains=secondary_domains,
            depth_index=depth_index,
            skill_level="",  # Set by level classifier
            skill_level_confidence=0.0,  # Set by level classifier
            tech_graph=tech_graph,
            modernity_score=tech_graph,  # Placeholder
            years_experience_estimate=years_experience,
            organization_ready=org_ready,
            growth_indicators=growth_indicators,
        )

    def _calculate_depth_index(self, languages: dict[str, float]) -> DepthIndex:
        """Calculate depth vs breadth profile."""
        if not languages:
            return DepthIndex(
                specialist_language="",
                specialist_score=0.0,
                breadth_score=0.0,
                depth_category="unknown",
            )

        # Find specialist language
        max_lang = max(languages.items(), key=lambda x: x[1])
        specialist_language = max_lang[0]
        specialist_score = max_lang[1]

        # Calculate breadth score (how many technologies they use meaningfully)
        meaningful_techs = [lang for lang, score in languages.items() if score > 0.1]
        breadth_score = len(meaningful_techs)

        # Normalize breadth (0-10 scale)
        breadth_score = min(10, breadth_score / 2)

        # Categorize
        depth_category = self._categorize_depth(
            specialist_score, len(meaningful_techs)
        )

        return DepthIndex(
            specialist_language=specialist_language,
            specialist_score=specialist_score,
            breadth_score=round(breadth_score, 1),
            depth_category=depth_category,
        )

    def _categorize_depth(self, specialist_score: float, num_techs: int) -> str:
        """Categorize depth vs breadth profile."""
        if specialist_score >= self.SPECIALIST_THRESHOLD and num_techs <= 3:
            return "specialist"
        elif specialist_score >= self.T_SHAPED_MIN_DEPTH and num_techs <= 6:
            return "t-shaped"
        elif num_techs >= self.BREADTH_THRESHOLD and specialist_score < 0.4:
            return "generalist"
        elif num_techs >= self.BREADTH_THRESHOLD and specialist_score >= 0.4:
            return "deep-generalist"
        else:
            return "balanced"

    def _categorize_domains(
        self, domains: list[DomainProfile]
    ) -> tuple[list[str], list[str]]:
        """Categorize domains into primary and secondary."""
        if not domains:
            return [], []

        # Sort by confidence
        sorted_domains = sorted(domains, key=lambda x: x.confidence, reverse=True)

        primary = []
        secondary = []

        for domain in sorted_domains:
            if domain.confidence >= 0.7:
                primary.append(domain.domain)
            elif domain.confidence >= 0.4:
                secondary.append(domain.domain)

        # Limit primary to top 3
        primary = primary[:3]
        # Limit secondary to next 3
        secondary = secondary[:3]

        return primary, secondary

    def _estimate_experience(
        self,
        languages: dict[str, float],
        frameworks: list[str],
        repo_analyses: list[dict],
        aggregates: Optional[dict] = None,
    ) -> int:
        """Estimate years of experience based on signals."""
        aggregates = aggregates or {}
        years = 0

        # Language diversity suggests experience
        num_langs = len([l for l, s in languages.items() if s > 0.1])
        years += min(6, num_langs * 1.5)

        # Deep expertise in primary language adds years
        if languages:
            max_depth = max(languages.values()) if languages else 0
            if max_depth > 0.5:
                years += 3  # Deep specialist has been doing this a while

        # Framework maturity
        mature_frameworks = {"react", "vue", "angular", "django", "rails", "spring",
                           "kubernetes", "terraform", "postgres", "redis", "fastapi"}
        mature_count = len([f for f in frameworks if f.lower() in mature_frameworks])
        years += min(3, mature_count)

        # Repository complexity signals
        total_complexity = sum(
            r.get("complexity_score", 0) for r in repo_analyses
        )
        years += min(5, total_complexity // 20)

        # Use aggregates for more accurate estimation
        if aggregates:
            total_commits = aggregates.get("total_commits", 0)
            if total_commits > 100:
                years += min(3, int(math.log10(total_commits / 10)))

            total_prs = aggregates.get("total_prs", 0)
            if total_prs > 20:
                years += min(2, int(math.log10(total_prs)))

        # Impact bonus - high-star repos suggest established engineer
        total_stars = sum(r.get("stars", 0) for r in repo_analyses)
        if total_stars > 100:
            years += min(5, int(math.log10(total_stars + 1)))

        # Max reasonable estimate - legendary engineers get credit
        if total_stars > 10000:
            return min(40, years)  # Guido, Linus, etc.
        return min(25, max(3, years))

    def _check_organization_ready(
        self,
        frameworks: list[str],
        infrastructure: list[str],
        repo_analyses: list[dict],
        aggregates: Optional[dict] = None,
    ) -> bool:
        """Check if developer shows enterprise/organization readiness signals."""
        aggregates = aggregates or {}
        signals = 0

        # Has modern frameworks
        modern_frameworks = {"typescript", "fastapi", "nestjs", "react", "vue", "next.js"}
        if any(f.lower() in modern_frameworks for f in frameworks):
            signals += 1

        # Has infrastructure skills
        infra_tools = {"docker", "kubernetes", "ci/cd", "github-actions", "terraform"}
        if any(i.lower() in infra_tools for i in infrastructure):
            signals += 1

        # Use aggregates for maturity signals
        if aggregates:
            test_coverage = aggregates.get("test_coverage_ratio", 0)
            ci_usage = aggregates.get("ci_usage_ratio", 0)
            docker_usage = aggregates.get("docker_usage_ratio", 0)

            if test_coverage > 0.3:
                signals += 1
            if ci_usage > 0.3:
                signals += 1
            if docker_usage > 0.2:
                signals += 1

            # Has docs
            docs_ratio = aggregates.get("docs_ratio", 0)
            if docs_ratio > 0.3:
                signals += 1

        # Has documentation from repo analysis
        has_docs = any(
            "docs" in r.get("complexity_signals", {}).get("documentation", {}).get("signal", "")
            for r in repo_analyses
        )
        if has_docs:
            signals += 1

        # Has tests
        has_tests = any(
            "test" in r.get("complexity_signals", {}).get("test-coverage", {}).get("signal", "")
            for r in repo_analyses
        )
        if has_tests:
            signals += 1

        return signals >= 3

    def _identify_growth_indicators(
        self,
        languages: dict[str, float],
        frameworks: list[str],
        domains: list[DomainProfile],
        repo_analyses: list[dict],
        aggregates: Optional[dict] = None,
    ) -> list[str]:
        """Identify signals that show growth mindset."""
        aggregates = aggregates or {}
        indicators = []

        # Learning modern languages
        modern_langs = {"rust", "go", "typescript", "kotlin", "swift", "dart"}
        if any(l.lower() in modern_langs for l in languages.keys()):
            indicators.append("Adopts modern programming languages")

        # Multi-paradigm knowledge
        paradigms = set()
        if "python" in languages or "javascript" in languages:
            paradigms.add("multi-paradigm")
        if "rust" in languages or "go" in languages:
            paradigms.add("systems")
        if "haskell" in languages or "scala" in languages or "elixir" in languages:
            paradigms.add("functional")
        if len(paradigms) >= 2:
            indicators.append("Works across multiple programming paradigms")

        # ML/AI indicates learning emerging tech
        if any(d.domain in ["Machine Learning Engineering", "AI/LLM Engineering"]
               for d in domains):
            indicators.append("Invests in AI/ML skills")

        # Infrastructure indicates cloud-native thinking
        if any(i.lower() in {"kubernetes", "docker", "terraform"} for i in frameworks):
            indicators.append("Understands cloud-native infrastructure")

        # Recent activity shows active development
        recent_repos = [r for r in repo_analyses if r.get("recency_score", 0) > 0.5]
        if len(recent_repos) >= 2:
            indicators.append("Maintains multiple active projects")

        # Open source contributions (implied by star count)
        impactful_repos = [r for r in repo_analyses
                         if r.get("impact", {}).get("stars", 0) > 50]
        if impactful_repos:
            indicators.append("Produces impactful open source work")

        # Use aggregates for additional signals
        if aggregates:
            # Consistent contributions
            total_commits = aggregates.get("total_commits", 0)
            if total_commits > 100:
                indicators.append(f"Consistent contributor ({total_commits}+ commits)")

            # Community engagement
            total_prs = aggregates.get("total_prs", 0)
            if total_prs > 10:
                indicators.append(f"Active in open source community ({total_prs}+ PRs)")

            # Modern engineering practices
            ci_usage = aggregates.get("ci_usage_ratio", 0)
            if ci_usage > 0.5:
                indicators.append("Follows modern CI/CD practices")

        return indicators[:5]  # Limit to top 5

    def compute_language_depth(
        self,
        lang_bytes: dict[str, int],
    ) -> dict[str, float]:
        """
        Compute normalized language depth scores from raw bytes.

        Args:
            lang_bytes: Dict of language -> bytes

        Returns:
            Dict of language -> depth score (0-1)
        """
        if not lang_bytes:
            return {}

        total_bytes = sum(lang_bytes.values())
        if total_bytes == 0:
            return {}

        # Languages to de-prioritize (UI/web markup that can skew results)
        deprioritize = {"HTML", "CSS", "SCSS", "Sass", "Less", "Stylus", "Vue", "SVG", "XML"}
        prioritize_boost = {"Python", "C", "C++", "Rust", "Go", "Java", "TypeScript", "JavaScript", "C#"}

        log_term = math.log(1 + total_bytes)
        depth_scores: dict[str, float] = {}

        for lang, bytes_in_lang in lang_bytes.items():
            if bytes_in_lang > 0:
                proportion = bytes_in_lang / total_bytes
                depth = proportion * log_term

                # Apply multipliers
                if lang in deprioritize:
                    depth *= 0.3  # Reduce weight of UI languages
                elif lang in prioritize_boost:
                    depth *= 1.5  # Boost core programming languages

                depth_scores[lang] = depth

        if not depth_scores:
            return {}

        # Min-max normalization
        min_depth = min(depth_scores.values())
        max_depth = max(depth_scores.values())

        if max_depth > min_depth:
            for lang in depth_scores:
                depth_scores[lang] = (depth_scores[lang] - min_depth) / (max_depth - min_depth)
        else:
            for lang in depth_scores:
                depth_scores[lang] = 1.0

        return {k: round(v, 4) for k, v in depth_scores.items()}


def aggregate_skills(
    languages: dict[str, float],
    frameworks: list[str],
    infrastructure: list[str],
    domains: list[DomainProfile],
    tech_graph: TechGraph,
    repo_analyses: list[dict],
    aggregates: Optional[dict] = None,
) -> SkillProfile:
    """
    Convenience function to aggregate skill signals.

    Args:
        languages: Language depth scores
        frameworks: Detected frameworks
        infrastructure: Detected infrastructure
        domains: Detected domains
        tech_graph: Technology graph
        repo_analyses: Repo analysis results
        aggregates: Optional pre-computed aggregates

    Returns:
        Aggregated SkillProfile
    """
    aggregator = SkillAggregator()
    return aggregator.aggregate(
        languages, frameworks, infrastructure, domains, tech_graph, repo_analyses, aggregates
    )
