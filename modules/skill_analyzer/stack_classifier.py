"""
Stack Modernity Classifier
==========================
Classifies technology stacks as modern vs legacy.
Provides modernity scores based on technology choices and patterns.
"""

from typing import Optional
from modules.skill_analyzer.types import StackModernity


# =============================================================================
# MODERNITY SCORING MATRIX
# =============================================================================

# Modern technologies (score: 0.8-1.0)
MODERN_TECHNOLOGIES = {
    # Languages
    "rust": 0.95,
    "go": 0.9,
    "typescript": 0.9,
    "kotlin": 0.85,
    "swift": 0.85,
    "dart": 0.85,
    "python": 0.8,  # Modern Python (3.10+)
    "julia": 0.9,
    "zig": 0.85,
    "gleam": 0.9,
    "elixir": 0.85,
    "gleam": 0.9,

    # Frontend
    "react": 0.85,
    "vue.js": 0.85,
    "svelte": 0.9,
    "solid": 0.9,
    "next.js": 0.9,
    "nuxt": 0.85,
    "remix": 0.9,
    "sveltekit": 0.9,
    "gatsby": 0.8,
    "vite": 0.95,
    "esbuild": 0.9,
    "swc": 0.9,
    "turbopack": 0.95,
    "tailwindcss": 0.9,
    "radix-ui": 0.9,
    "shadcn": 0.9,
    "radix": 0.9,

    # Backend
    "fastapi": 0.9,
    "nestjs": 0.85,
    "fastify": 0.9,
    "gin": 0.9,
    "echo": 0.85,
    "axum": 0.9,
    "actix-web": 0.9,
    "spring-boot": 0.85,
    "quarkus": 0.9,
    "micronaut": 0.85,

    # Data/ML
    "pytorch": 0.9,
    "jax": 0.9,
    "huggingface": 0.9,
    "langchain": 0.9,
    "polars": 0.9,
    "duckdb": 0.9,
    "dbt": 0.85,
    "arrow": 0.9,
    "delta-lake": 0.85,
    "iceberg": 0.85,

    # Infrastructure
    "kubernetes": 0.85,
    "docker": 0.8,
    "terraform": 0.85,
    "opentelemetry": 0.9,
    "vault": 0.85,
    "argocd": 0.9,
    "flux": 0.85,
    "cilium": 0.9,
    "istio": 0.85,
    "linkerd": 0.85,
    "temporal": 0.9,
    "knative": 0.85,

    # Observability
    "prometheus": 0.85,
    "grafana": 0.85,
    "loki": 0.85,
    "tempo": 0.85,
    "otel": 0.9,

    # AI/ML Tools
    "vllm": 0.9,
    "ollama": 0.9,
    "llamaindex": 0.9,
    "weaviate": 0.85,
    "pinecone": 0.85,
    "chroma": 0.85,
    "milvus": 0.85,

    # Databases
    "postgresql": 0.8,
    "planetscale": 0.9,
    "supabase": 0.85,
    "neon": 0.9,
    "turso": 0.9,
    "cockroachdb": 0.85,
    "tidb": 0.85,
    "clickhouse": 0.85,
}

# Legacy technologies (score: 0.1-0.4)
LEGACY_TECHNOLOGIES = {
    # Languages
    "php": 0.3,
    "perl": 0.2,
    "coffeescript": 0.2,
    "coffeescript": 0.2,
    "actionscript": 0.15,
    "vb.net": 0.3,
    "objective-c": 0.35,
    "cobol": 0.1,
    "fortran": 0.15,
    "pascal": 0.15,

    # Frontend
    "angular.js": 0.2,
    "backbone.js": 0.2,
    "ember.js": 0.25,
    "jquery": 0.25,
    "grunt": 0.2,
    "bower": 0.15,
    "requirejs": 0.2,
    "webpack": 0.5,  # Transitional - still common but declining
    "gulp": 0.3,
    "sass": 0.4,  # Transitional
    "less": 0.35,

    # Backend
    "express": 0.5,  # Transitional - still common but Express vs Fastify
    "rails": 0.4,  # Transitional
    "django": 0.6,  # Still relevant but not cutting edge
    "flask": 0.5,
    "spring": 0.5,  # vs Spring Boot
    "struts": 0.15,
    "laravel": 0.45,
    "codeigniter": 0.2,

    # Databases
    "mysql": 0.5,  # Still common but PostgreSQL is more modern choice
    "mongodb": 0.6,  # Still common but newer DBs available
    "sqlite": 0.6,  # Good for embedded but not for scale
    "redis": 0.7,  # Still relevant but some patterns changed
    "memcached": 0.3,

    # Infrastructure
    "jenkins": 0.5,  # Transitional - GitHub Actions more modern
    "travis-ci": 0.3,
    "circleci": 0.65,  # Transitional
    "chef": 0.3,
    "puppet": 0.25,
    "consul": 0.7,  # Transitional
}

# Modern practices/patterns (bonus points)
MODERN_PRACTICES = {
    "typescript": 0.15,  # Type safety
    "testing": 0.1,  # Has tests
    "ci/cd": 0.1,  # Has CI/CD
    "docker": 0.1,  # Containerization
    "kubernetes": 0.15,  # Orchestration
    "openapi": 0.1,  # API documentation
    "graphql": 0.1,  # Modern API paradigm
    "grpc": 0.1,  # Modern RPC
    "terraform": 0.1,  # IaC
    "opentelemetry": 0.1,  # Observability standard
    "oauth": 0.1,  # Modern auth
    "jwt": 0.05,  # Token auth
    "zero-trust": 0.1,  # Security pattern
}

# Legacy patterns (negative points)
LEGACY_PRACTICES = {
    "jquery": -0.15,
    "angular.js": -0.2,
    "backbone": -0.15,
    "requirejs": -0.1,
    "gulp": -0.1,
    "grunt": -0.15,
    "bower": -0.1,
    "monolith": -0.1,
    "spa-monolith": -0.1,
}


class StackModernityClassifier:
    """Classifies technology stack modernity."""

    def __init__(self):
        self.modern_techs = MODERN_TECHNOLOGIES
        self.legacy_techs = LEGACY_TECHNOLOGIES
        self.modern_practices = MODERN_PRACTICES
        self.legacy_practices = LEGACY_PRACTICES

    def classify(
        self,
        technologies: list[str],
        repo_structure: Optional[dict] = None,
        has_tests: bool = False,
        has_ci: bool = False,
        has_docker: bool = False,
    ) -> StackModernity:
        """
        Classify stack modernity.

        Args:
            technologies: List of technologies
            repo_structure: Optional repo structure info
            has_tests: Whether the repo has tests
            has_ci: Whether the repo has CI
            has_docker: Whether the repo has Docker

        Returns:
            StackModernity with scores and signals
        """
        tech_set = {t.lower() for t in technologies}

        # Calculate base scores
        age_scores: list[float] = []
        ecosystem_scores: list[float] = []
        signals: list[str] = []
        warnings: list[str] = []

        for tech in technologies:
            tech_lower = tech.lower()

            if tech_lower in self.modern_techs:
                age_scores.append(self.modern_techs[tech_lower])
            elif tech_lower in self.legacy_techs:
                age_scores.append(self.legacy_techs[tech_lower])
                warnings.append(f"Legacy technology: {tech}")

        # Calculate ecosystem alignment
        ecosystem_patterns = self._detect_ecosystem_patterns(tech_set)
        for pattern, score in ecosystem_patterns.items():
            ecosystem_scores.append(score)
            signals.append(f"Ecosystem alignment: {pattern}")

        # Calculate pattern scores
        pattern_scores: list[float] = []
        if has_tests:
            pattern_scores.append(self.modern_practices["testing"])
            signals.append("Has test coverage")
        if has_ci:
            pattern_scores.append(self.modern_practices["ci/cd"])
            signals.append("Has CI/CD")
        if has_docker:
            pattern_scores.append(self.modern_practices["docker"])
            signals.append("Uses containerization")

        # Check for modern practices in technologies
        for tech in technologies:
            tech_lower = tech.lower()
            if tech_lower == "typescript":
                pattern_scores.append(self.modern_practices["typescript"])
                signals.append("Uses TypeScript (type safety)")
            if tech_lower == "graphql":
                pattern_scores.append(self.modern_practices["graphql"])
                signals.append("Uses GraphQL")
            if tech_lower == "grpc":
                pattern_scores.append(self.modern_practices["grpc"])
                signals.append("Uses gRPC")
            if tech_lower == "opentelemetry":
                pattern_scores.append(self.modern_practices["opentelemetry"])
                signals.append("Uses OpenTelemetry")

        # Calculate final scores
        age_score = sum(age_scores) / len(age_scores) if age_scores else 0.5
        ecosystem_score = sum(ecosystem_scores) / len(ecosystem_scores) if ecosystem_scores else 0.5
        patterns_score = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 0.5 if (has_tests or has_ci or has_docker) else 0.3

        # Overall score is weighted average
        overall = (
            age_score * 0.5 +
            ecosystem_score * 0.3 +
            patterns_score * 0.2
        )

        # Normalize to 0-100
        overall = max(0, min(100, overall * 100))
        age_score *= 100
        ecosystem_score *= 100
        patterns_score *= 100

        return StackModernity(
            overall_score=round(overall, 1),
            age_score=round(age_score, 1),
            ecosystem_score=round(ecosystem_score, 1),
            patterns_score=round(patterns_score, 1),
            signals=signals,
            warnings=warnings,
        )

    def _detect_ecosystem_patterns(self, tech_set: set[str]) -> dict[str, float]:
        """Detect modern ecosystem patterns."""
        patterns: dict[str, float] = {}

        # Cloud Native pattern
        cloud_native = {"kubernetes", "docker", "prometheus", "grafana"}
        if tech_set.intersection(cloud_native):
            patterns["Cloud Native"] = 0.9

        # Modern Frontend pattern
        modern_frontend = {"react", "typescript", "vite", "tailwindcss"}
        if tech_set.intersection(modern_frontend):
            patterns["Modern Frontend"] = 0.9

        # Modern Backend pattern
        modern_backend = {"go", "rust", "fastapi", "postgres"}
        if tech_set.intersection(modern_backend):
            patterns["Modern Backend"] = 0.9

        # AI/ML pattern
        ai_ml = {"pytorch", "huggingface", "langchain", "numpy"}
        if tech_set.intersection(ai_ml):
            patterns["AI/ML"] = 0.9

        # Serverless pattern
        serverless = {"aws-lambda", "azure-functions", "cloud-functions", "vercel", "netlify"}
        if tech_set.intersection(serverless):
            patterns["Serverless"] = 0.85

        # Platform Engineering pattern
        platform = {"kubernetes", "helm", "argocd", "opentelemetry"}
        if tech_set.intersection(platform):
            patterns["Platform Engineering"] = 0.9

        # Data Engineering pattern
        data_eng = {"spark", "kafka", "airflow", "dbt"}
        if tech_set.intersection(data_eng):
            patterns["Data Engineering"] = 0.85

        # Observability pattern
        observability = {"prometheus", "grafana", "loki", "tempo"}
        if tech_set.intersection(observability):
            patterns["Observability"] = 0.9

        return patterns

    def get_modernity_recommendations(self, technologies: list[str]) -> list[str]:
        """
        Get recommendations to improve stack modernity.

        Returns:
            List of recommendations
        """
        tech_set = {t.lower() for t in technologies}
        recommendations: list[str] = []

        # Check for type safety
        if "javascript" in tech_set and "typescript" not in tech_set:
            recommendations.append("Consider adding TypeScript for type safety")

        # Check for testing
        if not any(t.lower() in {"pytest", "jest", "vitest", "rspec", "minitest", "unittest"} for t in technologies):
            recommendations.append("Add test coverage with pytest, Jest, or similar")

        # Check for CI/CD
        if not any(t.lower() in {"github-actions", "gitlab-ci", "circleci", "jenkins", "travis"} for t in technologies):
            recommendations.append("Set up CI/CD pipeline with GitHub Actions or similar")

        # Check for containerization
        if "docker" not in tech_set:
            recommendations.append("Add Docker for consistent deployments")

        # Check for modern Python
        if "python" in tech_set and "fastapi" not in tech_set and "flask" in tech_set:
            recommendations.append("Consider FastAPI for modern Python API development")

        # Check for modern Node.js
        if "node.js" in tech_set and "express" in tech_set and "fastify" not in tech_set:
            recommendations.append("Consider Fastify for higher performance Node.js APIs")

        # Check for observability
        if "prometheus" not in tech_set and "datadog" not in tech_set:
            recommendations.append("Add Prometheus/Grafana for observability")

        return recommendations


def classify_modernity(
    technologies: list[str],
    has_tests: bool = False,
    has_ci: bool = False,
    has_docker: bool = False,
) -> StackModernity:
    """
    Convenience function to classify stack modernity.

    Args:
        technologies: List of technology names
        has_tests: Whether repos have tests
        has_ci: Whether repos have CI
        has_docker: Whether repos have Docker

    Returns:
        StackModernity result
    """
    classifier = StackModernityClassifier()
    return classifier.classify(technologies, has_tests=has_tests, has_ci=has_ci, has_docker=has_docker)
