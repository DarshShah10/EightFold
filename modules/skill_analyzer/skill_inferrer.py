"""
Semantic Skill Inference
========================
Extracts what developers actually built - not just what languages they used.
Infers skills from repo names, descriptions, topics, dependencies, and file patterns.
"""

import re
from typing import Optional
from modules.skill_analyzer.types import SkillSignal


# =============================================================================
# SKILL SIGNAL PATTERNS
# =============================================================================

# Direct skill mentions in descriptions
SKILL_PATTERNS = {
    # ML/AI
    r"machine learning|ml\b": {"skill": "Machine Learning", "confidence": 0.9, "domain": "ai"},
    r"\bml\b": {"skill": "Machine Learning", "confidence": 0.6, "domain": "ai"},
    r"deep learning|neural network": {"skill": "Deep Learning", "confidence": 0.95, "domain": "ai"},
    r"nlp|natural language processing": {"skill": "NLP", "confidence": 0.95, "domain": "ai"},
    r"computer vision|cv\b|image recognition": {"skill": "Computer Vision", "confidence": 0.95, "domain": "ai"},
    r"llm|large language model|chatgpt|gpt-": {"skill": "LLM Engineering", "confidence": 0.95, "domain": "ai"},
    r"artificial intelligence|a\.i\.|ai\b": {"skill": "AI Engineering", "confidence": 0.85, "domain": "ai"},
    r"reinforcement learning|rl\b": {"skill": "Reinforcement Learning", "confidence": 0.95, "domain": "ai"},
    r"transformer|bert|gpt|attention": {"skill": "Transformer Models", "confidence": 0.9, "domain": "ai"},
    r"generative ai|gen-?ai": {"skill": "Generative AI", "confidence": 0.95, "domain": "ai"},

    # Data Engineering
    r"data pipeline|data engineering|etl": {"skill": "Data Engineering", "confidence": 0.9, "domain": "data"},
    r"data warehouse|data lake": {"skill": "Data Warehousing", "confidence": 0.9, "domain": "data"},
    r"stream processing|real-time data|streaming": {"skill": "Real-time Processing", "confidence": 0.85, "domain": "data"},
    r"big data|spark|hadoop": {"skill": "Big Data", "confidence": 0.85, "domain": "data"},
    r"analytics|dashboard|reporting": {"skill": "Data Analytics", "confidence": 0.75, "domain": "data"},

    # Backend/Systems
    r"api|rest\s*(api)?|graphql|grpc": {"skill": "API Development", "confidence": 0.85, "domain": "backend"},
    r"microservice|micro-service": {"skill": "Microservices", "confidence": 0.9, "domain": "backend"},
    r"serverless|lambda|function as a service": {"skill": "Serverless", "confidence": 0.9, "domain": "backend"},
    r"distributed system|consensus|raft|paxos": {"skill": "Distributed Systems", "confidence": 0.95, "domain": "backend"},
    r"real-?time|websocket|socket\.io": {"skill": "Real-time Systems", "confidence": 0.9, "domain": "backend"},
    r"high performance|low latency|high-throughput": {"skill": "Performance Engineering", "confidence": 0.9, "domain": "backend"},
    r"caching|redis|memcache": {"skill": "Caching", "confidence": 0.85, "domain": "backend"},
    r"message queue|rabbitmq|activemq": {"skill": "Message Queues", "confidence": 0.85, "domain": "backend"},
    r"event driven|event sourcing|cqrs": {"skill": "Event-Driven Architecture", "confidence": 0.9, "domain": "backend"},

    # Frontend
    r"responsive|mobile-?first|adaptive": {"skill": "Responsive Design", "confidence": 0.8, "domain": "frontend"},
    r"accessibility|a11y|wcag": {"skill": "Accessibility", "confidence": 0.9, "domain": "frontend"},
    r"animation|transition|motion": {"skill": "UI Animation", "confidence": 0.8, "domain": "frontend"},
    r"component library|design system|styling": {"skill": "Design Systems", "confidence": 0.85, "domain": "frontend"},
    r"ssr|server side rendering|ssg|static site": {"skill": "SSR/SSG", "confidence": 0.9, "domain": "frontend"},
    r"progressive web app|pwa": {"skill": "PWA Development", "confidence": 0.95, "domain": "frontend"},

    # DevOps/Platform
    r"kubernetes|k8s|orchestration": {"skill": "Kubernetes", "confidence": 0.95, "domain": "devops"},
    r"docker|container": {"skill": "Containerization", "confidence": 0.9, "domain": "devops"},
    r"ci/cd|pipeline|github action": {"skill": "CI/CD", "confidence": 0.9, "domain": "devops"},
    r"terraform|infrastructure as code": {"skill": "Infrastructure as Code", "confidence": 0.95, "domain": "devops"},
    r"monitoring|observability|prometheus": {"skill": "Observability", "confidence": 0.85, "domain": "devops"},
    r"logging|elk|splunk": {"skill": "Log Management", "confidence": 0.85, "domain": "devops"},
    r"security|authentication|oauth|jwt": {"skill": "Security", "confidence": 0.8, "domain": "devops"},
    r"cloud|aws|azure|gcp": {"skill": "Cloud Computing", "confidence": 0.75, "domain": "devops"},
    r"site reliability|sre|on-call": {"skill": "SRE", "confidence": 0.95, "domain": "devops"},

    # Web3
    r"blockchain|web3|defi|nft": {"skill": "Web3/Blockchain", "confidence": 0.9, "domain": "web3"},
    r"smart contract|solidity|ether": {"skill": "Smart Contract Development", "confidence": 0.95, "domain": "web3"},
    r"dao|decentralized": {"skill": "DAO Development", "confidence": 0.9, "domain": "web3"},

    # Mobile
    r"ios|iphone|ipad|swift": {"skill": "iOS Development", "confidence": 0.9, "domain": "mobile"},
    r"android|mobile app|kotlin": {"skill": "Android Development", "confidence": 0.9, "domain": "mobile"},
    r"cross.?platform|react native|flutter": {"skill": "Cross-Platform Development", "confidence": 0.9, "domain": "mobile"},

    # Data Science
    r"statistics|statistical|regression": {"skill": "Statistics", "confidence": 0.85, "domain": "data-science"},
    r"visualization|chart|d3\.js|plotly": {"skill": "Data Visualization", "confidence": 0.85, "domain": "data-science"},
    r"jupyter|notebook|exploratory": {"skill": "Data Exploration", "confidence": 0.85, "domain": "data-science"},

    # General Engineering
    r"test|testing|tdd|bdd": {"skill": "Testing", "confidence": 0.75, "domain": "engineering"},
    r"performance|optimization|speed": {"skill": "Performance Optimization", "confidence": 0.8, "domain": "engineering"},
    r"refactor|clean code|best practice": {"skill": "Code Quality", "confidence": 0.75, "domain": "engineering"},
    r"documentation|docs|readme": {"skill": "Technical Writing", "confidence": 0.7, "domain": "engineering"},
    r"open source|oss|contribution": {"skill": "Open Source", "confidence": 0.8, "domain": "engineering"},
    r"api design|restful": {"skill": "API Design", "confidence": 0.85, "domain": "engineering"},
}

# Repository name patterns that indicate skills
REPO_NAME_PATTERNS = {
    # API frameworks
    r"^api$|^rest|^graphql|^grpc": {"skill": "API Development", "confidence": 0.7},
    r"server|backend|service": {"skill": "Backend Development", "confidence": 0.6},
    r"client|sdk|wrapper": {"skill": "SDK Development", "confidence": 0.7},

    # ML/AI
    r"ml$|machine.?learning|^nn$|^cnn$|^rnn$": {"skill": "Machine Learning", "confidence": 0.7},
    r"ai$|^gpt|^llm|^bert|^transformer": {"skill": "LLM/NLP Engineering", "confidence": 0.8},
    r"model|training|inference": {"skill": "ML Engineering", "confidence": 0.65},
    r"dataset|corpus|benchmark": {"skill": "Data Engineering", "confidence": 0.7},

    # Infrastructure
    r"deploy|k8s|helm|operator": {"skill": "Platform/DevOps", "confidence": 0.7},
    r"terraform|ansible|packer": {"skill": "Infrastructure as Code", "confidence": 0.8},
    r"monitor|observ|metrics|alert": {"skill": "Observability", "confidence": 0.7},
    r"ci$|pipeline|workflow": {"skill": "CI/CD", "confidence": 0.7},

    # Web
    r"ui$|frontend|web|spa": {"skill": "Frontend Development", "confidence": 0.6},
    r"dashboard|admin|portal": {"skill": "Web Application Development", "confidence": 0.6},
    r"plugin|extension|browser": {"skill": "Browser Extension Development", "confidence": 0.7},

    # Mobile
    r"app$|mobile|android|ios": {"skill": "Mobile Development", "confidence": 0.6},
    r"react.?native|flutter": {"skill": "Cross-Platform Mobile", "confidence": 0.8},

    # Data
    r"etl|pipeline|stream": {"skill": "Data Engineering", "confidence": 0.7},
    r"warehouse|lake|analytics": {"skill": "Data Engineering", "confidence": 0.7},
    r"visualiz|chart|plot|dashboard": {"skill": "Data Visualization", "confidence": 0.7},

    # Crypto/Web3
    r"chain|crypto|web3|blockchain": {"skill": "Blockchain Development", "confidence": 0.8},
    r"token|nft|defi|dao": {"skill": "DeFi/NFT Development", "confidence": 0.8},
    r"contract|solidity": {"skill": "Smart Contract Development", "confidence": 0.85},

    # Tooling
    r"cli|tool|utility|helper": {"skill": "Developer Tooling", "confidence": 0.7},
    r"lib|library|framework": {"skill": "Library/Framework Development", "confidence": 0.7},
    r"bot|automation|script": {"skill": "Automation", "confidence": 0.65},

    # Database
    r"db|database|postgres|mysql|mongo": {"skill": "Database Engineering", "confidence": 0.7},
    r"cache|redis|memcache": {"skill": "Caching", "confidence": 0.7},
    r"search|elastic|solr": {"skill": "Search Engineering", "confidence": 0.7},
}

# Dependency file patterns that indicate skills
DEPENDENCY_SKILL_MAPPING = {
    # Python
    "requirements.txt": ["pip", "python"],
    "pyproject.toml": ["python", "poetry"],
    "Pipfile": ["python", "pipenv"],
    "setup.py": ["python", "packaging"],
    "environment.yml": ["conda", "python"],

    # JavaScript/TypeScript
    "package.json": ["node.js", "npm"],
    "yarn.lock": ["yarn", "node.js"],
    "package-lock.json": ["npm", "node.js"],
    "tsconfig.json": ["typescript"],
    ".eslintrc": ["eslint", "linting"],

    # Rust
    "Cargo.toml": ["rust", "cargo"],
    "Cargo.lock": ["rust"],

    # Go
    "go.mod": ["go", "golang"],
    "go.sum": ["go"],

    # Mobile
    "Podfile": ["cocoapods", "ios"],
    "Podfile.lock": ["cocoapods"],
    "ios/Podfile": ["ios", "cocoapods"],
    "android/app/build.gradle": ["android", "gradle"],
    "pubspec.yaml": ["flutter", "dart"],

    # Infrastructure
    "Dockerfile": ["docker", "containerization"],
    "docker-compose.yml": ["docker", "containerization"],
    "docker-compose.yaml": ["docker", "containerization"],
    ".github/workflows": ["github-actions", "ci-cd"],
    "Jenkinsfile": ["jenkins", "ci-cd"],
    ".circleci/config.yml": ["circleci", "ci-cd"],
    ".gitlab-ci.yml": ["gitlab-ci", "ci-cd"],
    "terraform.tf": ["terraform", "iac"],
    "ansible.cfg": ["ansible", "configuration-management"],
}

# File pattern signals (from repo structure)
FILE_PATTERN_SIGNALS = {
    # ML patterns
    r"models?\/.+\.pt$|models?\/.+\.h5$": {"skill": "ML Model Management", "confidence": 0.8},
    r"notebooks?\/.+\.ipynb$": {"skill": "Jupyter Notebooks", "confidence": 0.75},
    r"training|train\.py|train\.sh": {"skill": "ML Training", "confidence": 0.75},
    r"inference|predict|serve": {"skill": "ML Inference", "confidence": 0.75},
    r"dataset|data\/|data\.py": {"skill": "Data Engineering", "confidence": 0.7},

    # Infrastructure patterns
    r"kubernetes|charts?\/|k8s": {"skill": "Kubernetes", "confidence": 0.85},
    r"docker-compose": {"skill": "Docker Compose", "confidence": 0.85},
    r"terraform|modules?\/.+tf": {"skill": "Terraform", "confidence": 0.85},
    r"helm|templates?\/.+yaml": {"skill": "Helm Charts", "confidence": 0.8},
    r"prometheus|grafana|monitoring": {"skill": "Observability", "confidence": 0.8},

    # Frontend patterns
    r"components?\/.+|pages?\/.+": {"skill": "Component Architecture", "confidence": 0.75},
    r"hooks?\/.+|use.+\.tsx?": {"skill": "React Hooks", "confidence": 0.8},
    r"styles?\/.+|assets?\/.+": {"skill": "Styling/Assets", "confidence": 0.7},
    r"__tests?__|test\.py|spec\.js": {"skill": "Testing", "confidence": 0.75},

    # Backend patterns
    r"api|routes?|endpoints?": {"skill": "API Development", "confidence": 0.75},
    r"middleware|interceptors?": {"skill": "Middleware", "confidence": 0.75},
    r"services?\/.+|usecases?": {"skill": "Service Layer", "confidence": 0.7},
    r"models?\/.+|schemas?": {"skill": "Data Modeling", "confidence": 0.7},

    # Security patterns
    r"security|vuln|secret": {"skill": "Security", "confidence": 0.8},
    r"auth|jwt|oauth": {"skill": "Authentication", "confidence": 0.85},
}


class SkillInferrer:
    """Infers semantic skills from various data sources."""

    def __init__(self):
        self.patterns = SKILL_PATTERNS
        self.repo_patterns = REPO_NAME_PATTERNS
        self.dependency_signals = DEPENDENCY_SKILL_MAPPING
        self.file_patterns = FILE_PATTERN_SIGNALS

    def infer_from_description(self, description: str) -> list[SkillSignal]:
        """Extract skills from repository description."""
        if not description:
            return []

        signals = []
        description_lower = description.lower()

        for pattern, info in self.patterns.items():
            if re.search(pattern, description_lower, re.IGNORECASE):
                signals.append(SkillSignal(
                    skill=info["skill"],
                    confidence=info["confidence"],
                    source="description",
                    weight=info.get("weight", 1.0),
                ))

        return signals

    def infer_from_repo_name(self, name: str) -> list[SkillSignal]:
        """Extract skills from repository name."""
        if not name:
            return []

        signals = []
        name_lower = name.lower()

        # Check repo name patterns
        for pattern, info in self.repo_patterns.items():
            if re.search(pattern, name_lower, re.IGNORECASE):
                signals.append(SkillSignal(
                    skill=info["skill"],
                    confidence=info["confidence"] * 0.8,  # Lower weight than description
                    source="repo_name",
                    weight=0.7,
                ))

        return signals

    def infer_from_topics(self, topics: list[str]) -> list[SkillSignal]:
        """Extract skills from repository topics."""
        if not topics:
            return []

        signals = []
        for topic in topics:
            topic_lower = topic.lower()
            signals.append(SkillSignal(
                skill=topic.title().replace("-", " ").replace("_", " "),
                confidence=0.8,
                source="topic",
                weight=0.9,
            ))

        return signals

    def infer_from_dependencies(self, dependencies: list[str]) -> list[SkillSignal]:
        """Extract skills from dependency files."""
        if not dependencies:
            return []

        signals = []
        for dep_file in dependencies:
            dep_lower = dep_file.lower()

            # Check direct matches
            for pattern, skills in self.dependency_signals.items():
                if pattern.lower() in dep_lower:
                    for skill in skills:
                        signals.append(SkillSignal(
                            skill=skill,
                            confidence=0.7,
                            source="dependency",
                            weight=0.6,
                        ))

        return signals

    def infer_from_file_patterns(self, file_paths: list[str]) -> list[SkillSignal]:
        """Extract skills from file path patterns."""
        if not file_paths:
            return []

        signals = []
        for file_path in file_paths[:100]:  # Limit for performance
            path_lower = file_path.lower()

            for pattern, info in self.file_patterns.items():
                if re.search(pattern, path_lower, re.IGNORECASE):
                    signals.append(SkillSignal(
                        skill=info["skill"],
                        confidence=info["confidence"] * 0.7,
                        source="file_pattern",
                        weight=0.5,
                    ))

        return signals

    def infer_from_readme(self, readme_content: str) -> list[SkillSignal]:
        """Extract skills from README content."""
        if not readme_content:
            return []

        signals = []
        content_lower = readme_content.lower()

        # Look for "Built with", "Tech stack", "Features" sections
        tech_sections = re.findall(
            r"(?:built with|tech stack|technologies?|features?)[:\s]+([^\n]+)",
            content_lower
        )

        for section in tech_sections:
            # Split by common delimiters
            technologies = re.split(r"[,;|•·&]|and\s+", section)
            for tech in technologies:
                tech = tech.strip()
                if len(tech) > 2 and len(tech) < 30:
                    signals.append(SkillSignal(
                        skill=tech.title(),
                        confidence=0.75,
                        source="readme",
                        weight=0.6,
                    ))

        return signals

    def aggregate_signals(
        self,
        description_signals: list[SkillSignal],
        name_signals: list[SkillSignal],
        topic_signals: list[SkillSignal],
        dependency_signals: list[SkillSignal],
        file_pattern_signals: list[SkillSignal],
    ) -> dict[str, dict]:
        """
        Aggregate skill signals from all sources.

        Returns:
            Dict mapping skill names to aggregated info
        """
        skill_aggregates: dict[str, dict] = {}

        all_signals = (
            description_signals +
            name_signals +
            topic_signals +
            dependency_signals +
            file_pattern_signals
        )

        for signal in all_signals:
            if signal.skill not in skill_aggregates:
                skill_aggregates[signal.skill] = {
                    "skill": signal.skill,
                    "total_weighted_confidence": 0.0,
                    "sources": [],
                    "max_confidence": 0.0,
                    "total_weight": 0.0,
                }

            agg = skill_aggregates[signal.skill]
            agg["total_weighted_confidence"] += signal.confidence * signal.weight
            agg["total_weight"] += signal.weight
            agg["max_confidence"] = max(agg["max_confidence"], signal.confidence)
            if signal.source not in agg["sources"]:
                agg["sources"].append(signal.source)

        # Calculate final scores
        for skill, agg in skill_aggregates.items():
            if agg["total_weight"] > 0:
                agg["final_score"] = agg["total_weighted_confidence"] / agg["total_weight"]
            else:
                agg["final_score"] = 0.0

            # Boost score if multiple sources
            agg["source_boost"] = 1.0 + (len(agg["sources"]) * 0.1)

        return skill_aggregates


def infer_skills(
    repos: list[dict],
    dependencies: Optional[list[str]] = None,
    file_paths: Optional[list[str]] = None,
) -> dict[str, dict]:
    """
    Infer skills from repositories.

    Args:
        repos: List of repository dictionaries
        dependencies: Optional list of dependency file names
        file_paths: Optional list of file paths

    Returns:
        Aggregated skill information
    """
    inferrer = SkillInferrer()

    all_description_signals: list[SkillSignal] = []
    all_name_signals: list[SkillSignal] = []
    all_topic_signals: list[SkillSignal] = []

    for repo in repos:
        # From description
        description = repo.get("description", "")
        all_description_signals.extend(inferrer.infer_from_description(description))

        # From name
        name = repo.get("name", "")
        all_name_signals.extend(inferrer.infer_from_repo_name(name))

        # From topics
        topics = repo.get("topics", []) or []
        all_topic_signals.extend(inferrer.infer_from_topics(topics))

    # From dependencies
    dependency_signals = inferrer.infer_from_dependencies(dependencies or [])

    # From file patterns
    file_pattern_signals = inferrer.infer_from_file_patterns(file_paths or [])

    # Aggregate all signals
    return inferrer.aggregate_signals(
        all_description_signals,
        all_name_signals,
        all_topic_signals,
        dependency_signals,
        file_pattern_signals,
    )
