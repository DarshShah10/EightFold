"""
Job Description Parser
======================
Extracts requirements, skills, and priorities from job descriptions
to dynamically configure the scoring engine.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class JobRequirement:
    """A single requirement extracted from JD."""
    skill: str
    category: str  # technical, soft_skill, tool, language, practice
    importance: float  # 0.0 - 1.0
    keywords: List[str] = field(default_factory=list)


@dataclass
class PriorityWeights:
    """Adjusted weights based on JD priorities."""
    cognitive_load: float = 0.25
    temporal_patterns: float = 0.10
    code_hygiene: float = 0.25
    problem_solving: float = 0.25
    engineering_maturity: float = 0.15


@dataclass
class JDParsed:
    """Complete JD analysis result."""
    # Raw requirements
    requirements: List[JobRequirement] = field(default_factory=list)

    # Priority weights (adjusted from JD)
    weights: PriorityWeights = field(default_factory=PriorityWeights)

    # Role type inference
    inferred_role_type: str = "generalist"  # frontend, backend, fullstack, devops, ml, etc.

    # Key signals to emphasize
    emphasized_signals: List[str] = field(default_factory=list)

    # Anti-signals (what we DON'T want)
    anti_signals: List[str] = field(default_factory=list)

    # Preferred personality archetypes
    preferred_archetypes: List[str] = field(default_factory=list)

    # Minimum thresholds
    minimum_thresholds: Dict[str, float] = field(default_factory=dict)

    # Raw JD text (for LLM analysis)
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requirements": [
                {
                    "skill": r.skill,
                    "category": r.category,
                    "importance": r.importance,
                    "keywords": r.keywords,
                }
                for r in self.requirements
            ],
            "weights": {
                "cognitive_load": self.weights.cognitive_load,
                "temporal_patterns": self.weights.temporal_patterns,
                "code_hygiene": self.weights.code_hygiene,
                "problem_solving": self.weights.problem_solving,
                "engineering_maturity": self.weights.engineering_maturity,
            },
            "inferred_role_type": self.inferred_role_type,
            "emphasized_signals": self.emphasized_signals,
            "anti_signals": self.anti_signals,
            "preferred_archetypes": self.preferred_archetypes,
            "minimum_thresholds": self.minimum_thresholds,
        }


class JDParser:
    """
    Parses job descriptions to extract requirements and adjust scoring.

    Supports:
    - Technical skills (Python, JavaScript, etc.)
    - Practices (TDD, CI/CD, Agile)
    - Soft skills (leadership, communication)
    - Tools/Platforms (AWS, Docker, Kubernetes)
    """

    # Skill category patterns
    SKILL_PATTERNS = {
        "language": {
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
            "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css"
        },
        "frontend": {
            "react", "vue", "angular", "svelte", "next.js", "nuxt", "gatsby",
            "redux", "tailwind", "sass", "webpack", "vite"
        },
        "backend": {
            "django", "flask", "fastapi", "express", "spring", "rails", "laravel",
            "node.js", "graphql", "rest", "api", "microservices"
        },
        "data": {
            "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
            "spark", "hadoop", "kafka", "airflow", "dbt", "tableau", "power bi"
        },
        "devops": {
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible",
            "jenkins", "github actions", "gitlab ci", "circleci", "prometheus",
            "grafana", "elk", "datadog", "new relic"
        },
        "database": {
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
            "dynamodb", "sqlite", "oracle", "sql server"
        },
        "practice": {
            "tdd", "test-driven", "agile", "scrum", "kanban", "devops", "devsecops",
            "code review", "pair programming", "clean code", "solid principles"
        },
        "soft_skill": {
            "leadership", "communication", "mentoring", "team player", "problem-solving",
            "collaboration", "mentorship", "presentation", "documentation"
        },
    }

    # Role type indicators
    ROLE_INDICATORS = {
        "frontend": ["frontend", "front-end", "ui developer", "web developer", "react", "vue", "angular"],
        "backend": ["backend", "back-end", "api developer", "server developer"],
        "fullstack": ["fullstack", "full-stack", "full stack"],
        "devops": ["devops", "sre", "site reliability", "platform engineer", "infrastructure"],
        "ml": ["machine learning", "ml engineer", "data scientist", "ai", "deep learning", "nlp"],
        "mobile": ["mobile", "ios", "android", "react native", "flutter"],
        "security": ["security", "appsec", "security engineer", "penetration"],
        "data": ["data engineer", "analytics", "bi", "data analyst"],
    }

    # Signal importance mapping for different roles
    ROLE_SIGNAL_PREFERENCES = {
        "frontend": {
            "emphasized": ["code_hygiene", "consistency_score", "test_coverage_ratio"],
            "archetypes": ["code_artisan", "feature_factory"],
            "weights": {"code_hygiene": 0.30, "problem_solving": 0.25, "cognitive_load": 0.20}
        },
        "backend": {
            "emphasized": ["architectural_complexity_score", "refactor_ratio", "performance_score"],
            "archetypes": ["architect", "code_artisan"],
            "weights": {"cognitive_load": 0.30, "problem_solving": 0.25, "engineering_maturity": 0.20}
        },
        "fullstack": {
            "emphasized": ["cross_boundary_commit_ratio", "multi_module_commit_ratio", "test_coverage_ratio"],
            "archetypes": ["architect", "feature_factory"],
            "weights": {"cognitive_load": 0.25, "problem_solving": 0.25, "code_hygiene": 0.20}
        },
        "devops": {
            "emphasized": ["ci_pipeline_ratio", "github_actions_ratio", "engineering_maturity_score"],
            "archetypes": ["devops_champion", "architect"],
            "weights": {"engineering_maturity": 0.35, "cognitive_load": 0.20, "code_hygiene": 0.20}
        },
        "ml": {
            "emphasized": ["data_analysis_patterns", "research_commits", "experiment_tracking"],
            "archetypes": ["researcher", "code_artisan"],
            "weights": {"problem_solving": 0.35, "cognitive_load": 0.25, "code_hygiene": 0.15}
        },
    }

    def __init__(self):
        """Initialize parser with compiled patterns."""
        self._skill_pattern = self._build_skill_pattern()
        self._importance_patterns = self._build_importance_patterns()

    def _build_skill_pattern(self) -> re.Pattern:
        """Build regex pattern for skills."""
        all_skills = set()
        for category_skills in self.SKILL_PATTERNS.values():
            all_skills.update(category_skills)

        # Create pattern that matches skill boundaries
        skills_regex = "|".join(re.escape(s) for s in all_skills)
        return re.compile(rf'\b({skills_regex})\b', re.IGNORECASE)

    def _build_importance_patterns(self) -> Dict[str, Tuple[re.Pattern, float]]:
        """Build patterns for extracting importance levels."""
        return {
            "required": (re.compile(r'(?:required|must have|essential|minimum)', re.IGNORECASE), 1.0),
            "preferred": (re.compile(r'(?:preferred|nice to have|bonus|desired)', re.IGNORECASE), 0.7),
            "nice": (re.compile(r'(?:plus|extra|additional)', re.IGNORECASE), 0.4),
        }

    def parse(self, jd_text: str) -> JDParsed:
        """
        Parse a job description and extract requirements.

        Args:
            jd_text: Raw job description text

        Returns:
            JDParsed with extracted requirements and adjusted weights
        """
        result = JDParsed()
        result.raw_text = jd_text

        # Extract skills
        requirements = self._extract_skills(jd_text)
        result.requirements = requirements

        # Infer role type
        result.inferred_role_type = self._infer_role_type(jd_text)

        # Adjust weights based on role
        result.weights = self._adjust_weights_for_role(result.inferred_role_type)

        # Get role-specific preferences
        role_prefs = self.ROLE_SIGNAL_PREFERENCES.get(result.inferred_role_type, {})
        result.emphasized_signals = role_prefs.get("emphasized", [])
        result.preferred_archetypes = role_prefs.get("archetypes", [])

        # Extract explicit priorities from JD
        priorities = self._extract_priorities(jd_text)
        if priorities:
            result.weights = self._adjust_weights_from_priorities(result.weights, priorities)

        # Extract anti-signals (deal breakers)
        result.anti_signals = self._extract_anti_signals(jd_text)

        # Extract minimum thresholds
        result.minimum_thresholds = self._extract_thresholds(jd_text)

        return result

    def parse_from_file(self, file_path: str) -> JDParsed:
        """Parse JD from a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return self.parse(f.read())

    def _extract_skills(self, text: str) -> List[JobRequirement]:
        """Extract skills and their importance from text."""
        requirements = []
        text_lower = text.lower()

        # Find all skill matches
        matched_skills = set()
        for match in self._skill_pattern.finditer(text):
            skill = match.group().lower()
            if skill not in matched_skills:
                matched_skills.add(skill)

                # Determine importance
                importance = 0.5  # default
                for level, (pattern, weight) in self._importance_patterns.items():
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(text), match.end() + 100)
                    context = text[context_start:context_end].lower()

                    if pattern.search(context):
                        importance = max(importance, weight)
                        break

                # Determine category
                category = self._get_skill_category(skill)

                requirements.append(JobRequirement(
                    skill=skill,
                    category=category,
                    importance=importance,
                    keywords=[skill]
                ))

        return requirements

    def _get_skill_category(self, skill: str) -> str:
        """Get the category of a skill."""
        skill_lower = skill.lower()
        for category, skills in self.SKILL_PATTERNS.items():
            if skill_lower in skills:
                return category
        return "other"

    def _infer_role_type(self, text: str) -> str:
        """Infer the role type from JD text."""
        text_lower = text.lower()
        scores = {}

        for role, indicators in self.ROLE_INDICATORS.items():
            score = sum(1 for ind in indicators if ind in text_lower)
            if score > 0:
                scores[role] = score

        if not scores:
            return "generalist"

        return max(scores, key=scores.get)

    def _adjust_weights_for_role(self, role_type: str) -> PriorityWeights:
        """Get adjusted weights for a specific role type."""
        base = PriorityWeights()

        if role_type in self.ROLE_SIGNAL_PREFERENCES:
            prefs = self.ROLE_SIGNAL_PREFERENCES[role_type]
            weights = prefs.get("weights", {})

            # Normalize weights to 1.0
            total = sum(weights.values())
            if total > 0:
                base = PriorityWeights(
                    cognitive_load=weights.get("cognitive_load", 0.25) / total,
                    temporal_patterns=0.10,
                    code_hygiene=weights.get("code_hygiene", 0.25) / total,
                    problem_solving=weights.get("problem_solving", 0.25) / total,
                    engineering_maturity=weights.get("engineering_maturity", 0.15) / total,
                )

        return base

    def _extract_priorities(self, text: str) -> Dict[str, float]:
        """Extract explicit priority signals from text."""
        priorities = {}

        priority_keywords = {
            "quality": ["quality", "best practices", "clean code", "maintainable"],
            "speed": ["fast", "agile", "velocity", "ship", "deliver"],
            "architecture": ["architecture", "scalable", "design", "system design"],
            "collaboration": ["team", "collaboration", "mentor", "lead", "communicate"],
            "innovation": ["innovate", "research", "experiment", "novel"],
        }

        text_lower = text.lower()
        for priority, keywords in priority_keywords.items():
            count = sum(text_lower.count(kw) for kw in keywords)
            if count > 0:
                priorities[priority] = min(count / 5, 1.0)  # Normalize

        return priorities

    def _adjust_weights_from_priorities(
        self,
        base: PriorityWeights,
        priorities: Dict[str, float]
    ) -> PriorityWeights:
        """Adjust weights based on extracted priorities."""
        adjusted = PriorityWeights(
            cognitive_load=base.cognitive_load,
            temporal_patterns=base.temporal_patterns,
            code_hygiene=base.code_hygiene,
            problem_solving=base.problem_solving,
            engineering_maturity=base.engineering_maturity,
        )

        # Map priorities to dimensions
        priority_map = {
            "quality": ("code_hygiene", 0.15),
            "architecture": ("cognitive_load", 0.15),
            "collaboration": ("temporal_patterns", 0.10),
            "innovation": ("problem_solving", 0.10),
        }

        for priority, intensity in priorities.items():
            if priority in priority_map:
                dim, adjustment = priority_map[priority]
                old_value = getattr(adjusted, dim)
                new_value = min(1.0, old_value + intensity * adjustment)
                setattr(adjusted, dim, new_value)

        # Renormalize weights
        total = (
            adjusted.cognitive_load +
            adjusted.temporal_patterns +
            adjusted.code_hygiene +
            adjusted.problem_solving +
            adjusted.engineering_maturity
        )

        if total > 0 and abs(total - 1.0) > 0.01:
            factor = 1.0 / total
            adjusted = PriorityWeights(
                cognitive_load=adjusted.cognitive_load * factor,
                temporal_patterns=adjusted.temporal_patterns * factor,
                code_hygiene=adjusted.code_hygiene * factor,
                problem_solving=adjusted.problem_solving * factor,
                engineering_maturity=adjusted.engineering_maturity * factor,
            )

        return adjusted

    def _extract_anti_signals(self, text: str) -> List[str]:
        """Extract deal-breaker anti-signals."""
        anti_signals = []
        text_lower = text.lower()

        anti_keywords = {
            "no_startups": ["startup experience", "startup environment"],
            "no_legacy": ["no legacy", "modern codebase", "greenfield"],
            "senior_only": ["senior only", "5+ years", "7+ years"],
            "remote_only": ["remote only", "work from home"],
        }

        for signal, keywords in anti_keywords.items():
            if any(kw in text_lower for kw in keywords):
                anti_signals.append(signal)

        return anti_signals

    def _extract_thresholds(self, text: str) -> Dict[str, float]:
        """Extract minimum thresholds from text."""
        thresholds = {}

        # Look for specific threshold mentions
        patterns = [
            (r'(\d+)%\s*test\s*coverage', 'test_coverage_ratio'),
            (r'(\d+)\+\s*(?:years|yrs)', 'min_experience_years'),
            (r'at\s+least\s+(\d+)\s*commits', 'min_commits'),
        ]

        for pattern, threshold_name in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if threshold_name == 'test_coverage_ratio':
                    value = value / 100  # Convert to ratio
                thresholds[threshold_name] = value

        return thresholds
