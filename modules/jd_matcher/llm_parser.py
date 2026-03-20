"""
LLM-Powered JD Parser
=====================
Uses LLMs to dynamically extract skills from job descriptions.

Supports:
- OpenAI GPT models
- Anthropic Claude models
- Local/fallback extraction when LLM unavailable
"""

import json
import re
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ExtractedSkill:
    """A skill extracted from job description."""
    name: str
    category: str  # 'language', 'framework', 'tool', 'platform', 'concept', 'domain'
    is_mandatory: bool
    context: str  # Surrounding text for context
    confidence: float  # How confident we are this is a skill


def get_llm_client():
    """Get LLM client based on available API keys."""
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def extract_skills_with_llm(jd_text: str) -> list[str]:
    """
    Extract skills from job description using LLM.

    Falls back to basic extraction if LLM unavailable.

    Returns:
        List of skill names extracted from JD
    """
    provider = get_llm_client()

    if provider == "openai":
        return extract_with_openai(jd_text)
    elif provider == "anthropic":
        return extract_with_anthropic(jd_text)
    else:
        # Fallback to basic extraction
        return extract_skills_basic(jd_text)


def extract_with_openai(jd_text: str) -> list[str]:
    """Extract skills using OpenAI GPT."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""Extract all technical skills, technologies, tools, frameworks, platforms, and domain knowledge mentioned in this job description.

For each skill, determine:
1. The exact skill/technology name (e.g., "Python", "TensorFlow", "AWS", "Kubernetes", "machine learning")
2. Whether it's mandatory (required) or nice-to-have

Return a JSON array of objects with:
- "skill": the skill name
- "mandatory": true if required/must-have, false if nice-to-have/bonus

Focus on:
- Programming languages (Python, R, Java, JavaScript, etc.)
- ML/AI frameworks (TensorFlow, PyTorch, scikit-learn, etc.)
- Cloud platforms (AWS, Azure, GCP)
- MLOps tools (Docker, Kubernetes, MLflow, etc.)
- Databases (SQL, PostgreSQL, MongoDB, etc.)
- Concepts (time-series forecasting, NLP, computer vision, etc.)

Job Description:
{jd_text[:4000]}

Return ONLY valid JSON, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Extract skills from result
        skills = []
        if isinstance(result, dict) and "skills" in result:
            skills = [s["skill"] for s in result["skills"] if "skill" in s]
        elif isinstance(result, list):
            skills = [s["skill"] if isinstance(s, dict) else s for s in result]

        return skills

    except Exception as e:
        print(f"OpenAI extraction failed: {e}")
        return extract_skills_basic(jd_text)


def extract_with_anthropic(jd_text: str) -> list[str]:
    """Extract skills using Anthropic Claude."""
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""Extract all technical skills, technologies, tools, frameworks, platforms, and domain knowledge mentioned in this job description.

Return a JSON object with a "skills" array containing objects with:
- "skill": the exact skill name
- "mandatory": true if required/must-have, false if nice-to-have

Focus on: programming languages, ML/AI frameworks, cloud platforms, MLOps tools, databases, and technical concepts.

Job Description:
{jd_text[:4000]}

Return ONLY valid JSON."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text)

        skills = []
        if isinstance(result, dict) and "skills" in result:
            skills = [s["skill"] for s in result["skills"] if "skill" in s]
        elif isinstance(result, list):
            skills = [s["skill"] if isinstance(s, dict) else s for s in result]

        return skills

    except Exception as e:
        print(f"Anthropic extraction failed: {e}")
        return extract_skills_basic(jd_text)


def extract_skills_basic(jd_text: str) -> list[str]:
    """
    Basic skill extraction without LLM.
    Uses pattern matching and heuristics.
    """
    skills = set()
    text_lower = jd_text.lower()

    # Comprehensive skill patterns
    skill_patterns = {
        # Languages
        "python": r'\bpython\b',
        "r": r'\br\b(?:\s+programming|\s+language|\s+stats|\s+development)?',
        "java": r'\bjava(?:\s+programming|\s+development|\s+se)?',
        "javascript": r'\bjavascript\b|\bjs\b(?=\s)',
        "typescript": r'\btypescript\b|\bts\b(?=\s)',
        "c++": r'\bc\+\+\b',
        "c#": r'\bc#\b',
        "go": r'\bgolang\b|\bgo(?:\s+language|\s+programming)\b',
        "rust": r'\brust\b',
        "scala": r'\bscala\b',
        "sql": r'\bsql\b|\bpostgresql\b|\bmysql\b|\bsqlite\b|\bmariadb\b|\bdatabases?\b',

        # ML Frameworks
        "tensorflow": r'\btensorflow\b|\btf\b(?:\s+keras)?',
        "pytorch": r'\bpytorch\b|\btorch\b',
        "scikit-learn": r'\bscikit[- ]?learn\b|\bsklearn\b',
        "keras": r'\bkeras\b',
        "jax": r'\bjax\b',

        # ML Libraries
        "pandas": r'\bpandas\b',
        "numpy": r'\bnumpy\b',
        "scipy": r'\bscipy\b',
        "matplotlib": r'\bmatplotlib\b',
        "seaborn": r'\bseaborn\b',

        # Cloud
        "aws": r'\baws\b|\bamazon\s*web\s*services\b|\bec2\b|\bs3\b|\blambda\b',
        "azure": r'\bazure\b|\bazure\s*(?:ml|data|functions|storage)\b',
        "gcp": r'\bgcp\b|\bgoogle\s*cloud\b|\bbigquery\b',
        "databricks": r'\bdatabricks\b',

        # MLOps & DevOps
        "docker": r'\bdocker\b|\bcontainers?\b',
        "kubernetes": r'\bkubernetes\b|\bk8s\b|\bk8s\b',
        "terraform": r'\bterraform\b|\bterraforming\b',
        "mlflow": r'\bmlflow\b',
        "airflow": r'\bairflow\b',
        "kubeflow": r'\bkubeflow\b',

        # CI/CD
        "github actions": r'\bgithub\s*actions\b|\bgha\b',
        "jenkins": r'\bjenkins\b',
        "gitlab ci": r'\bgitlab\s*ci\b',

        # ML Concepts
        "machine learning": r'\bmachine\s*learning\b|\bml\b(?:\s+engineering|\s+pipeline)',
        "deep learning": r'\bdeep\s*learning\b|\bdl\b(?:\s+models?)?',
        "neural networks": r'\bneural\s*networks?\b|\bnn\b',
        "nlp": r'\bnlp\b|\bnatural\s*language\s*processing\b',
        "computer vision": r'\bcomputer\s*vision\b|\bcv\b',
        "time series": r'\btime[- ]series\b|\bforecasting\b|\bforecasting\b',
        "reinforcement learning": r'\breinforcement\s*learning\b|\brl\b',
        "generative ai": r'\bgenerative\s*ai\b|\bgenai\b|\bgpt\b|\bllm\b|\blarge\s*language\s*models?\b',

        # Data Engineering
        "spark": r'\bspark\b|\bpyspark\b|\bapache\s*spark\b',
        "kafka": r'\bkafka\b|\bapache\s*kafka\b|\bkafkaspark\b',
        "etl": r'\betl\b|\bdata\s*pipeline\b|\bpipeline\b',
        "data warehouse": r'\bdata\s*warehouse\b|\bdw\b',

        # Platforms & Tools
        "git": r'\bgit\b',
        "linux": r'\blinux\b|\bunix\b',
        "api": r'\bapi\b|\brest\s*api\b|\bapi\s*development\b',
        "flask": r'\bflask\b',
        "django": r'\bdjango\b',
        "fastapi": r'\bfastapi\b',
        "react": r'\breact\b|\breactjs\b',
        "vue": r'\bvue\.?js\b',
        "angular": r'\bangular\b',

        # Other
        "statistics": r'\bstatistics\b|\bstatistical\b',
        "optimization": r'\boptimization\b|\bconstrained\s*optimization\b',
        "feature engineering": r'\bfeature\s*engineering\b',
        "model deployment": r'\bmodel\s*deployment\b|\bserving\b|\binference\b',
        "model monitoring": r'\bmodel\s*monitoring\b|\bdrift\s*detection\b',
        "a/b testing": r'\ba/?b\s*testing\b|\bexperiment\w*\b',
    }

    # Extract skills using patterns
    for skill, pattern in skill_patterns.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            skills.add(skill)

    # Extract acronyms (all caps, 2-4 letters)
    acronyms = re.findall(r'\b([A-Z]{2,4})\b', jd_text)
    known_acronyms = {
        "ML": "machine learning",
        "AI": "artificial intelligence",
        "DL": "deep learning",
        "NLP": "natural language processing",
        "CV": "computer vision",
        "API": "api",
        "SQL": "sql",
        "ETL": "etl",
        "CI": "ci/cd",
        "CD": "ci/cd",
        "K8S": "kubernetes",
        "SRE": "sre",
        "DEVOP": "devops",
    }
    for acr in acronyms:
        if acr in known_acronyms:
            skills.add(known_acronyms[acr])

    # Extract CamelCase words (properly capitalized compound words)
    camel_words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', jd_text)
    for word in camel_words:
        # Common tech CamelCase words
        tech_mapping = {
            "MachineLearning": "machine learning",
            "DeepLearning": "deep learning",
            "TimeSeries": "time series",
            "NaturalLanguage": "natural language processing",
            "ComputerVision": "computer vision",
            "ReinforcementLearning": "reinforcement learning",
            "GitHub": "github",
            "PostgreSQL": "postgresql",
            "AmazonS3": "amazon s3",
            "AmazonWebServices": "aws",
        }
        if word in tech_mapping:
            skills.add(tech_mapping[word])

    return list(skills)


def extract_skills_with_context(jd_text: str) -> list[ExtractedSkill]:
    """
    Extract skills with context (which section they're in, surrounding text).
    """
    skills = []
    mandatory_skills = set()
    nice_to_have = set()

    text_lower = jd_text.lower()

    # Detect mandatory section - look for requirements section
    # Match from "What We are looking for" until "Good to Have"
    mandatory_section_match = re.search(
        r'(what we[\s]*are[\s]*looking for)[:\s]*(.+?)(?=\n\n|\r\r|good to have|bonus)',
        text_lower,
        re.IGNORECASE | re.DOTALL
    )

    mandatory_text = ""
    if mandatory_section_match:
        mandatory_text = mandatory_section_match.group(2)[:2000]  # Limit to 2000 chars
    else:
        # Fallback: look for patterns
        mandatory_patterns = [
            r'(?:what we[\'"]?re looking for|requirements?|must-?have|needed|essential)[:\s]+(.{2000})',
            r'(?:years?|experience|proficiency|strong|excellent|mastery)[:\s]+(.{500})',
        ]
        for pattern in mandatory_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                mandatory_text += match + " "

    # Detect nice-to-have section
    nice_patterns = [
        r'(?:nice to have|good to have|preferred|bonus|plus|additional)[:\s]+(.{500})',
    ]

    nice_text = ""
    for pattern in nice_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            nice_text += match + " "

    # Also check for "or similar" patterns - these are still mandatory if part of main requirements
    or_patterns = re.findall(r'(\w+(?:\s+\w+)?)\s*,\s*\w+\s*,\s*(?:or|a)\s+similar', text_lower)
    for skill in or_patterns:
        if skill.lower() in mandatory_text.lower():
            mandatory_skills.add(skill.lower())

    # Check for "X or Y" patterns where X is mandatory
    for match in re.finditer(r'(\w+)\s*,\s*(\w+)\s*,\?\s*(?:or|a)\s*similar', text_lower):
        for group in match.groups():
            if group and group.lower() in mandatory_text.lower():
                mandatory_skills.add(group.lower())

    # Extract all skills
    all_skills = extract_skills_with_llm(jd_text)
    if not all_skills:
        all_skills = extract_skills_basic(jd_text)

    # Determine category
    category_map = {
        "python": "language", "java": "language", "r": "language", "javascript": "language",
        "typescript": "language", "c++": "language", "go": "language", "rust": "language",
        "sql": "language",
        "tensorflow": "framework", "pytorch": "framework", "scikit-learn": "framework",
        "keras": "framework", "flask": "framework", "django": "framework", "fastapi": "framework",
        "pandas": "library", "numpy": "library", "scipy": "library",
        "aws": "cloud", "azure": "cloud", "gcp": "cloud", "databricks": "cloud",
        "docker": "tool", "kubernetes": "tool", "terraform": "tool",
        "machine learning": "concept", "deep learning": "concept", "nlp": "concept",
        "computer vision": "concept", "time series": "concept", "generative ai": "concept",
    }

    for skill in all_skills:
        # Determine if mandatory
        is_mandatory = skill.lower() in mandatory_text.lower()
        is_nice = skill.lower() in nice_text.lower()

        # Extract context
        idx = text_lower.find(skill.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(jd_text), idx + len(skill) + 50)
            context = jd_text[start:end].strip()
        else:
            context = ""

        # Determine category
        category = category_map.get(skill.lower(), "other")

        skills.append(ExtractedSkill(
            name=skill,
            category=category,
            is_mandatory=is_mandatory and not is_nice,
            context=context,
            confidence=0.8 if is_mandatory else 0.6 if is_nice else 0.5
        ))

    return skills


if __name__ == "__main__":
    # Test
    test_jd = """
    We are looking for a Senior Python Engineer with experience in:
    - Machine learning and deep learning (TensorFlow, PyTorch)
    - AWS or Azure cloud platforms
    - Docker and Kubernetes
    - Time series forecasting

    Nice to have:
    - Generative AI / LLMs
    - MLOps experience with MLflow
    """

    skills = extract_skills_with_llm(test_jd)
    print(f"LLM Skills: {skills}")

    skills_basic = extract_skills_basic(test_jd)
    print(f"Basic Skills: {skills_basic}")
