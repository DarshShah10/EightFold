"""
JD Skill Extractor - Codemax API (OpenAI-Compatible)
Extracts structured skills from job descriptions.
"""

import json
import os
from typing import Dict, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

SKILL_EXTRACTION_PROMPT = """You are a talent intelligence skill extraction engine. Analyze job descriptions and extract structured skill information.

Extract skills and return ONLY valid JSON with this exact structure:
{
  "must_have": ["required/hard skills"],
  "nice_to_have": ["preferred skills"],
  "seniority_signals": ["experience level indicators"],
  "domain_knowledge": ["industry-specific knowledge"],
  "soft_skills": ["interpersonal/communication skills"]
}

Rules:
- Normalize skill names (e.g., "machine learning" not "ML")
- Include programming languages, frameworks, tools, methodologies
- For seniority: look for "5+ years", "senior", "lead", "principal", "entry-level"
- Return ONLY JSON, no additional text"""


def get_codemax_client():
    """Get configured Codemax API client."""
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package not installed. Run: pip install openai")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = "https://api.codemax.pro/v1"
    model = os.getenv("OPENAI_MODEL", "claude-opus-4-6")

    if not api_key:
        raise ValueError("API key not found. Set ANTHROPIC_API_KEY environment variable.")

    return openai.OpenAI(api_key=api_key, base_url=base_url), model


def _call_codemax_messages(prompt: str, system: str = "", max_tokens: int = 500) -> str:
    """
    Call Codemax API using /v1/messages endpoint (Anthropic format).
    Returns the text content from the response.
    """
    import requests as _requests

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key in ("your-codemax-api-key-here", "", "none", "null"):
        raise ValueError("No valid API key")

    messages = []
    if system:
        messages.append({"role": "user", "content": f"[SYSTEM INSTRUCTIONS]\n{system}"})
    messages.append({"role": "user", "content": prompt})

    resp = _requests.post(
        "https://api.codemax.pro/v1/messages",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        json={
            "model": os.getenv("OPENAI_MODEL", "claude-opus-4-6"),
            "max_tokens": max_tokens,
            "messages": messages,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    content = data.get("content", [])
    for block in content:
        if block.get("type") == "text":
            return block.get("text", "")
    raise RuntimeError("No text in API response")


def extract_skills_from_jd(jd_text: str, model: str = None) -> Dict:
    """Extract structured skills from job description using Codemax API."""
    if not jd_text or len(jd_text.strip()) < 50:
        raise ValueError("Job description text is too short or empty")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key in ("your-codemax-api-key-here", "", "none", "null"):
        print("Warning: No valid API key found, using fallback extraction")
        return extract_skills_fallback(jd_text)

    try:
        # Use /v1/messages endpoint with Anthropic format
        user_prompt = f"""Extract skills from this job description and return ONLY valid JSON.

Job Description:
{jd_text}

Return this exact JSON format:
{{
  "must_have": ["required/hard skills - programming languages, frameworks, tools"],
  "nice_to_have": ["preferred skills"],
  "seniority_signals": ["experience level indicators like senior/junior"],
  "soft_skills": ["interpersonal/communication skills"]
}}

Rules:
- Return ONLY valid JSON, no additional text or markdown
- Normalize names: "machine learning" not "ML"
- Include programming languages, frameworks, tools, methodologies"""

        content = _call_codemax_messages(user_prompt, system=SKILL_EXTRACTION_PROMPT, max_tokens=600)

        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:] if lines[0].startswith("```") else lines)
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        skills = json.loads(content)

        required_keys = ["must_have", "nice_to_have", "seniority_signals"]
        for key in required_keys:
            if key not in skills:
                skills[key] = []
            elif not isinstance(skills[key], list):
                skills[key] = [str(skills[key])]

        skills.setdefault("domain_knowledge", [])
        skills.setdefault("soft_skills", [])

        # ── Post-process: ensure technical skills are in must_have ──────────────
        # Prevent soft skills from polluting must_have — they belong in soft_skills
        _SOFT_SKILL_PATTERNS = {
            "communication", "leadership", "teamwork", "collaboration", "presentation",
            "problem solving", "problem-solving", "analytical", "interpersonal",
            "mentoring", "stakeholder", "mentoring", "agile", "scrum", "time management",
            "organizational", "negotiation", "critical thinking", "creative",
        }
        technical_skills_set = {
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "ruby", "php", "swift", "kotlin", "scala", "r",
            "react", "angular", "vue", "node.js", "html", "css", "sass", "tailwind",
            "next.js", "nuxt", "express", "django", "flask", "fastapi", "spring",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb",
            "sql", "nosql", "firebase", "cassandra",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
            "ci/cd", "github actions", "linux", "nginx",
            "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
            "nlp", "computer vision", "ai", "scikit-learn", "opencv",
            "mlops", "mlflow", "sagemaker",
            "spark", "hadoop", "kafka", "airflow", "snowflake", "etl",
            "git", "graphql", "rest", "microservices", "api", "backend", "frontend", "full stack",
            "solid", "design patterns", "architecture",
        }

        def is_technical(skill: str) -> bool:
            sl = skill.lower()
            # Exact match in technical set
            if sl in technical_skills_set:
                return True
            # Check if it's a soft skill (shouldn't be in must_have)
            if sl in _SOFT_SKILL_PATTERNS:
                return False
            # Check if it contains soft skill patterns
            if any(p in sl for p in _SOFT_SKILL_PATTERNS):
                return False
            return True

        # Move non-technical skills from must_have → nice_to_have
        final_must_have = [s for s in skills["must_have"] if is_technical(s)]
        bumped_skills = [s for s in skills["must_have"] if not is_technical(s)]
        if bumped_skills:
            # Add to soft_skills bucket
            existing_soft = set(s.lower() for s in skills["soft_skills"])
            for s in bumped_skills:
                if s.lower() not in existing_soft:
                    skills["soft_skills"].append(s)
            skills["must_have"] = final_must_have
            # Ensure bumped skills also in nice_to_have
            existing_nice = set(s.lower() for s in skills["nice_to_have"])
            for s in bumped_skills:
                if s.lower() not in existing_nice:
                    skills["nice_to_have"].append(s)

        return skills

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}, using fallback")
        return extract_skills_fallback(jd_text)
    except Exception as e:
        print(f"API error: {e}, using fallback")
        return extract_skills_fallback(jd_text)


def extract_skills_fallback(jd_text: str) -> Dict:
    """Fallback skill extraction using keyword matching + arrow-delimited format parsing."""
    import re

    # ── Priority patterns: arrow-delimited format (e.g. "Technology->Machine Learning->Python") ──
    # This format appears in enterprise JDs (Infosys, TCS, etc.)
    arrow_skills = []
    # Match lines like "Technology->Machine Learning->Python" or "OpenSystem->Python"
    arrow_pattern = re.compile(
        r'(?:Primary|Preferrred|Required|Generic|Desirable|Skill|Technology|Platform|Tool)\s*[:\->]+\s*'
        r'(?:[\w\s]+->)*\s*([A-Z][A-Za-z\s]+?)(?:\s*[,;\n]|$)',
        re.IGNORECASE
    )
    for match in arrow_pattern.finditer(jd_text):
        skill = match.group(1).strip()
        if len(skill) >= 3 and skill.lower() not in {"open", "system", "technology", "platform", "tool", "service", "line", "services", "engineer"}:
            arrow_skills.append(skill)

    # Also extract individual skills from arrow-delimited segments
    # e.g. "Machine Learning->Python" → extract both
    arrow_segment_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)')
    for segment in re.finditer(r'[A-Za-z]+->([^\n]+)', jd_text):
        for skill_match in arrow_segment_pattern.finditer(segment.group(1)):
            skill = skill_match.group(1).strip()
            if len(skill) >= 3:
                arrow_skills.append(skill)

    technical_skills = {
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
        "React", "Angular", "Vue", "Node.js", "HTML", "CSS", "SASS", "Tailwind",
        "Next.js", "Nuxt", "Express", "Django", "Flask", "FastAPI", "Pyramid",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB",
        "SQL", "NoSQL", "Firebase", "Cassandra",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins",
        "CI/CD", "GitHub Actions", "Linux", "Nginx",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras",
        "NLP", "Computer Vision", "AI", "Scikit-learn", "OpenCV",
        "MLOps", "MLflow", "SageMaker",
        "Spark", "Hadoop", "Kafka", "Airflow", "Snowflake", "ETL",
        "Git", "GraphQL", "REST", "Agile", "Scrum",
        "Microservices", "API", "Backend", "Frontend", "Full Stack",
        "SOLID", "Design Patterns", "Architecture",
    }

    # Skills ranked by importance (first = highest priority)
    skill_priority = {
        "python": 1, "java": 1, "javascript": 1, "typescript": 1,
        "c++": 1, "c#": 1, "go": 1, "rust": 1, "ruby": 1,
        "machine learning": 1, "deep learning": 1, "tensorflow": 1, "pytorch": 1,
        "react": 2, "angular": 2, "vue": 2, "node.js": 2,
        "flask": 2, "django": 2, "fastapi": 2,
        "aws": 3, "azure": 3, "gcp": 3, "docker": 3, "kubernetes": 3,
        "postgresql": 4, "mysql": 4, "mongodb": 4, "sql": 4,
        "git": 4, "agile": 4, "scrum": 4,
        "nlp": 2, "computer vision": 2, "ai": 2,
        "microservices": 3, "api": 3, "architecture": 3,
    }

    found_technical: list[str] = []
    found_from_arrow: list[str] = []

    def skill_normalize(s: str) -> str:
        """Normalize skill name to title case matching our set."""
        s = s.strip()
        for known in technical_skills:
            if known.lower() == s.lower():
                return known
        return s if s.title() in {k.title() for k in technical_skills} else s

    # First: collect skills from arrow format (higher confidence)
    for skill in arrow_skills:
        norm = skill_normalize(skill)
        if norm in technical_skills or norm.lower() in technical_skills:
            found_from_arrow.append(norm if norm in technical_skills else norm.title())
        elif skill.lower() in {k.lower() for k in technical_skills}:
            for k in technical_skills:
                if k.lower() == skill.lower():
                    found_from_arrow.append(k)
                    break

    # Second: keyword matching (word boundary + arrow format)
    for skill in technical_skills:
        # Check word boundary
        pattern = r'(?<![A-Za-z])' + re.escape(skill) + r'(?![A-Za-z])'
        if re.search(pattern, jd_text, re.IGNORECASE):
            if skill not in found_from_arrow:
                found_technical.append(skill)
        # Also check arrow-delimited (no word boundary needed)
        if f"->{skill}" in jd_text or f"->{skill.title()}" in jd_text:
            if skill not in found_from_arrow and skill not in found_technical:
                found_technical.append(skill)

    # Merge arrow-skills with priority
    all_found = found_from_arrow + found_technical
    # Deduplicate preserving priority order
    seen = set()
    priority_skills = []
    for skill in all_found:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            priority_skills.append(skill)

    soft_skills = {
        "Leadership", "Communication", "Problem Solving", "Teamwork", "Collaboration",
        "Agile", "Scrum", "Mentoring", "Presentation", "Analytical",
    }
    found_soft = []
    for skill in soft_skills:
        pattern = r'(?<![A-Za-z])' + re.escape(skill) + r'(?![A-Za-z])'
        if re.search(pattern, jd_text, re.IGNORECASE):
            found_soft.append(skill)

    seniority_signals = []
    if re.search(r'\b(senior|lead|principal|staff|expert|5\+|7\+|10\+)\b', jd_text, re.IGNORECASE):
        seniority_signals.append("Senior/Lead level (5+ years)")
    if re.search(r'\b(junior|entry|intern|0-2|0-3)\b', jd_text, re.IGNORECASE):
        seniority_signals.append("Entry/Junior level (0-3 years)")

    # Split: must_have = highest priority (first 50%), nice_to_have = rest
    total = len(priority_skills)
    split = max(1, int(total * 0.5))

    return {
        "must_have": priority_skills[:split] if total > 0 else [],
        "nice_to_have": priority_skills[split:] if total > 0 else [],
        "seniority_signals": seniority_signals,
        "domain_knowledge": [],
        "soft_skills": list(set(found_soft)),
    }


# Skill graph for adjacency analysis
SKILL_GRAPH = {
    "Python": ["Python", "FastAPI", "Django", "Flask", "Scikit-learn", "PyTorch", "TensorFlow", "Pandas", "NumPy"],
    "JavaScript": ["JavaScript", "TypeScript", "React", "Vue", "Angular", "Node.js", "Next.js"],
    "Java": ["Java", "Kotlin", "Scala", "Spring", "Spring Boot"],
    "Go": ["Go", "Rust", "C++", "gRPC"],
    "React": ["React", "React Native", "Next.js", "TypeScript"],
    "Node.js": ["Node.js", "Express", "NestJS", "TypeScript"],
    # ML skills: Python is the primary language for ML
    "Machine Learning": ["Python", "ML", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "NLP"],
    "Deep Learning": ["Python", "TensorFlow", "PyTorch", "Keras", "Computer Vision", "NLP"],
    "TensorFlow": ["Python", "TensorFlow", "Keras", "Deep Learning"],
    "PyTorch": ["Python", "PyTorch", "Hugging Face", "Deep Learning"],
    "NLP": ["Python", "PyTorch", "TensorFlow", "NLTK", "SpaCy"],
    "Computer Vision": ["Python", "OpenCV", "PyTorch", "TensorFlow"],
    "Kubernetes": ["Kubernetes", "Docker", "Helm", "Kustomize"],
    "AWS": ["AWS", "EC2", "S3", "Lambda", "ECS", "EKS"],
    "PostgreSQL": ["PostgreSQL", "MySQL", "SQL"],
}


def get_skill_adjacent(skill: str) -> List[str]:
    """Get skills adjacent to a given skill."""
    skill_upper = skill.upper()
    for key, adjacents in SKILL_GRAPH.items():
        if skill_upper in [s.upper() for s in adjacents]:
            return adjacents
    return []


if __name__ == "__main__":
    sample_jd = """
    Senior ML Engineer
    Requirements:
    - Python, Machine Learning, Deep Learning
    - TensorFlow or PyTorch
    - AWS, Docker, Kubernetes
    - Strong communication skills
    """

    print("Testing with Codemax API...")
    result = extract_skills_from_jd(sample_jd)
    print(json.dumps(result, indent=2))
