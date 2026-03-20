"""
Technology Relationship Graph
==============================
Maps technologies to their categories, relationships, and stack patterns.
Enables understanding that "React + TypeScript + Node" = Modern Fullstack.
"""

from typing import Optional
from modules.skill_analyzer.types import TechNode, TechGraph


# =============================================================================
# TECHNOLOGY TAXONOMIES
# =============================================================================

TECH_CATEGORIES = {
    # Programming Languages
    "python": {"category": "language", "subcategory": "general", "tags": ["backend", "scripting", "data"]},
    "javascript": {"category": "language", "subcategory": "web", "tags": ["frontend", "fullstack"]},
    "typescript": {"category": "language", "subcategory": "web", "tags": ["frontend", "fullstack", "type-safe"]},
    "java": {"category": "language", "subcategory": "enterprise", "tags": ["backend", "android", "enterprise"]},
    "go": {"category": "language", "subcategory": "systems", "tags": ["backend", "cloud", "microservices"]},
    "rust": {"category": "language", "subcategory": "systems", "tags": ["backend", "performance", "wasm"]},
    "c++": {"category": "language", "subcategory": "systems", "tags": ["embedded", "game-dev", "performance"]},
    "c": {"category": "language", "subcategory": "systems", "tags": ["embedded", "low-level"]},
    "c#": {"category": "language", "subcategory": "enterprise", "tags": ["backend", "game-dev", "dotnet"]},
    "ruby": {"category": "language", "subcategory": "web", "tags": ["backend", "web", "rails"]},
    "php": {"category": "language", "subcategory": "web", "tags": ["backend", "web"]},
    "swift": {"category": "language", "subcategory": "mobile", "tags": ["ios", "macos", "apple"]},
    "kotlin": {"category": "language", "subcategory": "mobile", "tags": ["android", "backend", "jvm"]},
    "dart": {"category": "language", "subcategory": "mobile", "tags": ["flutter", "cross-platform"]},
    "scala": {"category": "language", "subcategory": "functional", "tags": ["big-data", "jvm", "spark"]},
    "r": {"category": "language", "subcategory": "data", "tags": ["data-science", "statistics", "ml"]},
    "julia": {"category": "language", "subcategory": "scientific", "tags": ["ml", "scientific", "high-perf"]},
    "haskell": {"category": "language", "subcategory": "functional", "tags": ["compilers", "type-theory"]},
    "elixir": {"category": "language", "subcategory": "functional", "tags": ["distributed", "beam", "real-time"]},
    "shell": {"category": "language", "subcategory": "scripting", "tags": ["devops", "sysadmin"]},
    "powershell": {"category": "language", "subcategory": "scripting", "tags": ["devops", "windows"]},
    "sql": {"category": "language", "subcategory": "query", "tags": ["database", "data"]},
    "html": {"category": "language", "subcategory": "markup", "tags": ["frontend", "web"]},
    "css": {"category": "language", "subcategory": "styling", "tags": ["frontend", "web", "design"]},
    "scss": {"category": "language", "subcategory": "styling", "tags": ["frontend", "web"]},
    "vue": {"category": "framework", "subcategory": "frontend", "tags": ["frontend", "web", "vuejs"]},
    "svelte": {"category": "framework", "subcategory": "frontend", "tags": ["frontend", "web"]},
    "serversidetemplating": {"category": "template", "subcategory": "server", "tags": ["backend", "web"]},
}

# Framework relationships
FRAMEWORK_RELATIONSHIPS = {
    # Frontend Frameworks
    "react": {
        "related": ["next.js", "gatsby", "remix", "react-native", "expo"],
        "implies": ["javascript", "typescript"],
        "stack_tags": ["modern-frontend", "component-based", "single-page-app"],
        "version_signals": ["react-hooks", "concurrent-mode", "server-components"],
    },
    "next.js": {
        "related": ["react", "vercel", "tailwindcss"],
        "implies": ["react", "typescript"],
        "stack_tags": ["fullstack-javascript", "ssr", "meta-framework"],
    },
    "vue.js": {
        "related": ["nuxt.js", "quasar", "vue-native"],
        "implies": ["javascript", "vue"],
        "stack_tags": ["modern-frontend", "progressive"],
    },
    "angular": {
        "related": ["angular.js", "nestjs"],
        "implies": ["typescript"],
        "stack_tags": ["enterprise-frontend", "full-stack"],
    },
    "svelte": {
        "related": ["sveltekit", "sapper"],
        "implies": ["javascript"],
        "stack_tags": ["compile-time-optimized", "modern"],
    },
    "gatsby": {
        "related": ["next.js", "react", "contentful"],
        "implies": ["react", "graphql"],
        "stack_tags": ["static-site-generator", "jamstack"],
    },
    # Backend Frameworks
    "fastapi": {
        "related": ["starlette", "uvicorn", "pydantic"],
        "implies": ["python"],
        "stack_tags": ["modern-python", "async", "api-first"],
        "version_signals": ["python-3.9+", "pydantic-v2"],
    },
    "django": {
        "related": ["django-rest-framework", "celery", "wagtail"],
        "implies": ["python"],
        "stack_tags": ["fullstack-python", "batteries-included"],
    },
    "flask": {
        "related": ["blueprint", "sqlalchemy"],
        "implies": ["python"],
        "stack_tags": ["lightweight", "micro-framework"],
    },
    "express": {
        "related": ["multer", "passport", "socket.io"],
        "implies": ["javascript", "node.js"],
        "stack_tags": ["node-backend", "minimalist", "middleware"],
    },
    "nestjs": {
        "related": ["angular", "typeorm", "passport"],
        "implies": ["typescript", "node.js"],
        "stack_tags": ["enterprise-node", "typed-backend"],
    },
    "fastify": {
        "related": ["multer", "@fastify"],
        "implies": ["javascript", "node.js"],
        "stack_tags": ["high-performance", "modern-node"],
    },
    "rails": {
        "related": ["sidekiq", "active-record", "devise"],
        "implies": ["ruby"],
        "stack_tags": ["fullstack-ruby", "convention-over-config"],
    },
    "spring": {
        "related": ["spring-boot", "spring-cloud", "spring-security"],
        "implies": ["java", "kotlin"],
        "stack_tags": ["enterprise-java", "microservices"],
    },
    "spring-boot": {
        "related": ["spring", "spring-cloud", "spring-security"],
        "implies": ["java"],
        "stack_tags": ["java-rest-api", "microservices"],
    },
    "gin": {
        "related": ["gorm"],
        "implies": ["go"],
        "stack_tags": ["go-web", "high-performance"],
    },
    "echo": {
        "related": ["gorm", "labstack"],
        "implies": ["go"],
        "stack_tags": ["go-web", "minimalist"],
    },
    "axum": {
        "related": ["tokio", "tower"],
        "implies": ["rust"],
        "stack_tags": ["async-rust", "modern-rust"],
    },
    "actix-web": {
        "related": ["tokio", "diesel"],
        "implies": ["rust"],
        "stack_tags": ["rust-web", "high-performance"],
    },
    "phoenix": {
        "related": ["ecto", "liveview"],
        "implies": ["elixir"],
        "stack_tags": ["real-time-elixir", "distributed"],
    },
    # Mobile Frameworks
    "react-native": {
        "related": ["expo", "react", "typescript"],
        "implies": ["javascript", "react"],
        "stack_tags": ["cross-platform-mobile", "javascript-mobile"],
    },
    "flutter": {
        "related": ["dart", "riverpod", "bloc"],
        "implies": ["dart"],
        "stack_tags": ["cross-platform-mobile", "ui-toolkit"],
    },
    "expo": {
        "related": ["react-native", "react"],
        "implies": ["javascript"],
        "stack_tags": ["react-native-toolkit", "rapid-dev"],
    },
    # Data/ML Frameworks
    "pytorch": {
        "related": ["torchvision", "tensorboard", "fastai"],
        "implies": ["python"],
        "stack_tags": ["deep-learning", "ml-research", "modern-ml"],
        "version_signals": ["pytorch-2.0", "torch.compile", "dynamo"],
    },
    "tensorflow": {
        "related": ["keras", "tensorboard", "tflite"],
        "implies": ["python"],
        "stack_tags": ["deep-learning", "ml-production", "ml-deployment"],
    },
    "scikit-learn": {
        "related": ["pandas", "numpy", "scipy"],
        "implies": ["python"],
        "stack_tags": ["ml-classical", "data-science"],
    },
    "jax": {
        "related": ["flax", "optax"],
        "implies": ["python"],
        "stack_tags": ["scientific-ml", "autodiff", "modern-ml"],
    },
    "langchain": {
        "related": ["openai", "llamaindex", "vector-db"],
        "implies": ["python"],
        "stack_tags": ["llm-apps", "ai-engineering", "modern-ml"],
    },
    "huggingface": {
        "related": ["transformers", "datasets", "accelerate"],
        "implies": ["python"],
        "stack_tags": ["nlp", "transformer-models", "pre-trained-ml"],
    },
    "pandas": {
        "related": ["numpy", "matplotlib", "jupyter"],
        "implies": ["python"],
        "stack_tags": ["data-analysis", "data-wrangling"],
    },
    "numpy": {
        "related": ["scipy", "pandas", "matplotlib"],
        "implies": ["python"],
        "stack_tags": ["numerical-computing", "data-science-base"],
    },
    "apache-spark": {
        "related": ["pyspark", "delta-lake", "databricks"],
        "implies": ["scala", "python"],
        "stack_tags": ["big-data", "distributed-computing", "data-engineering"],
    },
    "kafka": {
        "related": ["flink", "spark-streaming", "confluent"],
        "implies": [],
        "stack_tags": ["event-streaming", "data-engineering", "real-time"],
    },
    # Infrastructure
    "docker": {
        "related": ["docker-compose", "kubernetes", "containerd"],
        "implies": [],
        "stack_tags": ["containerization", "devops", "infrastructure"],
    },
    "kubernetes": {
        "related": ["helm", "kustomize", "istio", "docker"],
        "implies": ["docker"],
        "stack_tags": ["orchestration", "cloud-native", "devops"],
    },
    "terraform": {
        "related": ["ansible", "vault", "packer"],
        "implies": [],
        "stack_tags": ["infrastructure-as-code", "multi-cloud", "devops"],
    },
    "ansible": {
        "related": ["terraform", "vault", "chef"],
        "implies": [],
        "stack_tags": ["configuration-management", "devops", "automation"],
    },
    "prometheus": {
        "related": ["grafana", "alertmanager"],
        "implies": [],
        "stack_tags": ["observability", "monitoring", "sre"],
    },
    "grafana": {
        "related": ["prometheus", "loki", "tempo"],
        "implies": [],
        "stack_tags": ["observability", "dashboards", "monitoring"],
    },
    "github-actions": {
        "related": ["github", "docker", "aws-actions"],
        "implies": [],
        "stack_tags": ["ci-cd", "automation", "devops"],
    },
    "circleci": {
        "related": ["docker", "aws"],
        "implies": [],
        "stack_tags": ["ci-cd", "automation"],
    },
    "datadog": {
        "related": ["prometheus", "grafana"],
        "implies": [],
        "stack_tags": ["observability", "apm", "enterprise-monitoring"],
    },
}

# Stack pattern definitions
STACK_PATTERNS = {
    "modern-fullstack": {
        "technologies": ["react", "typescript", "node.js", "postgresql", "docker"],
        "min_match": 3,
        "implies": ["frontend", "backend", "database", "infrastructure"],
    },
    "ml-engineer": {
        "technologies": ["python", "pytorch", "tensorflow", "pandas", "jupyter", "mlflow"],
        "min_match": 3,
        "implies": ["machine-learning", "data-science", "research"],
    },
    "data-engineer": {
        "technologies": ["python", "spark", "kafka", "airflow", "dbt", "snowflake"],
        "min_match": 3,
        "implies": ["data-pipelines", "etl", "data-warehousing"],
    },
    "devops-engineer": {
        "technologies": ["docker", "kubernetes", "terraform", "ansible", "prometheus", "grafana"],
        "min_match": 3,
        "implies": ["infrastructure", "ci-cd", "observability", "cloud"],
    },
    "platform-engineer": {
        "technologies": ["kubernetes", "terraform", "helm", "argo-cd", "istio"],
        "min_match": 3,
        "implies": ["platform", "infrastructure", "developer-tools"],
    },
    "backend-systems": {
        "technologies": ["go", "rust", "postgresql", "redis", "grpc", "kafka"],
        "min_match": 3,
        "implies": ["high-performance", "distributed-systems", "microservices"],
    },
    "frontend-engineer": {
        "technologies": ["react", "vue", "typescript", "css", "webpack", "testing-library"],
        "min_match": 3,
        "implies": ["ui-development", "responsive-design", "component-architecture"],
    },
    "mobile-engineer": {
        "technologies": ["react-native", "flutter", "swift", "kotlin", "expo"],
        "min_match": 2,
        "implies": ["mobile-development", "cross-platform", "app-store"],
    },
    "web3-engineer": {
        "technologies": ["solidity", "web3.js", "ethers.js", "hardhat", "nft"],
        "min_match": 2,
        "implies": ["blockchain", "smart-contracts", "decentralized"],
    },
    "security-engineer": {
        "technologies": ["snyk", "OWASP", "vault", "sast", "dast", "pen-testing"],
        "min_match": 2,
        "implies": ["application-security", "devsecops", "compliance"],
    },
    "sre-engineer": {
        "technologies": ["prometheus", "grafana", "kubernetes", "alertmanager", "pagerduty"],
        "min_match": 3,
        "implies": ["reliability", "observability", "incident-response"],
    },
    "data-scientist": {
        "technologies": ["python", "r", "pandas", "jupyter", "scikit-learn", "statistics"],
        "min_match": 3,
        "implies": ["statistical-analysis", "visualization", "research"],
    },
    "ai-engineer": {
        "technologies": ["langchain", "openai", "huggingface", "llm", "vector-db"],
        "min_match": 2,
        "implies": ["llm-applications", "ai-integration", "prompt-engineering"],
    },
    "real-time-systems": {
        "technologies": ["websocket", "socket.io", "grpc", "kafka", "flink", "elixir"],
        "min_match": 3,
        "implies": ["event-driven", "streaming", "low-latency"],
    },
    "api-engineer": {
        "technologies": ["fastapi", "graphql", "postman", "openapi", "grpc", "rest"],
        "min_match": 3,
        "implies": ["api-design", "documentation", "integration"],
    },
}

# Runtimes and their implications
RUNTIME_RELATIONSHIPS = {
    "node.js": {"implies": ["javascript"], "stack_tags": ["server-side-javascript", "async-io"]},
    "deno": {"implies": ["typescript"], "stack_tags": ["modern-javascript", "secure"]},
    "bun": {"implies": ["javascript", "typescript"], "stack_tags": ["fast-runtime", "all-in-one"]},
    "jvm": {"implies": ["java", "scala", "kotlin"], "stack_tags": ["enterprise", "cross-platform"]},
    "dart-vm": {"implies": ["dart"], "stack_tags": ["cross-platform"]},
    "wasm": {"implies": [], "stack_tags": ["webassembly", "portable"]},
}

# Database relationships
DATABASE_RELATIONSHIPS = {
    "postgresql": {"category": "sql", "implies": ["sql"], "stack_tags": ["relational", "production-db"]},
    "mysql": {"category": "sql", "implies": ["sql"], "stack_tags": ["relational", "web-db"]},
    "mongodb": {"category": "nosql", "implies": [], "stack_tags": ["document-db", "flexible-schema"]},
    "redis": {"category": "nosql", "implies": [], "stack_tags": ["cache", "in-memory", "real-time"]},
    "elasticsearch": {"category": "nosql", "implies": [], "stack_tags": ["search", "log-analysis"]},
    "neo4j": {"category": "nosql", "implies": [], "stack_tags": ["graph-db", "relationships"]},
    "snowflake": {"category": "warehouse", "implies": ["sql"], "stack_tags": ["data-warehouse", "cloud-dw"]},
    "bigquery": {"category": "warehouse", "implies": ["sql"], "stack_tags": ["serverless-dw", "gcp"]},
    "clickhouse": {"category": "warehouse", "implies": [], "stack_tags": ["olap", "analytics"]},
    "timescale": {"category": "timeseries", "implies": ["postgresql"], "stack_tags": ["time-series", "iot"]},
    "supabase": {"category": "backend-as-a-service", "implies": ["postgresql"], "stack_tags": ["firebase-alternative", "realtime"]},
    "planetscale": {"category": "sql", "implies": ["mysql"], "stack_tags": ["serverless-mysql", "branching-db"]},
    "prisma": {"category": "orm", "implies": [], "stack_tags": ["type-safe-db", "modern-orm"]},
    "sqlalchemy": {"category": "orm", "implies": ["python"], "stack_tags": ["python-orm", "flexible"]},
    "drizzle": {"category": "orm", "implies": ["typescript"], "stack_tags": ["type-safe-orm", "lightweight"]},
}


class TechGraphBuilder:
    """Builds technology relationship graphs from detected technologies."""

    def __init__(self):
        self.nodes: dict[str, TechNode] = {}

    def add_technology(self, tech: str, metadata: Optional[dict] = None) -> TechNode:
        """Add a technology to the graph."""
        tech_lower = tech.lower()
        metadata = metadata or {}

        # Determine category
        if tech_lower in TECH_CATEGORIES:
            cat_info = TECH_CATEGORIES[tech_lower]
            category = cat_info["category"]
            subcategory = cat_info.get("subcategory", "")
            stack_tags = cat_info.get("tags", [])
        elif tech_lower in FRAMEWORK_RELATIONSHIPS:
            category = "framework"
            framework_info = FRAMEWORK_RELATIONSHIPS[tech_lower]
            stack_tags = framework_info.get("stack_tags", [])
            subcategory = ""
        elif tech_lower in DATABASE_RELATIONSHIPS:
            category = "database"
            db_info = DATABASE_RELATIONSHIPS[tech_lower]
            stack_tags = db_info.get("stack_tags", [])
            subcategory = db_info.get("category", "")
        elif tech_lower in RUNTIME_RELATIONSHIPS:
            category = "runtime"
            runtime_info = RUNTIME_RELATIONSHIPS[tech_lower]
            stack_tags = runtime_info.get("stack_tags", [])
            subcategory = ""
        else:
            category = metadata.get("category", "unknown")
            subcategory = metadata.get("subcategory", "")
            stack_tags = metadata.get("tags", [])

        node = TechNode(
            name=tech,
            category=category,
            subcategory=subcategory,
            stack_tags=stack_tags,
            related_technologies=self._get_related_technologies(tech_lower),
            version_signals=self._get_version_signals(tech_lower),
        )
        self.nodes[tech_lower] = node
        return node

    def _get_related_technologies(self, tech: str) -> list[str]:
        """Get technologies related to this one."""
        if tech in FRAMEWORK_RELATIONSHIPS:
            return FRAMEWORK_RELATIONSHIPS[tech].get("related", [])
        if tech in RUNTIME_RELATIONSHIPS:
            return []
        return []

    def _get_version_signals(self, tech: str) -> list[str]:
        """Get version signals for this technology."""
        if tech in FRAMEWORK_RELATIONSHIPS:
            return FRAMEWORK_RELATIONSHIPS[tech].get("version_signals", [])
        return []

    def build(self) -> TechGraph:
        """Build the final tech graph."""
        # Identify primary stack
        primary_stack = self._identify_primary_stack()

        # Identify related stacks
        related_stacks = self._identify_related_stacks()

        return TechGraph(
            nodes=self.nodes,
            primary_stack=primary_stack,
            related_stacks=related_stacks,
        )

    def _identify_primary_stack(self) -> str:
        """Identify the primary technology stack."""
        if not self.nodes:
            return "Unknown"

        # Score by stack tags
        stack_scores: dict[str, float] = {}
        for node in self.nodes.values():
            for tag in node.stack_tags:
                stack_scores[tag] = stack_scores.get(tag, 0) + 1

        if stack_scores:
            # Combine top tags into a stack name
            top_tags = sorted(stack_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            return " + ".join([tag.replace("-", " ").title() for tag, _ in top_tags])

        # Fall back to most common category
        categories = [n.category for n in self.nodes.values()]
        if categories:
            from collections import Counter
            most_common = Counter(categories).most_common(1)[0][0]
            return f"{most_common.title()} Stack"

        return "Unknown"

    def _identify_related_stacks(self) -> list[str]:
        """Identify related technology stacks."""
        related = []
        all_tags: set[str] = set()

        for node in self.nodes.values():
            all_tags.update(node.stack_tags)

        # Match against stack patterns
        for pattern_name, pattern_info in STACK_PATTERNS.items():
            stack_techs = set(t.lower() for t in pattern_info["technologies"])
            matches = len(all_tags.intersection(stack_techs))
            if matches >= pattern_info["min_match"]:
                related.append(pattern_name.replace("-", " ").title())

        return related[:5]  # Limit to top 5


def build_tech_graph(technologies: list[str]) -> TechGraph:
    """
    Build a technology relationship graph from a list of technologies.

    Args:
        technologies: List of technology names

    Returns:
        TechGraph with relationship information
    """
    builder = TechGraphBuilder()
    for tech in technologies:
        builder.add_technology(tech)
    return builder.build()


def detect_stack_patterns(technologies: list[str]) -> list[dict]:
    """
    Detect stack patterns from technologies.

    Args:
        technologies: List of technology names

    Returns:
        List of detected stack patterns with match info
    """
    detected = []
    tech_set = set(t.lower() for t in technologies)

    for pattern_name, pattern_info in STACK_PATTERNS.items():
        stack_techs = set(t.lower() for t in pattern_info["technologies"])
        matches = tech_set.intersection(stack_techs)
        match_ratio = len(matches) / len(stack_techs)

        if match_ratio >= 0.5:  # At least 50% match
            detected.append({
                "pattern": pattern_name,
                "display_name": pattern_name.replace("-", " ").title(),
                "match_count": len(matches),
                "total_required": len(pattern_info["technologies"]),
                "match_ratio": round(match_ratio, 2),
                "matched_technologies": list(matches),
                "implied_domains": pattern_info["implies"],
            })

    # Sort by match ratio
    detected.sort(key=lambda x: x["match_ratio"], reverse=True)
    return detected
