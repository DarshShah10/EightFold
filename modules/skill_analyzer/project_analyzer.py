"""
Project Analyzer
=================
Analyzes individual repositories for complexity, impact, and skill signals.
"""

import math
from datetime import datetime, timezone
from typing import Optional
from modules.skill_analyzer.types import ProjectImpact


# =============================================================================
# COMPLEXITY SIGNAL PATTERNS
# =============================================================================

# Indicators of project complexity
COMPLEXITY_INDICATORS = {
    # Architecture patterns
    r"\/api\/": {"signal": "api-endpoints", "weight": 2},
    r"\/services?\/": {"signal": "service-layer", "weight": 2},
    r"\/core\/": {"signal": "core-domain", "weight": 3},
    r"\/domain\/": {"signal": "ddd-architecture", "weight": 4},
    r"\/entities\/": {"signal": "entity-modeling", "weight": 2},
    r"\/middleware\/": {"signal": "middleware", "weight": 2},
    r"\/plugins?\/": {"signal": "plugin-architecture", "weight": 3},
    r"\/extensions?\/": {"signal": "extensible-design", "weight": 3},
    r"\/adapters?\/": {"signal": "adapter-pattern", "weight": 2},
    r"\/drivers?\/": {"signal": "driver-layer", "weight": 2},

    # ML/Data patterns
    r"\/models?\/": {"signal": "model-layer", "weight": 3},
    r"\/training\/": {"signal": "training-pipeline", "weight": 3},
    r"\/inference\/": {"signal": "inference-pipeline", "weight": 3},
    r"\/features?\/": {"signal": "feature-engineering", "weight": 3},
    r"\/datasets?\/": {"signal": "dataset-management", "weight": 2},
    r"\/notebooks?\/": {"signal": "notebooks", "weight": 2},

    # Infrastructure patterns
    r"\/deployments?\/": {"signal": "deployment-config", "weight": 2},
    r"\/kubernetes\/": {"signal": "k8s-config", "weight": 3},
    r"\/helm\/": {"signal": "helm-charts", "weight": 3},
    r"\/terraform\/": {"signal": "terraform-iac", "weight": 3},
    r"\/ci\/": {"signal": "ci-config", "weight": 2},
    r"\/scripts\/": {"signal": "automation-scripts", "weight": 2},

    # Testing patterns
    r"\/tests?\/": {"signal": "test-coverage", "weight": 2},
    r"\/__tests?__\/": {"signal": "test-coverage", "weight": 2},
    r"\/fixtures?\/": {"signal": "test-fixtures", "weight": 2},
    r"\/mocks?\/": {"signal": "mocking", "weight": 2},

    # Documentation patterns
    r"\/docs?\/": {"signal": "documentation", "weight": 1},
    r"\/examples?\/": {"signal": "examples", "weight": 2},
    r"\/tutorials?\/": {"signal": "tutorials", "weight": 2},
}

# High-impact project indicators
IMPACT_INDICATORS = {
    # Popular libraries
    r"^react$": 10,
    r"^vue$": 8,
    r"^angular$": 7,
    r"^pytorch$": 10,
    r"^tensorflow$": 10,
    r"^fastapi$": 8,
    r"^scikit-learn$": 8,
    r"^requests$": 7,
    r"^express$": 7,
    r"^lodash$": 7,
    r"^moment$": 6,

    # Popular tools
    r"^eslint$": 8,
    r"^prettier$": 8,
    r"^webpack$": 7,
    r"^babel$": 7,
    r"^vite$": 8,

    # Historical/legendary projects
    r"^abc$": 50,  # ABC language - foundational
    r"^mypy": 30,  # Type checker for Python
    r"^python": 20,  # Python-related projects
    r"^django$": 15,
    r"^flask$": 15,
    r"^pandas$": 20,
    r"^numpy$": 20,
    r"^CPython": 30,  # Python implementation

    # Impact keywords
    r"framework": 3,
    r"library": 3,
    r"sdk": 4,
    r"cli": 3,
    r"tool": 2,
    r"generator": 3,
    r"starter": 3,
    r"template": 2,
    r"boilerplate": 3,
    r"parser": 5,
    r"compiler": 5,
    r"interpreter": 5,
}

# Stars thresholds for different project types
STAR_THRESHOLDS = {
    "library": 1000,  # Libraries need fewer stars to be considered impactful
    "framework": 500,
    "tool": 500,
    "application": 2000,
    "documentation": 100,
}


class ProjectAnalyzer:
    """Analyzes individual repositories."""

    def analyze_repo(
        self,
        repo: dict,
        file_paths: Optional[list[str]] = None,
        repo_branches: Optional[list[dict]] = None,
        repo_releases: Optional[list[dict]] = None,
    ) -> dict:
        """
        Analyze a single repository.

        Args:
            repo: Repository data dictionary
            file_paths: Optional list of file paths in repo
            repo_branches: Optional list of branches for this repo
            repo_releases: Optional list of releases for this repo

        Returns:
            Analysis result with complexity, impact, and signals
        """
        # Basic metrics - handle different field names
        stars = repo.get("stargazers_count", repo.get("stargazers", 0)) or 0
        forks = repo.get("forks_count", repo.get("forks", 0)) or 0
        watchers = repo.get("watchers_count", repo.get("watchers", 0)) or 0
        size = repo.get("size", 0) or 0

        # Age calculation
        created_at = repo.get("created_at", "")
        age_days = self._calculate_age_days(created_at)

        # Activity signals
        pushed_at = repo.get("pushed_at", "")
        last_activity_days = self._calculate_age_days(pushed_at)

        # Complexity signals
        complexity_signals = self._extract_complexity_signals(file_paths or [])

        # Impact calculation
        impact = self._calculate_impact(
            stars=stars,
            forks=forks,
            watchers=watchers,
            repo_name=repo.get("name", ""),
            description=repo.get("description", ""),
            age_days=age_days,
        )

        # Project type inference
        project_type = self._infer_project_type(
            repo.get("name", ""),
            repo.get("description", ""),
            file_paths or [],
        )

        # Calculate recency score
        recency_score = self._calculate_recency_score(last_activity_days)

        return {
            "name": repo.get("name", ""),
            "full_name": repo.get("full_name", ""),
            "impact": impact.__dict__,
            "complexity_signals": complexity_signals,
            "complexity_score": sum(s["weight"] for s in complexity_signals.values()),
            "project_type": project_type,
            "recency_score": recency_score,
            "age_days": age_days,
            "last_activity_days": last_activity_days,
            "stars": stars,
            "forks": forks,
            "size": size,
            "topics": repo.get("topics", []) or [],
            "language": repo.get("language"),
            "description": repo.get("description"),
            "has_issues": repo.get("has_issues", False),
            "has_wiki": repo.get("has_wiki", False),
            "is_archived": repo.get("is_archived", False),
            # Release and branch info
            "release_count": len(repo_releases) if repo_releases else 0,
            "branch_count": len(repo_branches) if repo_branches else 0,
            "has_protected_branches": any(b.get("is_protected", False) for b in (repo_branches or [])),
        }

    def _calculate_age_days(self, date_str: str) -> int:
        """Calculate age in days from ISO date string."""
        if not date_str:
            return 0

        try:
            # Handle ISO format
            date_str = date_str.replace("Z", "+00:00")
            created = datetime.fromisoformat(date_str.replace("T", " ").split("+")[0])
            now = datetime.now(timezone.utc)
            return (now - created).days
        except (ValueError, TypeError):
            return 0

    def _extract_complexity_signals(self, file_paths: list[str]) -> dict:
        """Extract architectural complexity signals from file paths."""
        signals: dict[str, dict] = {}

        for file_path in file_paths:
            path_lower = file_path.lower()

            for pattern, info in COMPLEXITY_INDICATORS.items():
                if pattern.lower() in path_lower:
                    signal_name = info["signal"]
                    if signal_name not in signals:
                        signals[signal_name] = {
                            "signal": signal_name,
                            "weight": info["weight"],
                            "count": 0,
                        }
                    signals[signal_name]["count"] += 1

        return signals

    def _calculate_impact(
        self,
        stars: int,
        forks: int,
        watchers: int,
        repo_name: str,
        description: str,
        age_days: int,
    ) -> ProjectImpact:
        """Calculate project impact score."""
        # Base impact from engagement
        engagement_score = math.log1p(stars) + 0.5 * math.log1p(forks) + 0.3 * math.log1p(watchers)

        # Impact bonus for popular library names
        name_lower = repo_name.lower()
        for pattern, bonus in IMPACT_INDICATORS.items():
            if pattern in name_lower:
                engagement_score += bonus

        # Description bonus
        desc_lower = description.lower() if description else ""
        for pattern, bonus in IMPACT_INDICATORS.items():
            if pattern in desc_lower:
                engagement_score += bonus * 0.5

        # Normalize to 0-100
        impact_score = min(100, engagement_score * 2)

        # Recency weight (recent projects get higher weight)
        recency_weight = 1.0
        if age_days > 365:
            years = age_days / 365
            recency_weight = max(0.3, 1.0 - (years - 1) * 0.1)

        # Community score
        community_score = 0.0
        if stars > 0:
            # Fork ratio indicates community contribution
            fork_ratio = forks / stars if stars > 0 else 0
            community_score = min(100, (fork_ratio * 50 + math.log1p(stars) * 2))

        return ProjectImpact(
            stars=stars,
            forks=forks,
            watchers=watchers,
            impact_score=round(impact_score, 1),
            recency_weight=round(recency_weight, 2),
            community_score=round(community_score, 1),
        )

    def _infer_project_type(
        self,
        name: str,
        description: str,
        file_paths: list[str],
    ) -> str:
        """Infer the type of project."""
        combined = f"{name} {description}".lower()
        paths_str = " ".join(file_paths).lower()

        # Check for specific types
        if any(p in combined for p in ["sdk", "library", "package", "framework"]):
            return "library/framework"
        if any(p in combined for p in ["cli", "tool", "utility"]):
            return "tool"
        if any(p in combined for p in ["web", "app", "application", "dashboard"]):
            return "application"
        if any(p in paths_str for p in ["models", "training", "inference", "notebooks"]):
            return "ml-project"
        if any(p in paths_str for p in ["kubernetes", "helm", "terraform"]):
            return "infrastructure"
        if any(p in combined for p in ["bot", "automation", "script"]):
            return "automation"
        if any(p in combined for p in ["plugin", "extension", "integration"]):
            return "plugin"
        if any(p in combined for p in ["docs", "documentation", "wiki"]):
            return "documentation"
        if any(p in combined for p in ["config", "dotfiles", "setup"]):
            return "configuration"
        if any(p in combined for p in ["template", "starter", "boilerplate"]):
            return "template"

        return "application"  # Default

    def _calculate_recency_score(self, days_since_activity: int) -> float:
        """Calculate recency score based on last activity."""
        if days_since_activity == 0:
            return 1.0
        elif days_since_activity < 30:
            return 0.9
        elif days_since_activity < 90:
            return 0.7
        elif days_since_activity < 180:
            return 0.5
        elif days_since_activity < 365:
            return 0.3
        else:
            return 0.1

    def rank_repos_by_impact(self, repo_analyses: list[dict]) -> list[dict]:
        """
        Rank repositories by impact.

        Args:
            repo_analyses: List of repo analysis results

        Returns:
            Sorted list with rank information
        """
        # Score each repo
        scored_repos = []
        for repo in repo_analyses:
            impact = repo.get("impact", {})
            impact_score = impact.get("impact_score", 0)

            # Weight by recency
            recency = repo.get("recency_score", 1.0)
            complexity = repo.get("complexity_score", 0)

            # Final score
            final_score = (
                impact_score * 0.5 +
                recency * 100 * 0.3 +
                min(complexity * 2, 50) * 0.2
            )

            scored_repos.append({
                **repo,
                "final_score": round(final_score, 1),
            })

        # Sort by final score
        scored_repos.sort(key=lambda x: x["final_score"], reverse=True)

        # Add rank
        for i, repo in enumerate(scored_repos):
            repo["impact_rank"] = i + 1

        return scored_repos


def analyze_projects(
    repos: list[dict],
    branches_by_repo: Optional[dict[str, list[dict]]] = None,
    releases_by_repo: Optional[dict[str, list[dict]]] = None,
    aggregates: Optional[dict] = None,
) -> list[dict]:
    """
    Analyze multiple repositories.

    Args:
        repos: List of repository data
        branches_by_repo: Optional dict mapping repo name to branches
        releases_by_repo: Optional dict mapping repo name to releases
        aggregates: Optional pre-computed aggregates

    Returns:
        List of analysis results ranked by impact
    """
    analyzer = ProjectAnalyzer()
    analyses = []

    # Normalize branches format (could be dict or directly a list per repo)
    branches = branches_by_repo or {}
    releases = releases_by_repo or {}

    for repo in repos:
        repo_name = repo.get("name", "")
        full_name = repo.get("full_name", "")

        # Get branches/releases for this repo
        repo_branches = branches.get(full_name) or branches.get(repo_name) or []
        repo_releases = releases.get(full_name) or releases.get(repo_name) or []

        analysis = analyzer.analyze_repo(
            repo,
            repo_branches=repo_branches,
            repo_releases=repo_releases,
        )
        analyses.append(analysis)

    # Rank by impact
    ranked = analyzer.rank_repos_by_impact(analyses)
    return ranked
