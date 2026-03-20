"""
JD Parser
=========
Extracts structured requirements from job postings.

Parses job descriptions into:
- Must-have skills
- Nice-to-have skills
- Key focus areas
- Experience requirements
- Required vs preferred qualifications
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkillRequirement:
    """A single skill requirement from a job posting."""
    skill: str
    category: str  # 'technical', 'tool', 'framework', 'domain', 'soft'
    weight: float = 1.0  # Importance weight
    is_mandatory: bool = True
    context: str = ""  # The sentence/paragraph this came from
    keywords: list[str] = field(default_factory=list)  # Alternative keywords to match


@dataclass
class ExperienceRequirement:
    """Experience level requirements."""
    years_min: int = 0
    years_max: int = 10
    area: str = ""  # e.g., "AI/ML", "Python", "Azure"


@dataclass
class ParsedJobDescription:
    """Structured representation of a job posting."""
    title: str = ""
    raw_text: str = ""
    mandatory_skills: list[SkillRequirement] = field(default_factory=list)
    nice_to_have_skills: list[SkillRequirement] = field(default_factory=list)
    key_focus_areas: list[str] = field(default_factory=list)
    experience_requirement: Optional[ExperienceRequirement] = None
    education: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)


# =============================================================================
# SKILL PATTERNS
# =============================================================================

# Technical skills and their alternative names
SKILL_ALTERNATIVES = {
    "python": ["python", "python programming", "python development"],
    "r": ["r programming", "r language", "r development"],
    "sql": ["sql", "structured query language", "database queries"],
    "time-series": ["time series", "time-series", "forecasting", "prediction models"],
    "machine learning": ["machine learning", "ml", "traditional ml", "ml algorithms"],
    "deep learning": ["deep learning", "neural networks", "dl"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "azure": ["azure", "azure ml", "azure cloud", "microsoft azure"],
    "mlops": ["mlops", "ml ops", "machine learning operations"],
    "docker": ["docker", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "spark": ["spark", "pyspark", "apache spark"],
    "kafka": ["kafka", "apache kafka", "streaming"],
    "flask": ["flask", "flask api"],
    "django": ["django"],
    "feature engineering": ["feature engineering", "feature selection", "feature extraction"],
    "api development": ["api", "rest api", "api development", "web api"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "model deployment": ["model deployment", "deploy models", "deployment"],
    "model monitoring": ["model monitoring", "drift detection", "monitoring"],
    "cloud computing": ["cloud", "cloud computing", "cloud platforms"],
    "data pipeline": ["data pipeline", "etl", "data flow", "pipelines"],
    "genai": ["genai", "generative ai", "llm", "large language models", "langchain", "agentic"],
    "optimization": ["optimization", "constrained optimization", "linear programming"],
    "reinforcement learning": ["reinforcement learning", "rl", "policy optimization"],
    "statistics": ["statistics", "statistical", "statistical analysis"],
}

# Skill to category mapping
SKILL_CATEGORIES = {
    "python": "language",
    "r": "language",
    "sql": "language",
    "java": "language",
    "javascript": "language",
    "c++": "language",
    "scala": "language",
    "time-series": "domain",
    "machine learning": "domain",
    "deep learning": "domain",
    "statistics": "domain",
    "optimization": "domain",
    "reinforcement learning": "domain",
    "tensorflow": "framework",
    "pytorch": "framework",
    "scikit-learn": "framework",
    "keras": "framework",
    "pandas": "library",
    "numpy": "library",
    "scipy": "library",
    "matplotlib": "library",
    "seaborn": "library",
    "flask": "framework",
    "django": "framework",
    "fastapi": "framework",
    "azure": "cloud",
    "aws": "cloud",
    "gcp": "cloud",
    "docker": "tool",
    "kubernetes": "tool",
    "spark": "tool",
    "kafka": "tool",
    "mlops": "practice",
    "ci/cd": "practice",
    "feature engineering": "skill",
    "model deployment": "skill",
    "model monitoring": "skill",
    "api development": "skill",
    "cloud computing": "skill",
    "data pipeline": "skill",
    "genai": "domain",
}


def parse_job_description(jd_text: str) -> ParsedJobDescription:
    """
    Parse a job description into structured requirements.

    Args:
        jd_text: Raw job description text

    Returns:
        ParsedJobDescription with extracted skills and requirements
    """
    result = ParsedJobDescription(raw_text=jd_text)

    # Extract title (usually first line or near "Job Title" or "Position")
    result.title = _extract_title(jd_text)

    # Extract experience requirements
    result.experience_requirement = _extract_experience(jd_text)

    # Extract responsibilities
    result.responsibilities = _extract_responsibilities(jd_text)

    # Extract key focus areas
    result.key_focus_areas = _extract_key_focus_areas(jd_text)

    # Extract mandatory skills
    result.mandatory_skills = _extract_skills(jd_text, mandatory=True)

    # Extract nice-to-have skills
    result.nice_to_have_skills = _extract_skills(jd_text, mandatory=False)

    # Extract education
    result.education = _extract_education(jd_text)

    return result


def _extract_title(jd_text: str) -> str:
    """Extract job title from JD."""
    lines = jd_text.strip().split('\n')

    # First non-empty line is often the title
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 3 and len(line) < 100:
            # Skip common headers
            if any(header in line.lower() for header in ['job description', 'position:', 'role:']):
                continue
            return line

    return ""


def _extract_experience(jd_text: str) -> Optional[ExperienceRequirement]:
    """Extract years of experience requirement."""
    # Pattern: "3-5 years", "5+ years", "3 years"
    patterns = [
        r'(\d+)\s*[-–to]+\s*(\d+)\s*years?\s*(?:of\s+)?(?:experience|exp)?',
        r'(\d+)\+\s*years?\s*(?:of\s+)?(?:experience|exp)?',
        r'at\s+least\s+(\d+)\s*years?',
    ]

    text_lower = jd_text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            if len(match.groups()) == 2:
                return ExperienceRequirement(
                    years_min=int(match.group(1)),
                    years_max=int(match.group(2)),
                    area=_extract_experience_area(text_lower)
                )
            else:
                return ExperienceRequirement(
                    years_min=int(match.group(1)),
                    years_max=99,  # "5+ years"
                    area=_extract_experience_area(text_lower)
                )

    return None


def _extract_experience_area(text: str) -> str:
    """Extract the area for experience requirement."""
    if 'ai/ml' in text or 'machine learning' in text:
        return 'AI/ML'
    if 'data' in text:
        return 'Data'
    if 'cloud' in text:
        return 'Cloud'
    if 'software' in text:
        return 'Software'
    return 'Industry'


def _extract_responsibilities(jd_text: str) -> list[str]:
    """Extract job responsibilities."""
    responsibilities = []

    # Look for "What You'll Be Doing", "Responsibilities", etc.
    sections = re.split(r'(?:what you[\'"]?ll be doing|responsibilities|duties|key tasks)',
                       jd_text.lower())

    if len(sections) > 1:
        # Extract bullet points from this section
        section_text = sections[1].split('\n\n')[0]
        bullets = re.findall(r'[-•*]\s*([^\n]+)', section_text)
        responsibilities = [b.strip() for b in bullets if len(b.strip()) > 20]

    return responsibilities


def _extract_key_focus_areas(jd_text: str) -> list[str]:
    """Extract key focus areas from JD."""
    focus_areas = []

    # Look for "Key Focus Areas", "Primary Focus", etc.
    text_lower = jd_text.lower()
    patterns = [
        r'key focus areas?[:\s]+([^\n]+(?:\n(?!\n)[^\n]+)*)',
        r'primary focus[:\s]+([^\n]+(?:\n(?!\n)[^\n]+)*)',
        r'core focus[:\s]+([^\n]+(?:\n(?!\n)[^\n]+)*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            text = match.group(1)
            # Split by common delimiters
            areas = re.split(r'[,;•-]', text)
            focus_areas.extend([a.strip() for a in areas if len(a.strip()) > 5])

    # If no explicit focus areas, infer from responsibilities
    if not focus_areas:
        resp_lower = str(_extract_responsibilities(jd_text)).lower()
        if 'time-series' in resp_lower or 'forecast' in resp_lower:
            focus_areas.append("Time-series forecasting & prediction")
        if 'optimization' in resp_lower:
            focus_areas.append("Process optimization")
        if 'pipeline' in resp_lower:
            focus_areas.append("End-to-end ML pipeline development")
        if 'deploy' in resp_lower:
            focus_areas.append("ML model deployment")

    return focus_areas


def _extract_skills(jd_text: str, mandatory: bool = True) -> list[SkillRequirement]:
    """Extract skills from JD."""
    skills = []
    text_lower = jd_text.lower()

    # Determine which section to parse
    section_name = "looking for" if mandatory else "nice to have"
    section_pattern = f"{section_name}[:\s]+(.{{1000}})"

    if mandatory:
        # Parse "What We Are Looking For" or similar
        patterns = [
            r'what (?:we )?(?:are )?(?:looking for|want)[:\s]+(.{{2000}})',
            r'required[:\s]+(.{{2000}})',
            r'qualifications[:\s]+(.{{2000}})',
            r'skills?[:\s]+(.{{2000}})',
        ]
    else:
        # Parse "Nice to Have" or similar
        patterns = [
            r'nice to have[:\s]+(.{{1000}})',
            r'good to have[:\s]+(.{{1000}})',
            r'preferred[:\s]+(.{{1000}})',
            r'bonus[:\s]+(.{{1000}})',
        ]

    section_text = ""
    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            section_text = match.group(1).split('\n\n')[0]
            break

    if not section_text:
        section_text = text_lower  # Fall back to full text

    # Match skills from the section
    for skill, alternatives in SKILL_ALTERNATIVES.items():
        for alt in alternatives:
            if alt in section_text:
                # Get context (surrounding text)
                idx = section_text.find(alt)
                start = max(0, idx - 50)
                end = min(len(section_text), idx + len(alt) + 50)
                context = section_text[start:end]

                # Determine weight based on emphasis
                weight = 1.0
                if any(emph in context for emph in ['strong', 'extensive', 'proven']):
                    weight = 1.2
                if any(emph in context for emph in ['basic', 'familiarity', 'exposure']):
                    weight = 0.7

                skills.append(SkillRequirement(
                    skill=skill,
                    category=SKILL_CATEGORIES.get(skill, 'skill'),
                    weight=weight,
                    is_mandatory=mandatory,
                    context=context.strip(),
                    keywords=alternatives
                ))
                break  # Only add once per skill

    return skills


def _extract_education(jd_text: str) -> list[str]:
    """Extract education requirements."""
    education = []
    text_lower = jd_text.lower()

    patterns = [
        r'(?:bachelor|bs|ba|b\.s\.|b\.a\.)\s*(?:[\'\"]?s)?(?:\'s)?\s*(?:in|of)?\s*([^\n•]+)',
        r'(?:master|ms|ma|m\.s\.|m\.a\.)\s*(?:[\'\"]?s)?(?:\'s)?\s*(?:in|of)?\s*([^\n•]+)',
        r'(?:phd|ph\.d\.)\s*(?:in|of)?\s*([^\n•]+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if match and len(match) > 2:
                education.append(match.strip())

    return education[:5]  # Limit to 5 items


def print_parsed_jd(parsed: ParsedJobDescription) -> str:
    """Generate a human-readable summary of parsed JD."""
    lines = []

    if parsed.title:
        lines.append(f"Title: {parsed.title}")
        lines.append("")

    if parsed.experience_requirement:
        exp = parsed.experience_requirement
        if exp.years_max == 99:
            lines.append(f"Experience: {exp.years_min}+ years in {exp.area}")
        else:
            lines.append(f"Experience: {exp.years_min}-{exp.years_max} years in {exp.area}")
        lines.append("")

    lines.append(f"Mandatory Skills ({len(parsed.mandatory_skills)}):")
    for skill in parsed.mandatory_skills[:10]:
        lines.append(f"  • {skill.skill} ({skill.category})")
    if len(parsed.mandatory_skills) > 10:
        lines.append(f"  ... and {len(parsed.mandatory_skills) - 10} more")
    lines.append("")

    if parsed.nice_to_have_skills:
        lines.append(f"Nice to Have ({len(parsed.nice_to_have_skills)}):")
        for skill in parsed.nice_to_have_skills[:5]:
            lines.append(f"  • {skill.skill}")
        lines.append("")

    if parsed.key_focus_areas:
        lines.append("Key Focus Areas:")
        for area in parsed.key_focus_areas:
            lines.append(f"  • {area}")

    return "\n".join(lines)
