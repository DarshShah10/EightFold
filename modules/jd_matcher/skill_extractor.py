"""
Candidate Skill Extractor
========================
Extracts ALL skills a candidate has from their GitHub profile using:
- Language analysis
- Dependency analysis
- Topic analysis
- Commit pattern analysis
- Repo description analysis
- Skill inference (TypeScript → JS, etc.)

Then matches against JD skills for proper scoring.
"""

import re
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class CandidateSkill:
    """A skill extracted from candidate's GitHub."""
    skill: str
    confidence: float  # 0-1
    sources: list[str]  # Where we found it
    evidence: list[str]  # Specific evidence
    is_inferred: bool = False  # True if inferred from other skills


# =============================================================================
# SKILL INFERENCE RULES
# =============================================================================

# If candidate has X, they likely have Y
SKILL_INFERENCE = {
    # Languages
    "typescript": [("javascript", 0.85), ("node.js", 0.7), ("web development", 0.6)],
    "javascript": [("typescript", 0.7), ("node.js", 0.75), ("web development", 0.8)],
    "node.js": [("javascript", 0.9), ("npm", 0.7), ("backend development", 0.6)],
    "react": [("javascript", 0.9), ("jsx", 0.8), ("web development", 0.7)],
    "vue": [("javascript", 0.9), ("web development", 0.7)],
    "angular": [("typescript", 0.9), ("javascript", 0.9), ("rxjs", 0.6)],
    "c++": [("c", 0.8), ("systems programming", 0.6)],
    "c#": [(".net", 0.7), ("asp.net", 0.5)],
    "rust": [("systems programming", 0.7), ("c++", 0.5)],
    "go": [("golang", 1.0), ("backend development", 0.6), ("microservices", 0.5)],
    "golang": [("go", 1.0)],
    "python": [("django", 0.6), ("flask", 0.6), ("fastapi", 0.5), ("data science", 0.5)],

    # ML
    "tensorflow": [("deep learning", 0.9), ("neural networks", 0.8), ("keras", 0.7), ("machine learning", 0.8)],
    "pytorch": [("deep learning", 0.9), ("neural networks", 0.8), ("machine learning", 0.8)],
    "scikit-learn": [("machine learning", 0.9), ("sklearn", 1.0), ("data science", 0.7)],
    "sklearn": [("scikit-learn", 1.0), ("machine learning", 0.9)],
    "keras": [("tensorflow", 0.8), ("deep learning", 0.8), ("neural networks", 0.7)],
    "pandas": [("data analysis", 0.8), ("numpy", 0.8), ("data science", 0.7)],
    "numpy": [("data science", 0.7), ("scientific computing", 0.7), ("pandas", 0.8)],
    "scipy": [("numpy", 0.9), ("data science", 0.7), ("scientific computing", 0.8)],
    "matplotlib": [("data visualization", 0.8), ("numpy", 0.7), ("data science", 0.6)],
    "seaborn": [("matplotlib", 0.9), ("data visualization", 0.8), ("pandas", 0.6)],
    "jupyter": [("python", 0.8), ("data science", 0.6), ("jupyterlab", 0.7)],

    # MLOps
    "docker": [("containerization", 0.9), ("devops", 0.7), ("kubernetes", 0.6), ("ci/cd", 0.5)],
    "kubernetes": [("docker", 0.8), ("containerization", 0.8), ("k8s", 1.0), ("devops", 0.7), ("mlops", 0.6)],
    "k8s": [("kubernetes", 1.0)],
    "jenkins": [("ci/cd", 0.9), ("devops", 0.7), ("automation", 0.6)],
    "github actions": [("ci/cd", 0.9), ("devops", 0.6)],
    "gitlab ci": [("ci/cd", 0.9), ("devops", 0.6)],
    "terraform": [("infrastructure as code", 0.9), ("devops", 0.7), ("aws", 0.5)],
    "ansible": [("devops", 0.8), ("infrastructure as code", 0.7), ("automation", 0.7)],
    "mlflow": [("mlops", 0.8), ("machine learning", 0.6), ("model tracking", 0.8)],
    "kubeflow": [("mlops", 0.9), ("kubernetes", 0.8), ("machine learning", 0.6)],

    # Cloud
    "aws": [("amazon web services", 1.0), ("cloud", 0.8), ("s3", 0.7), ("ec2", 0.7), ("lambda", 0.6)],
    "azure": [("microsoft azure", 1.0), ("cloud", 0.8), ("azure devops", 0.6)],
    "gcp": [("google cloud", 1.0), ("cloud", 0.8), ("bigquery", 0.6)],
    "databricks": [("spark", 0.8), ("data engineering", 0.7), ("cloud", 0.6)],

    # Databases
    "postgresql": [("sql", 0.9), ("database", 0.8), ("postgres", 1.0)],
    "mysql": [("sql", 0.9), ("database", 0.8), ("mariadb", 0.6)],
    "mongodb": [("nosql", 0.9), ("database", 0.7), ("mongoose", 0.6)],
    "redis": [("caching", 0.8), ("database", 0.6), ("nosql", 0.6)],
    "elasticsearch": [("search", 0.8), ("nosql", 0.6), ("logstash", 0.5)],

    # Data Engineering
    "spark": [("pyspark", 0.8), ("big data", 0.8), ("data engineering", 0.7), ("apache spark", 1.0)],
    "kafka": [("streaming", 0.8), ("event driven", 0.7), ("apache kafka", 1.0), ("data engineering", 0.6)],
    "airflow": [("data pipeline", 0.8), ("etl", 0.7), ("workflow", 0.7), ("orchestration", 0.7)],
    "dbt": [("data transformation", 0.8), ("sql", 0.7), ("etl", 0.6)],

    # Concepts
    "machine learning": [("ml", 1.0), ("data science", 0.7), ("deep learning", 0.6)],
    "deep learning": [("neural networks", 0.9), ("machine learning", 0.9), ("ai", 0.6)],
    "nlp": [("natural language processing", 1.0), ("machine learning", 0.7), ("transformers", 0.6)],
    "computer vision": [("deep learning", 0.9), ("image processing", 0.8), ("cv", 1.0)],
    "time series": [("forecasting", 0.8), ("data analysis", 0.6)],
    "reinforcement learning": [("machine learning", 0.8), ("ai", 0.6), ("robotics", 0.4)],

    # Web
    "html": [("css", 0.9), ("web development", 0.8), ("frontend", 0.7)],
    "css": [("html", 0.9), ("web development", 0.8), ("frontend", 0.7), ("sass", 0.5)],
    "sass": [("css", 0.9), ("web development", 0.6)],
    "graphql": [("api", 0.7), ("backend development", 0.5)],
    "rest api": [("api", 1.0), ("backend development", 0.6), ("web services", 0.7)],

    # Practices
    "ci/cd": [("devops", 0.8), ("continuous integration", 1.0), ("continuous deployment", 1.0)],
    "devops": [("ci/cd", 0.7), ("infrastructure as code", 0.6), ("cloud", 0.6)],
    "agile": [("scrum", 0.7), ("software engineering", 0.5)],
    "tdd": [("testing", 0.8), ("software engineering", 0.6)],
    "testing": [("tdd", 0.6), ("pytest", 0.5), ("unit testing", 0.7)],
}


# Reverse inference (Y implies X)
REVERSE_INFERENCE = {
    "javascript": "web development",
    "node.js": "backend development",
    "react": "frontend",
    "docker": "devops",
    "kubernetes": "devops",
    "tensorflow": "machine learning",
    "pytorch": "machine learning",
    "kafka": "data engineering",
    "spark": "big data",
}


def extract_all_skills(raw_data: dict[str, Any]) -> dict[str, CandidateSkill]:
    """
    Extract ALL skills a candidate has from their GitHub profile.

    Returns dict of skill_name -> CandidateSkill
    """
    skills: dict[str, CandidateSkill] = {}

    repos = raw_data.get("repos", []) or []
    commits = raw_data.get("commits", []) or []
    dep_files = raw_data.get("dep_files", {}) or {}
    lang_bytes = raw_data.get("lang_bytes", {}) or {}

    # 1. Extract from languages
    skills.update(_extract_language_skills(lang_bytes, repos))

    # 2. Extract from dependencies
    skills.update(_extract_dependency_skills(dep_files, repos))

    # 3. Extract from topics
    skills.update(_extract_topic_skills(repos))

    # 4. Extract from descriptions
    skills.update(_extract_description_skills(repos))

    # 5. Extract from commit patterns
    skills.update(_extract_commit_skills(commits))

    # 6. Apply inference rules
    skills = _apply_skill_inference(skills)

    return skills


def _extract_language_skills(lang_bytes: dict, repos: list[dict]) -> dict[str, CandidateSkill]:
    """Extract skills from programming languages."""
    skills = {}

    if not lang_bytes:
        return skills

    total_bytes = sum(lang_bytes.values())

    for lang, bytes_count in lang_bytes.items():
        percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
        lang_normalized = lang.lower()

        # Normalize some language names
        name_mapping = {
            "python": "Python",
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "c++": "C++",
            "c#": "C#",
            "jupyter notebook": "Jupyter",
            "html": "HTML",
            "css": "CSS",
        }
        display_name = name_mapping.get(lang_normalized, lang)

        # Calculate confidence based on usage
        if percentage > 30:
            confidence = 0.95
        elif percentage > 10:
            confidence = 0.85
        elif percentage > 5:
            confidence = 0.75
        else:
            confidence = 0.6

        # Find repos using this language
        repos_using = []
        for repo in repos:
            if repo.get("language", "").lower() == lang_normalized:
                repos_using.append(repo.get("name", ""))

        skills[display_name.lower()] = CandidateSkill(
            skill=display_name,
            confidence=confidence,
            sources=["language_analysis"],
            evidence=[
                f"{percentage:.1f}% of codebase ({bytes_count // 1024}KB)",
                f"Used in {len(repos_using)} repos" if repos_using else "Used in codebase",
            ],
            is_inferred=False,
        )

    return skills


def _extract_dependency_skills(dep_files: dict, repos: list[dict]) -> dict[str, CandidateSkill]:
    """Extract skills from dependency files."""
    skills = {}

    for file_name, content in dep_files.items():
        if not content:
            continue

        content_str = str(content).lower()
        file_lower = file_name.lower()

        # Package.json (Node.js)
        if "package.json" in file_lower:
            _parse_npm_deps(content, skills)

        # Requirements.txt / pyproject.toml (Python)
        elif "requirements" in file_lower or "pyproject" in file_lower or "setup.py" in file_lower:
            _parse_python_deps(content, skills)

        # Cargo.toml (Rust)
        elif "cargo.toml" in file_lower:
            _parse_rust_deps(content, skills)

        # go.mod (Go)
        elif "go.mod" in file_lower:
            _parse_go_deps(content, skills)

        # pom.xml / build.gradle (Java)
        elif "pom.xml" in file_lower or "build.gradle" in file_lower:
            _parse_java_deps(content, skills)

    return skills


def _parse_npm_deps(content: str, skills: dict):
    """Parse npm package.json dependencies."""
    import json

    try:
        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content
    except:
        # Fallback to regex
        deps = re.findall(r'"([^"]+)":\s*"[^"]+"', content)
        for dep in deps:
            _add_dependency_skill(dep, skills, "npm")
        return

    all_deps = []
    if isinstance(data, dict):
        all_deps.extend(data.get("dependencies", {}).keys())
        all_deps.extend(data.get("devDependencies", {}).keys())

    for dep in all_deps:
        _add_dependency_skill(dep, skills, "npm")


def _parse_python_deps(content: str, skills: dict):
    """Parse Python requirements."""
    lines = content.split("\n") if isinstance(content, str) else []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Handle various formats
        pkg = re.split(r"[<>=!~]", line)[0].strip()
        pkg = pkg.replace("_", "-").lower()

        if pkg and not pkg.startswith("."):
            _add_dependency_skill(pkg, skills, "pip")


def _parse_rust_deps(content: str, skills: dict):
    """Parse Rust Cargo.toml dependencies."""
    in_deps = False
    lines = content.split("\n") if isinstance(content, str) else []

    for line in lines:
        line = line.strip()
        if line.startswith("["):
            in_deps = "dependencies" in line or "dev-dependencies" in line
        elif in_deps and "=" in line:
            pkg = line.split("=")[0].strip().replace('"', '').replace("'", '')
            _add_dependency_skill(pkg, skills, "cargo")


def _parse_go_deps(content: str, skills: dict):
    """Parse Go go.mod dependencies."""
    lines = content.split("\n") if isinstance(content, str) else []

    for line in lines:
        line = line.strip()
        if "/" in line and not line.startswith("module") and not line.startswith("require"):
            pkg = line.split()[0] if " " in line else line
            _add_dependency_skill(pkg.split("/")[-1], skills, "go")


def _parse_java_deps(content: str, skills: dict):
    """Parse Java Maven/Gradle dependencies."""
    # Look for common patterns
    patterns = [
        r'<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>',
        r'implementation\s+["\']([^"\']+)["\']',
        r'compile\s+["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                artifact = match[1] if len(match) > 1 else match[0]
            else:
                artifact = match

            # Extract short name
            parts = artifact.split(".")
            if len(parts) > 2:
                artifact = parts[-1]

            _add_dependency_skill(artifact.lower(), skills, "maven")


def _add_dependency_skill(dep: str, skills: dict, ecosystem: str):
    """Add a dependency as a skill."""
    dep = dep.lower()

    # Skip scoped packages for common frameworks
    if dep.startswith("@"):
        dep = dep.split("/")[-1] if "/" in dep else dep[1:]

    # Map to skill name
    skill_map = {
        "react": "React",
        "vue": "Vue",
        "angular": "Angular",
        "next": "Next.js",
        "nuxt": "Nuxt",
        "express": "Express",
        "fastify": "Fastify",
        "koa": "Koa",
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "scikit-learn": "scikit-learn",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "keras": "Keras",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scipy": "SciPy",
        "matplotlib": "Matplotlib",
        "seaborn": "Seaborn",
        "requests": "Python",
        "pytest": "pytest",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "kubectl": "Kubernetes",
        "helm": "Helm",
        "terraform": "Terraform",
        "ansible": "Ansible",
        "jenkins": "Jenkins",
        "grafana": "Grafana",
        "prometheus": "Prometheus",
        "nginx": "Nginx",
        "redis": "Redis",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "elasticsearch": "Elasticsearch",
        "kafka": "Apache Kafka",
        "spark": "Apache Spark",
        "airflow": "Apache Airflow",
        "mlflow": "MLflow",
        "kubeflow": "Kubeflow",
        "sentry": "Sentry",
        "stripe": "Stripe",
        "prisma": "Prisma",
        "sequelize": "Sequelize",
        "typeorm": "TypeORM",
        "graphql": "GraphQL",
        "apollo": "Apollo",
        "redux": "Redux",
        "webpack": "Webpack",
        "vite": "Vite",
        "esbuild": "esbuild",
        "swc": "SWC",
        "svelte": "Svelte",
        "sveltekit": "SvelteKit",
        "nextjs": "Next.js",
        "nuxtjs": "Nuxt",
        "trpc": "tRPC",
        "trpc": "tRPC",
        "zod": "Zod",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "psycopg2": "PostgreSQL",
        "pymongo": "MongoDB",
        "httpx": "Python",
        "aiohttp": "Python",
        "celery": "Celery",
        "rq": "Redis",
        "langchain": "LangChain",
        "llamaindex": "LlamaIndex",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "huggingface": "Hugging Face",
        "transformers": "Hugging Face Transformers",
        "gradio": "Gradio",
        "streamlit": "Streamlit",
        "langgraph": "LangGraph",
        "crewai": "CrewAI",
    }

    # Normalize
    dep_normalized = dep.lower().replace("-", "_").replace("_", "-")

    # Get display name
    display_name = skill_map.get(dep, dep.title())

    if display_name.lower() not in skills:
        skills[display_name.lower()] = CandidateSkill(
            skill=display_name,
            confidence=0.75,
            sources=["dependency_analysis"],
            evidence=[f"Found in {ecosystem} dependencies"],
            is_inferred=False,
        )


def _extract_topic_skills(repos: list[dict]) -> dict[str, CandidateSkill]:
    """Extract skills from GitHub topics."""
    skills = {}

    for repo in repos:
        topics = repo.get("topics", []) or []
        for topic in topics:
            topic_str = str(topic).lower()
            topic_display = str(topic).title()

            # Skip generic topics
            if topic_str in ["github", "python", "java", "javascript"]:
                continue

            # Map common topics to skills
            topic_map = {
                "machine-learning": ("Machine Learning", 0.9),
                "deep-learning": ("Deep Learning", 0.9),
                "natural-language-processing": ("NLP", 0.9),
                "computer-vision": ("Computer Vision", 0.9),
                "data-science": ("Data Science", 0.85),
                "artificial-intelligence": ("AI", 0.8),
                "neural-networks": ("Neural Networks", 0.85),
                "reinforcement-learning": ("Reinforcement Learning", 0.9),
                "tensorflow": ("TensorFlow", 0.9),
                "pytorch": ("PyTorch", 0.9),
                "scikit-learn": ("scikit-learn", 0.9),
                "kubernetes": ("Kubernetes", 0.9),
                "docker": ("Docker", 0.9),
                "devops": ("DevOps", 0.85),
                "mlops": ("MLOps", 0.9),
                "api": ("API Development", 0.75),
                "rest-api": ("REST API", 0.8),
                "graphql": ("GraphQL", 0.85),
                "microservices": ("Microservices", 0.8),
                "blockchain": ("Blockchain", 0.85),
                "web3": ("Web3", 0.8),
                "iot": ("IoT", 0.85),
                "aws": ("AWS", 0.9),
                "azure": ("Azure", 0.9),
                "gcp": ("Google Cloud", 0.9),
                "react": ("React", 0.9),
                "vue": ("Vue", 0.9),
                "angular": ("Angular", 0.9),
                "flutter": ("Flutter", 0.9),
                "react-native": ("React Native", 0.9),
                "swift": ("Swift", 0.9),
                "kotlin": ("Kotlin", 0.9),
                "typescript": ("TypeScript", 0.9),
                "nodejs": ("Node.js", 0.9),
                "postgresql": ("PostgreSQL", 0.9),
                "mongodb": ("MongoDB", 0.9),
                "redis": ("Redis", 0.9),
                "elasticsearch": ("Elasticsearch", 0.9),
                "kafka": ("Apache Kafka", 0.9),
                "spark": ("Apache Spark", 0.9),
                "airflow": ("Apache Airflow", 0.9),
                "data-engineering": ("Data Engineering", 0.85),
                "etl": ("ETL", 0.85),
                "ci-cd": ("CI/CD", 0.9),
                "infrastructure-as-code": ("Infrastructure as Code", 0.85),
                "terraform": ("Terraform", 0.9),
                "ansible": ("Ansible", 0.9),
            }

            if topic_str in topic_map:
                skill_name, conf = topic_map[topic_str]
            else:
                # Use title case
                skill_name = topic_display
                conf = 0.7

            if skill_name.lower() not in skills:
                skills[skill_name.lower()] = CandidateSkill(
                    skill=skill_name,
                    confidence=conf,
                    sources=["github_topics"],
                    evidence=[f"Topic: {topic}"],
                    is_inferred=False,
                )

    return skills


def _extract_description_skills(repos: list[dict]) -> dict[str, CandidateSkill]:
    """Extract skills from repo descriptions."""
    skills = {}

    # Keywords to look for in descriptions
    desc_keywords = {
        "api": "API Development",
        "rest": "REST API",
        "graphql": "GraphQL",
        "microservice": "Microservices",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "deep learning": "Deep Learning",
        "neural network": "Neural Networks",
        "nlp": "NLP",
        "nlp": "Natural Language Processing",
        "computer vision": "Computer Vision",
        "data pipeline": "Data Pipeline",
        "etl": "ETL",
        "real-time": "Real-time Systems",
        "streaming": "Streaming",
        "blockchain": "Blockchain",
        "smart contract": "Smart Contracts",
        "web3": "Web3",
        "ci/cd": "CI/CD",
        "devops": "DevOps",
        "testing": "Testing",
        "monitoring": "Monitoring",
        "observability": "Observability",
        "distributed": "Distributed Systems",
        "scalable": "Scalability",
        "cloud": "Cloud Computing",
        "serverless": "Serverless",
        "lambda": "AWS Lambda",
        "authentication": "Authentication",
        "oauth": "OAuth",
        "jwt": "JWT",
        "encryption": "Encryption",
        "security": "Security",
    }

    for repo in repos:
        desc = (repo.get("description", "") or "").lower()
        name = repo.get("name", "").lower()

        for keyword, skill_name in desc_keywords.items():
            if keyword in desc or keyword in name:
                if skill_name.lower() not in skills:
                    skills[skill_name.lower()] = CandidateSkill(
                        skill=skill_name,
                        confidence=0.6,
                        sources=["repository_description"],
                        evidence=[f"Found in: {repo.get('name', '')}"],
                        is_inferred=False,
                    )

    return skills


def _extract_commit_skills(commits: list[dict]) -> dict[str, CandidateSkill]:
    """Extract skills from commit patterns."""
    skills = {}

    # Keywords in commits that indicate skills
    commit_keywords = {
        "fix": "Bug Fixing",
        "bug": "Bug Fixing",
        "feat": "Feature Development",
        "feature": "Feature Development",
        "refactor": "Refactoring",
        "test": "Testing",
        "docs": "Documentation",
        "chore": "DevOps",
        "ci": "CI/CD",
        "deploy": "Deployment",
        "docker": "Docker",
        "k8s": "Kubernetes",
        "api": "API Development",
        "database": "Database",
        "migration": "Database Migration",
        "cache": "Caching",
        "auth": "Authentication",
        "security": "Security",
        "performance": "Performance Optimization",
        "optimize": "Optimization",
        "config": "Configuration Management",
        "script": "Scripting",
        "automation": "Automation",
        "monitoring": "Monitoring",
        "logging": "Logging",
        "error handling": "Error Handling",
        "exception": "Error Handling",
        "retry": "Resilience",
        "load test": "Load Testing",
        "stress test": "Load Testing",
        "integration test": "Integration Testing",
        "unit test": "Unit Testing",
        "e2e test": "End-to-End Testing",
        "pipeline": "Data Pipeline",
        "workflow": "Workflow Automation",
        "ci/cd": "CI/CD",
        "github actions": "GitHub Actions",
        "jenkins": "Jenkins",
        "terraform": "Terraform",
        "ansible": "Ansible",
    }

    commit_text = " ".join([
        (c.get("message", "") or "").lower()
        for c in commits
    ])

    commit_count = len(commits)

    for keyword, skill_name in commit_keywords.items():
        count = commit_text.count(keyword)
        if count >= 2:  # At least 2 occurrences
            if skill_name.lower() not in skills:
                confidence = min(0.8, 0.5 + (count / commit_count) * 0.3) if commit_count > 0 else 0.6
                skills[skill_name.lower()] = CandidateSkill(
                    skill=skill_name,
                    confidence=confidence,
                    sources=["commit_patterns"],
                    evidence=[f"{count} commits mentioning {keyword}"],
                    is_inferred=False,
                )

    return skills


def _apply_skill_inference(skills: dict[str, CandidateSkill]) -> dict[str, CandidateSkill]:
    """Apply inference rules to expand skills."""
    inferred = {}

    for skill_name, skill in skills.items():
        skill_lower = skill_name.lower()

        # Get inference rules for this skill
        inferences = SKILL_INFERENCE.get(skill_lower, [])

        for inferred_skill, confidence_boost in inferences:
            # Don't override existing skills
            if inferred_skill.lower() in skills:
                continue

            if inferred_skill.lower() not in inferred:
                # Calculate inferred confidence
                inferred_conf = skill.confidence * confidence_boost

                inferred[inferred_skill.lower()] = CandidateSkill(
                    skill=inferred_skill.title(),
                    confidence=inferred_conf,
                    sources=["skill_inference"],
                    evidence=[f"Inferred from {skill_name}"],
                    is_inferred=True,
                )

    # Merge inferred skills
    for skill_name, skill in inferred.items():
        if skill_name not in skills:
            skills[skill_name] = skill

    return skills


def get_all_candidate_skills(raw_data: dict[str, Any]) -> list[dict]:
    """
    Get all skills for a candidate as a list suitable for JD matching.

    Returns list of dicts with:
    - skill: skill name
    - confidence: confidence score
    - is_inferred: whether this was inferred
    - sources: where it was found
    """
    skills = extract_all_skills(raw_data)

    result = []
    for skill_name, skill in skills.items():
        result.append({
            "skill": skill.skill,
            "skill_key": skill_name.lower(),
            "confidence": skill.confidence,
            "is_inferred": skill.is_inferred,
            "sources": skill.sources,
            "evidence": skill.evidence,
        })

    # Sort by confidence
    result.sort(key=lambda x: -x["confidence"])

    return result


if __name__ == "__main__":
    # Test
    from pathlib import Path
    from modules.storage import load_json

    raw = load_json(Path("data/gvanrossum_raw.json"))
    skills = get_all_candidate_skills(raw)

    print(f"Extracted {len(skills)} skills from gvanrossum:")
    for s in skills[:20]:
        inferred = " (inferred)" if s["is_inferred"] else ""
        print(f"  [{s['confidence']:.0%}] {s['skill']}{inferred}")
        if s["evidence"]:
            print(f"         -> {s['evidence'][0]}")
