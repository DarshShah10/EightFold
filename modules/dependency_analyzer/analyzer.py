"""
Dependency Fingerprinting Analyzer
=================================
Analyzes dependency files to determine engineering philosophy and tech trends.
"""

from typing import Any, Dict, List, Optional
import re


# =============================================================================
# LIBRARY CLASSIFICATIONS
# =============================================================================

# Productivity-oriented libraries (speed over correctness)
PRODUCTIVITY_LIBRARIES = {
    "lodash", "underscore", "ramda", "moment", "date-fns", "dayjs",
    "axios", "request", "got", "node-fetch", "fetch",
    "jQuery", "zepto",
    "express", "koa", "fastify",
    "django", "flask", "rails", "laravel",
}

# Performance-oriented libraries
PERFORMANCE_LIBRARIES = {
    "numpy", "pandas", "scipy", "polars", "duckdb",
    "pytorch", "tensorflow", "jax", "torch",
    "rust", "tokio", "actix", "axum",
    "go", "fasthttp",
    "redis", "memcached", "rocksdb",
    "clickhouse", "duckdb", "polars",
    "esbuild", "swc", "vite", "bun",
}

# Research-grade libraries
RESEARCH_LIBRARIES = {
    "jupyter", "ipython", "jupyterlab",
    "numpy", "scipy", "sympy",
    "pandas", "statsmodels", "scikit-learn",
    "matplotlib", "plotly", "seaborn", "bokeh",
    "tensorflow", "pytorch", "jax",
    "networkx", "igraph",
    "beautifulsoup", "scrapy",
    "nltk", "spacy", "transformers",
}

# Production-grade libraries
PRODUCTION_LIBRARIES = {
    "sentry", "datadog", "newrelic", "prometheus", "grafana",
    "pagerduty", "opsgenie",
    "terraform", "ansible", "kubernetes", "helm",
    "docker", "docker-compose",
    "github-actions", "gitlab-ci", "jenkins",
    "aws", "azure", "gcp",
    "vault", "consul", "etcd",
    "argocd", "flux", "tekton",
    "opa", "falco", "trivy",
}

# Modern stack indicators
MODERN_LIBRARIES = {
    # TypeScript ecosystem
    "typescript", "ts-node", "tsx",
    "zod", "valibot", "yup",
    "prisma", "drizzle", "kysely",
    "trpc", "graphql-yoga", "nexus",
    "vite", "esbuild", "rollup",
    "vitest", "playwright", "testing-library",

    # Python modern
    "fastapi", "uvicorn", "pydantic",
    "httpx", "aiohttp", "anyio",
    "ruff", "mypy", "black",
    "poetry", "pdm", "rye",

    # Rust ecosystem
    "tokio", "serde", "tracing",
    "axum", "actix-web", "poem",
    "sqlx", "diesel",

    # Go modern
    "chi", "fiber", "echo",
    "slog", "zap", "zerolog",
}

# Legacy libraries
LEGACY_LIBRARIES = {
    "request", "node-fetch",  # Deprecated in favor of native fetch
    "mongoose",  # Mongoose vs Prisma
    "redux-thunk",  # Redux Toolkit now standard
    "class-transformer",  # Newer alternatives
    "moment",  # Day.js now preferred
    "underscore",  # Lodash or native now
    "bower",  # npm/yarn now standard
    "grunt",  # gulp/webpack now standard
    "gulp",  # npm scripts or webpack
    "jQuery",  # Modern frameworks now
    "angular.js",  # Angular 2+ now
    "backbone",  # React/Vue now standard
    "request-promise",  # async/await now standard
}


# =============================================================================
# ECOSYSTEM PATTERNS
# =============================================================================

ECOSYSTEM_PATTERNS = {
    "node": {
        "package_managers": ["package.json", "yarn.lock", "package-lock.json", "pnpm-lock.yaml"],
        "indicators": ["node_modules", "npm", "node.js"],
    },
    "python": {
        "package_managers": ["requirements.txt", "Pipfile", "pyproject.toml", "poetry.lock", "uv.lock"],
        "indicators": ["__pycache__", ".venv", "venv", "env"],
    },
    "rust": {
        "package_managers": ["Cargo.toml", "Cargo.lock"],
        "indicators": ["target/", "Cargo.lock"],
    },
    "go": {
        "package_managers": ["go.mod", "go.sum"],
        "indicators": ["vendor/", "go.sum"],
    },
    "java": {
        "package_managers": ["pom.xml", "build.gradle", "gradlew"],
        "indicators": ["target/", ".gradle"],
    },
    "mobile": {
        "package_managers": ["Podfile", "Podfile.lock", "pubspec.yaml", "pubspec.lock"],
        "indicators": ["Pods/", ".dart_tool"],
    },
}


class DependencyAnalyzer:
    """
    Analyzes dependency files to determine engineering philosophy.
    """

    def __init__(self):
        self.productivity_libs = PRODUCTIVITY_LIBRARIES
        self.performance_libs = PERFORMANCE_LIBRARIES
        self.research_libs = RESEARCH_LIBRARIES
        self.production_libs = PRODUCTION_LIBRARIES
        self.modern_libs = MODERN_LIBRARIES
        self.legacy_libs = LEGACY_LIBRARIES

    def analyze(
        self,
        raw_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze dependencies to determine engineering philosophy.

        Args:
            raw_data: Dictionary containing:
                - dep_files: Dict of dependency file content
                - repos: Optional list of repos for context

        Returns:
            Analysis results with philosophy scores and trends
        """
        dep_files = raw_data.get("dep_files", {})
        repos = raw_data.get("repos", []) or []

        # Parse all dependency files
        all_packages = self._parse_all_dependencies(dep_files)

        # Count library categories
        category_counts = self._count_categories(all_packages)

        # Calculate philosophy scores
        philosophy_scores = self._calculate_philosophy_scores(category_counts, len(all_packages))

        # Determine ecosystem alignment
        ecosystems = self._detect_ecosystems(dep_files)

        # Identify trends
        trends = self._identify_trends(all_packages, repos)

        # Build engineering philosophy summary
        philosophy = self._build_philosophy_summary(category_counts, ecosystems)

        return {
            "engineering_philosophy": philosophy,
            "philosophy_scores": philosophy_scores,
            "ecosystem": {
                "detected": list(ecosystems.keys()),
                "primary": max(ecosystems.keys(), default="unknown",
                             key=lambda k: ecosystems[k]),
            },
            "trends": trends,
            "libraries_detected": list(all_packages)[:50],  # Top 50
            "category_breakdown": category_counts,
            "summary": self._generate_summary(philosophy_scores, ecosystems, trends),
        }

    def _parse_all_dependencies(self, dep_files: Dict[str, Any]) -> set:
        """Parse all dependency files and extract package names."""
        packages = set()

        for file_name, content in dep_files.items():
            if not content:
                continue

            file_lower = file_name.lower()

            if "package.json" in file_lower:
                packages.update(self._parse_package_json(content))
            elif "requirements.txt" in file_lower or "pyproject.toml" in file_lower:
                packages.update(self._parse_python_deps(content))
            elif "cargo.toml" in file_lower:
                packages.update(self._parse_cargo_toml(content))
            elif "go.mod" in file_lower:
                packages.update(self._parse_go_mod(content))
            elif "pom.xml" in file_lower or "build.gradle" in file_lower:
                packages.update(self._parse_java_deps(content))
            elif "podfile" in file_lower:
                packages.update(self._parse_podfile(content))
            elif "pubspec.yaml" in file_lower:
                packages.update(self._parse_pubspec(content))

        return packages

    def _parse_package_json(self, content: str) -> set:
        """Parse npm/yarn package.json content."""
        packages = set()
        try:
            import json
            data = json.loads(content) if isinstance(content, str) else content

            # Dependencies
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})

            for pkg in list(deps.keys()) + list(dev_deps.keys()):
                # Extract base package name (handle scoped packages)
                base = pkg.split("/")[-1].split("@")[0]
                packages.add(base.lower())
        except:
            # Fallback to regex parsing
            for match in re.findall(r'"([^"]+)":\s*"[^"]+"', content):
                base = match.split("/")[-1].split("@")[0]
                packages.add(base.lower())
        return packages

    def _parse_python_deps(self, content: str) -> set:
        """Parse Python requirements.txt or pyproject.toml."""
        packages = set()
        for line in content.split("\n"):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Handle various formats
            pkg = re.split(r"[<>=!~]", line)[0].strip()
            pkg = pkg.replace("_", "-").lower()
            if pkg and not pkg.startswith("."):
                packages.add(pkg)
        return packages

    def _parse_cargo_toml(self, content: str) -> set:
        """Parse Rust Cargo.toml."""
        packages = set()
        in_deps = False
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("["):
                in_deps = "dependencies" in line or "dev-dependencies" in line
            elif in_deps and "=" in line:
                pkg = line.split("=")[0].strip().replace('"', '').replace("'", "")
                packages.add(pkg.lower())
        return packages

    def _parse_go_mod(self, content: str) -> set:
        """Parse Go go.mod."""
        packages = set()
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("require ("):
                continue
            if line.startswith(")"):
                break
            if "/" in line and not line.startswith("module"):
                pkg = line.split()[0] if " " in line else line
                packages.add(pkg.split("/")[-1].lower())
        return packages

    def _parse_java_deps(self, content: str) -> set:
        """Parse Java Maven/Gradle dependencies."""
        packages = set()
        for match in re.findall(r'[\'"]org\.apache\.(\w+)[\'"]|[\'"]com\.google\.(\w+)[\'"]', content):
            for g in match:
                if g:
                    packages.add(g.lower())
        for match in re.findall(r'name:\s*[\'"]([^\'"]+)[\'"]', content):
            packages.add(match.lower())
        return packages

    def _parse_podfile(self, content: str) -> set:
        """Parse iOS Podfile."""
        packages = set()
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("pod '"):
                pkg = line[4:].split("'")[0]
                packages.add(pkg.lower())
        return packages

    def _parse_pubspec(self, content: str) -> set:
        """Parse Flutter pubspec.yaml."""
        packages = set()
        in_deps = False
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("dependencies:"):
                in_deps = True
            elif line.startswith("dev_dependencies:"):
                in_deps = True
            elif line.startswith("sdks:") or line.startswith("flutter:"):
                continue
            elif line and not line.startswith("#") and ":" in line and in_deps:
                pkg = line.split(":")[0].strip()
                packages.add(pkg.lower())
        return packages

    def _count_categories(self, packages: set) -> Dict[str, int]:
        """Count packages in each category."""
        return {
            "productivity": len([p for p in packages if any(l.lower() in p for l in self.productivity_libs)]),
            "performance": len([p for p in packages if any(l.lower() in p for l in self.performance_libs)]),
            "research": len([p for p in packages if any(l.lower() in p for l in self.research_libs)]),
            "production": len([p for p in packages if any(l.lower() in p for l in self.production_libs)]),
            "modern": len([p for p in packages if any(l.lower() in p for l in self.modern_libs)]),
            "legacy": len([p for p in packages if any(l.lower() in p for l in self.legacy_libs)]),
        }

    def _calculate_philosophy_scores(
        self, counts: Dict[str, int], total: int
    ) -> Dict[str, float]:
        """Calculate philosophy scores based on library usage."""
        if total == 0:
            return {
                "pragmatism": 0.5,
                "performance_focus": 0.5,
                "research_grade": 0.5,
                "production_focus": 0.5,
                "modernity": 0.5,
            }

        p = counts.get("productivity", 0) / total
        perf = counts.get("performance", 0) / total
        research = counts.get("research", 0) / total
        prod = counts.get("production", 0) / total
        modern = counts.get("modern", 0) / total
        legacy = counts.get("legacy", 0) / total

        return {
            "pragmatism": round(p * 0.8 + perf * 0.2, 2),  # Prioritize getting things done
            "performance_focus": round(perf + research * 0.3, 2),  # Performance-conscious
            "research_grade": round(research * 1.5, 2),  # Research/academic work
            "production_focus": round(prod * 1.5, 2),  # Enterprise-ready
            "modernity": round(modern * 1.2 - legacy * 0.5, 2),  # Modern stack
        }

    def _detect_ecosystems(self, dep_files: Dict[str, Any]) -> Dict[str, int]:
        """Detect which ecosystems the project uses."""
        ecosystems = {}

        for file_name in dep_files.keys():
            file_lower = file_name.lower()
            for ecosystem, patterns in ECOSYSTEM_PATTERNS.items():
                if any(pm in file_lower for pm in patterns["package_managers"]):
                    ecosystems[ecosystem] = ecosystems.get(ecosystem, 0) + 1

        return ecosystems

    def _identify_trends(
        self, packages: set, repos: List[Dict]
    ) -> List[str]:
        """Identify technology trends from dependencies."""
        trends = []

        pkg_list = list(packages)

        # TypeScript adoption
        if any(p in pkg_list for p in ["typescript", "ts-node"]):
            trends.append("Adopts TypeScript for type safety")

        # Modern Python
        if any(p in pkg_list for p in ["fastapi", "pydantic", "uvicorn"]):
            trends.append("Uses modern Python stack (FastAPI)")

        # ML/AI
        if any(p in pkg_list for p in ["pytorch", "tensorflow", "transformers", "langchain"]):
            trends.append("Invests in ML/AI libraries")

        # Cloud-native
        if any(p in pkg_list for p in ["terraform", "kubernetes", "docker"]):
            trends.append("Follows cloud-native practices")

        # Observability
        if any(p in pkg_list for p in ["prometheus", "grafana", "sentry", "datadog"]):
            trends.append("Prioritizes observability")

        # Performance
        if any(p in pkg_list for p in ["numpy", "polars", "duckdb", "clickhouse"]):
            trends.append("Uses high-performance data tools")

        # Rust/Go migration signals
        if any(p in pkg_list for p in ["tokio", "actix", "axum"]):
            trends.append("Exploring Rust async ecosystem")
        if any(p in pkg_list for p in ["chi", "fiber", "echo"]):
            trends.append("Modern Go web frameworks")

        # Legacy warnings
        if any(p in pkg_list for p in ["moment", "underscore", "request"]):
            trends.append("Contains legacy dependencies (consider upgrade)")

        return trends[:5]  # Limit to 5 trends

    def _build_philosophy_summary(
        self, counts: Dict[str, int], ecosystems: Dict[str, int]
    ) -> Dict[str, List[str]]:
        """Build engineering philosophy summary."""
        philosophy = {}

        if counts.get("productivity", 0) > counts.get("performance", 0):
            philosophy["work_style"] = ["Productivity-oriented", "Ship fast, iterate"]
        elif counts.get("performance", 0) > 0:
            philosophy["work_style"] = ["Performance-oriented", "Optimize for speed"]
        else:
            philosophy["work_style"] = ["Balanced", "Right tool for the job"]

        if counts.get("production", 0) > counts.get("research", 0):
            philosophy["grade"] = ["Production-grade", "Enterprise-ready"]
        elif counts.get("research", 0) > 0:
            philosophy["grade"] = ["Research-grade", "Experimental"]
        else:
            philosophy["grade"] = ["Standard", "General purpose"]

        if counts.get("modern", 0) > counts.get("legacy", 0):
            philosophy["stack"] = ["Modern stack", "Current best practices"]
        elif counts.get("legacy", 0) > 2:
            philosophy["stack"] = ["Legacy stack", "May need modernization"]
        else:
            philosophy["stack"] = ["Mixed stack", "Gradual migration"]

        if ecosystems:
            philosophy["ecosystem"] = [f"Uses {', '.join(ecosystems.keys())} ecosystem"]

        return philosophy

    def _generate_summary(
        self,
        scores: Dict[str, float],
        ecosystems: Dict[str, float],
        trends: List[str],
    ) -> str:
        """Generate human-readable summary."""
        parts = []

        # Pragmatism
        if scores.get("pragmatism", 0.5) > 0.6:
            parts.append("pragmatic developer")
        elif scores.get("pragmatism", 0.5) < 0.4:
            parts.append("perfectionist approach")

        # Production focus
        if scores.get("production_focus", 0.5) > 0.5:
            parts.append("production-conscious")
        else:
            parts.append("prototype-friendly")

        # Modernity
        if scores.get("modernity", 0.5) > 0.6:
            parts.append("uses modern tools")
        elif scores.get("modernity", 0.5) < 0.3:
            parts.append("traditional approach")

        return ", ".join(parts) if parts else "Standard engineering practices"


def analyze_dependencies(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze dependencies.

    Args:
        raw_data: Dictionary with dep_files and optionally repos

    Returns:
        Analysis results
    """
    analyzer = DependencyAnalyzer()
    return analyzer.analyze(raw_data)
