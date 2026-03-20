"""
Domain Detection
================
Detects problem domains (ML, Web3, DevOps, etc.) from technology combinations.
Maps technologies to specific domain expertise areas.
"""

from typing import Optional
from modules.skill_analyzer.types import DomainProfile, SkillSignal


# =============================================================================
# DOMAIN SIGNATURES
# =============================================================================

DOMAIN_SIGNATURES = {
    "Machine Learning Engineering": {
        "technologies": [
            "pytorch", "tensorflow", "keras", "jax", "sklearn", "xgboost",
            "lightgbm", "catboost", "torch", "mlflow", "wandb", "tensorboard",
            "huggingface", "transformers", "fastai", "onnx", "tflite",
            "coreml", "tensorflow.js", "deca", "diffusers", "peft", "trl"
        ],
        "signals": [
            "training pipelines", "model checkpoints", "datasets directory",
            "notebooks", "experiment tracking", "hyperparameter tuning"
        ],
        "min_confidence": 2,
    },
    "Data Engineering": {
        "technologies": [
            "apache-spark", "spark", "pyspark", "kafka", "flink", "airflow",
            "dbt", "snowflake", "bigquery", "databricks", "delta-lake",
            "prestodb", "trino", "duckdb", "polars", "dask", "beam",
            "sqlglot", "great-expectations", "lakehouse"
        ],
        "signals": [
            "data pipelines", "etl", "data warehouse", "data lake",
            "batch processing", "stream processing", "data quality"
        ],
        "min_confidence": 2,
    },
    "Backend Systems Engineering": {
        "technologies": [
            "go", "rust", "postgresql", "mysql", "redis", "grpc", "kafka",
            "rabbitmq", "nats", "elasticsearch", "consul", "etcd", "raft",
            "cockroachdb", "tidb", "dynamodb", "cassandra", "scylladb"
        ],
        "signals": [
            "distributed systems", "microservices", "high availability",
            "consistency", "replication", "partitioning", "sharding"
        ],
        "min_confidence": 2,
    },
    "Frontend Engineering": {
        "technologies": [
            "react", "vue", "angular", "svelte", "next.js", "nuxt",
            "gatsby", "remix", "tailwindcss", "sass", "css", "html",
            "webpack", "vite", "rollup", "esbuild", "redux", "zustand",
            "vuex", "pinia", "react-query", "swr", "graphql", "urql"
        ],
        "signals": [
            "user interface", "components", "responsive design",
            "single page application", "progressive web app", "ssr"
        ],
        "min_confidence": 3,
    },
    "Fullstack Engineering": {
        "technologies": [
            "react", "vue", "angular", "node.js", "express", "fastapi",
            "django", "flask", "postgres", "mongodb", "redis", "typescript",
            "next.js", "nuxt", "remix", "prisma", "typeorm", "graphql"
        ],
        "signals": [
            "api development", "database design", "frontend-backend integration",
            "full stack", "end to end", "monorepo"
        ],
        "min_confidence": 3,
    },
    "DevOps/Platform Engineering": {
        "technologies": [
            "kubernetes", "docker", "terraform", "ansible", "helm", "prometheus",
            "grafana", "argocd", "flux", "jenkins", "github-actions", "gitlab-ci",
            "pagerduty", "datadog", "newrelic", "splunk", "vault", "consul",
            "istio", "linkerd", "envoy", "traefik", "nginx", "cert-manager"
        ],
        "signals": [
            "infrastructure", "deployment", "monitoring", "logging",
            "container orchestration", "ci/cd pipeline", "sre"
        ],
        "min_confidence": 3,
    },
    "Cloud Infrastructure Engineering": {
        "technologies": [
            "aws", "azure", "gcp", "terraform", "cloudformation", "pulumi",
            "eks", "gke", "aks", "lambda", "azure-functions", "cloud-functions",
            "s3", "blob-storage", "rds", "cloud-sql", "dynamodb", "cosmosdb"
        ],
        "signals": [
            "cloud native", "cloud platform", "serverless", "multi-cloud",
            "infrastructure automation", "cloud migration"
        ],
        "min_confidence": 3,
    },
    "Mobile Engineering": {
        "technologies": [
            "swift", "kotlin", "swiftui", "jetpack-compose", "react-native",
            "flutter", "expo", "ionic", "cordova", "capactior", "xcode",
            "android-studio", "app-store", "play-store", "fastlane"
        ],
        "signals": [
            "ios", "android", "mobile app", "cross-platform",
            "app store deployment", "mobile development"
        ],
        "min_confidence": 2,
    },
    "Data Science": {
        "technologies": [
            "python", "r", "jupyter", "pandas", "numpy", "scipy", "statsmodels",
            "scikit-learn", "statsmodels", "seaborn", "matplotlib", "plotly",
            "bokeh", "shiny", "tidyverse", "ggplot2", "caret", "tidymodels"
        ],
        "signals": [
            "statistical analysis", "data exploration", "visualization",
            "research", "notebooks", "hypothesis testing", "modeling"
        ],
        "min_confidence": 3,
    },
    "AI/LLM Engineering": {
        "technologies": [
            "openai", "anthropic", "llamaindex", "langchain", "vllm",
            "ollama", "huggingface", "transformers", "llama", "mistral",
            "vector-db", "pinecone", "weaviate", "chroma", "milvus",
            "prompt-engineering", "fine-tuning", "rag", "agents"
        ],
        "signals": [
            "llm", "large language model", "chatbot", "rag", "retrieval",
            "prompt", "vector search", "embedding", "generative"
        ],
        "min_confidence": 2,
    },
    "Security Engineering": {
        "technologies": [
            "snyk", "sast", "dast", "owasp", "sonarqube", "fortify",
            "veracode", "snyk", "aquasecurity", "trivy", "falco",
            "vault", "keycloak", "auth0", "okta", "identity"
        ],
        "signals": [
            "security", "vulnerability", "penetration testing", "sast",
            "dast", "security audit", "compliance", "iam", "authentication"
        ],
        "min_confidence": 2,
    },
    "Web3/Blockchain Engineering": {
        "technologies": [
            "solidity", "web3.js", "ethers.js", "hardhat", "truffle",
            "foundry", "openzeppelin", "nft", "erc-721", "erc-20",
            "polygon", "ethereum", "solana", "near", "avalanche", "chainlink"
        ],
        "signals": [
            "smart contract", "blockchain", "nft", "defi", "dao",
            "decentralized", "crypto", "web3", "token"
        ],
        "min_confidence": 2,
    },
    "Real-time Systems Engineering": {
        "technologies": [
            "websocket", "socket.io", "grpc", "grpc-web", "kafka", "flink",
            "spark-streaming", "elixir", "phoenix", "akka", "vertx",
            "server-sent-events", "mqtt", "amqp", "stomp"
        ],
        "signals": [
            "real-time", "streaming", "event-driven", "websocket",
            "live updates", "push notifications", "low latency"
        ],
        "min_confidence": 2,
    },
    "API/Integration Engineering": {
        "technologies": [
            "openapi", "swagger", "postman", "insomnia", "stoplight",
            "graphql", "grpc", "thunder-client", "rest", "webhook",
            "api-gateway", "kong", "apigee", "tyk"
        ],
        "signals": [
            "api design", "rest api", "graphql api", "integration",
            "webhook", "api documentation", "api gateway"
        ],
        "min_confidence": 2,
    },
    "Embedded/IoT Engineering": {
        "technologies": [
            "c", "c++", "rust", "arduino", "esp-idf", "mbed", "zephyr",
            "freertos", "platformio", "micropython", "circuitpython"
        ],
        "signals": [
            "embedded", "iot", "firmware", "microcontroller", "rtos",
            "sensor", "actuator", "hardware"
        ],
        "min_confidence": 2,
    },
    "Game Development": {
        "technologies": [
            "unity", "unreal", "godot", "cocos2d", "phaser", "three.js",
            "babylonjs", "playfab", "photon", "colyseus", "gdscript", "gml"
        ],
        "signals": [
            "game", "game engine", "unity", "unreal", "3d", "2d game",
            "gameplay", "renderer"
        ],
        "min_confidence": 2,
    },
    "Observability Engineering": {
        "technologies": [
            "prometheus", "grafana", "alertmanager", "loki", "tempo",
            "jaeger", "zipkin", "opentelemetry", "datadog", "newrelic",
            "sentry", "sentry-sdk", "opsgenie", "pagerduty"
        ],
        "signals": [
            "monitoring", "observability", "tracing", "logging",
            "metrics", "alerting", "incident response", "sre"
        ],
        "min_confidence": 2,
    },
    "Database Engineering": {
        "technologies": [
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "neo4j", "dynamodb", "cassandra", "couchbase", "cockroachdb",
            "tidb", "yugabytedb", "planetscale", "supabase", "fauna"
        ],
        "signals": [
            "database", "sql", "nosql", "data modeling", "indexing",
            "query optimization", "replication", "sharding"
        ],
        "min_confidence": 2,
    },
    "Developer Tools Engineering": {
        "technologies": [
            "cli", "tui", "fig", "warp", "oh-my-zsh", "neovim",
            "vscode-extension", "jetbrains-plugin", "lsp", "treesitter",
            "prettier", "eslint", "black", "ruff"
        ],
        "signals": [
            "developer experience", "dx", "cli tool", "editor plugin",
            "linter", "formatter", "code generation"
        ],
        "min_confidence": 2,
    },
    "Computer Vision": {
        "technologies": [
            "opencv", "torchvision", "pillow", "scikit-image", "albumentations",
            "detectron2", "yolo", "mmdetection", "opencv.js", "mediapipe",
            "cv2", "dlib", "face-recognition"
        ],
        "signals": [
            "computer vision", "image processing", "object detection",
            "image segmentation", "face recognition", "ocr"
        ],
        "min_confidence": 2,
    },
}


class DomainDetector:
    """Detects problem domains from technology signals."""

    def __init__(self):
        self.domain_signatures = DOMAIN_SIGNATURES

    def detect_domains(
        self,
        technologies: list[str],
        topics: Optional[list[str]] = None,
        repo_names: Optional[list[str]] = None,
        descriptions: Optional[list[str]] = None,
        languages: Optional[dict[str, float]] = None,
    ) -> list[DomainProfile]:
        """
        Detect domains from technology combinations.

        Args:
            technologies: List of detected technologies
            topics: Optional list of repo topics
            repo_names: Optional list of repo names
            descriptions: Optional list of repo descriptions

        Returns:
            List of detected domains with confidence scores
        """
        tech_set = {t.lower() for t in technologies}
        topics_set = {t.lower() for t in (topics or [])}
        all_signals = tech_set.union(topics_set)

        detected_domains: list[DomainProfile] = []

        # Also infer domains from languages when topics are sparse
        if not topics or len(topics) < 2:
            lang_domains = self._infer_domains_from_languages(languages or {}, technologies)
            for lang_domain in lang_domains:
                detected_domains.append(lang_domain)

        for domain_name, signature in self.domain_signatures.items():
            # Count matching technologies
            signature_techs = {t.lower() for t in signature["technologies"]}
            matching_techs = all_signals.intersection(signature_techs)
            match_count = len(matching_techs)

            if match_count >= signature["min_confidence"]:
                # Calculate confidence
                confidence = min(match_count / signature["min_confidence"], 1.0)

                # Boost if topic matches
                if any(t.lower() in signature["signals"] for t in topics_set):
                    confidence = min(confidence + 0.1, 1.0)

                detected_domains.append(DomainProfile(
                    domain=domain_name,
                    confidence=round(confidence, 2),
                    signals=list(matching_techs),
                    primary_technologies=list(matching_techs)[:5],
                ))

        # Sort by confidence
        detected_domains.sort(key=lambda x: x.confidence, reverse=True)

        return detected_domains

    def _infer_domains_from_languages(
        self,
        languages: dict[str, float],
        all_technologies: list[str],
    ) -> list[DomainProfile]:
        """Infer domains based on language expertise when topics are sparse."""
        detected = []
        lang_set = {l.lower() for l in languages.keys()}
        tech_set = {t.lower() for t in all_technologies}

        # Language-to-domain mapping (more comprehensive)
        lang_domain_map = {
            "python": [("Machine Learning Engineering", 0.8), ("Backend Systems Engineering", 0.9), ("Data Science", 0.8), ("Language Design", 0.7)],
            "c": [("Embedded/IoT Engineering", 0.9), ("Systems Programming", 0.95)],
            "c++": [("Game Development", 0.7), ("Systems Programming", 0.9), ("Embedded/IoT Engineering", 0.7)],
            "rust": [("Backend Systems Engineering", 0.9), ("Systems Programming", 0.95)],
            "go": [("Backend Systems Engineering", 0.95), ("DevOps/Platform Engineering", 0.7)],
            "java": [("Backend Systems Engineering", 0.9), ("Android/Mobile Engineering", 0.6)],
            "javascript": [("Frontend Engineering", 0.95), ("Fullstack Engineering", 0.8)],
            "typescript": [("Frontend Engineering", 0.9), ("Fullstack Engineering", 0.9)],
            "swift": [("iOS/MacOS Engineering", 0.95)],
            "kotlin": [("Android/Mobile Engineering", 0.95)],
            "ruby": [("Backend Systems Engineering", 0.8), ("Fullstack Engineering", 0.7)],
            "php": [("Backend Systems Engineering", 0.6), ("Web Development", 0.8)],
            "shell": [("DevOps/Platform Engineering", 0.9), ("SRE Engineering", 0.8)],
            "perl": [("Systems Programming", 0.6), ("Backend Systems Engineering", 0.5)],
            "haskell": [("Language Design", 0.9), ("Systems Programming", 0.7)],
        }

        # Aggregate domain scores based on language depth
        domain_scores: dict[str, float] = {}
        for lang, depth in languages.items():
            lang_lower = lang.lower()
            if lang_lower in lang_domain_map:
                for domain, base_score in lang_domain_map[lang_lower]:
                    weighted_score = base_score * depth
                    domain_scores[domain] = max(domain_scores.get(domain, 0), weighted_score)

        # Also check technologies
        tech_domain_map = {
            "pytorch": "Machine Learning Engineering",
            "tensorflow": "Machine Learning Engineering",
            "react": "Frontend Engineering",
            "vue": "Frontend Engineering",
            "angular": "Frontend Engineering",
            "kubernetes": "DevOps/Platform Engineering",
            "docker": "DevOps/Platform Engineering",
            "postgres": "Database Engineering",
            "redis": "Backend Systems Engineering",
        }
        for tech in tech_set:
            if tech in tech_domain_map:
                domain = tech_domain_map[tech]
                domain_scores[domain] = max(domain_scores.get(domain, 0), 0.6)

        # Create profiles for domains with significant scores
        for domain, score in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 0.5:
                detected.append(DomainProfile(
                    domain=domain,
                    confidence=min(score, 1.0),
                    signals=["inferred from language expertise"],
                    primary_technologies=[l for l in languages.keys() if l.lower() in lang_set][:3],
                ))

        return detected

    def detect_cross_domain_signals(
        self,
        technologies: list[str],
    ) -> list[str]:
        """
        Detect signals that span multiple domains.

        Returns:
            List of cross-domain capability signals
        """
        tech_set = {t.lower() for t in technologies}
        cross_domain_signals = []

        # Data + ML = MLOps
        if {"python", "kubernetes", "mlflow"}.issubset(tech_set) or \
           {"python", "docker", "pytorch"}.issubset(tech_set):
            cross_domain_signals.append("MLOps")

        # Backend + Frontend = Fullstack
        backend_techs = {"go", "rust", "java", "python", "node.js", "express", "fastapi", "django"}
        frontend_techs = {"react", "vue", "angular", "typescript", "javascript"}

        if tech_set.intersection(backend_techs) and tech_set.intersection(frontend_techs):
            cross_domain_signals.append("Fullstack Development")

        # DevOps + Cloud = Platform Engineering
        devops_techs = {"kubernetes", "docker", "terraform", "prometheus", "grafana"}
        cloud_techs = {"aws", "azure", "gcp"}

        if tech_set.intersection(devops_techs) and tech_set.intersection(cloud_techs):
            cross_domain_signals.append("Cloud Platform Engineering")

        # ML + Backend = ML Engineering
        ml_techs = {"pytorch", "tensorflow", "huggingface", "transformers"}
        backend_subset = {"fastapi", "django", "flask", "express", "go"}

        if tech_set.intersection(ml_techs) and tech_set.intersection(backend_subset):
            cross_domain_signals.append("ML Engineering (Production)")

        # Security + DevOps = DevSecOps
        security_techs = {"snyk", "veracode", "sonarqube", "vault", "owasp"}
        devops_subset = {"docker", "kubernetes", "github-actions", "terraform"}

        if tech_set.intersection(security_techs) and tech_set.intersection(devops_subset):
            cross_domain_signals.append("DevSecOps")

        # Data + Backend = Data Engineering
        data_techs = {"spark", "kafka", "airflow", "dbt", "pandas"}
        if tech_set.intersection(data_techs) and tech_set.intersection(backend_subset):
            cross_domain_signals.append("Data Engineering")

        return cross_domain_signals


def detect_domains(
    technologies: list[str],
    topics: Optional[list[str]] = None,
    languages: Optional[dict[str, float]] = None,
) -> list[DomainProfile]:
    """
    Convenience function to detect domains from technologies.

    Args:
        technologies: List of technology names
        topics: Optional list of repo topics
        languages: Optional dict of language -> depth score

    Returns:
        List of detected domains
    """
    detector = DomainDetector()
    return detector.detect_domains(technologies, topics, languages=languages)
