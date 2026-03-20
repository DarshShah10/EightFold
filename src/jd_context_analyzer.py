"""
JD Context Analyzer - Adaptive Weight System
==========================================

The scoring weights automatically ADAPT based on:
1. Company/Industry Type (detected from JD)
2. Role Seniority Level
3. JD Emphasis Patterns

Example:
- Bank hiring → Higher soft skills weight, compliance signals
- Startup hiring → Higher learning velocity, technical breadth
- Research lab → Higher ML depth, publications signal
"""

import json
from typing import Dict, List, Tuple
import re


class JDContextAnalyzer:
    """
    Analyzes job description to understand context and adapt scoring weights.

    This is the KEY INNOVATION: The system doesn't just match skills,
    it UNDERSTANDS what the company values and weights accordingly.
    """

    # Industry signal words
    INDUSTRY_PATTERNS = {
        "fintech_banking": {
            "keywords": [
                "bank", "fintech", "financial", "investment", "trading", "stock",
                "payment", "insurance", "compliance", "regulation", "risk",
                "fraud", "transaction", "ledger", "ledger", "audit", "tax",
                "wealth management", "capital", "loan", "credit", "mortgage",
                "SEC", "FINRA", "PCI", "KYC", "AML"
            ],
            "default_weights": {
                "soft_skills_match": 0.25,  # Communication critical
                "cultural_fit": 0.15,
                "technical_depth": 0.20,
                "verified_skill_match": 0.20,
                "learning_velocity": 0.10,
                "project_complexity": 0.10
            },
            "description": "Finance/Banking - prioritizes soft skills, compliance awareness"
        },
        "healthcare": {
            "keywords": [
                "healthcare", "medical", "hospital", "HIPAA", "patient",
                "clinical", "EHR", "EMR", "pharma", "biotech", "life sciences",
                "diagnostic", "treatment", "health record", "telehealth"
            ],
            "default_weights": {
                "soft_skills_match": 0.25,
                "cultural_fit": 0.15,
                "technical_depth": 0.20,
                "verified_skill_match": 0.20,
                "learning_velocity": 0.10,
                "project_complexity": 0.10
            },
            "description": "Healthcare - prioritizes soft skills, compliance"
        },
        "tech_startup": {
            "keywords": [
                "startup", "scale-up", " Series", "funding", "venture",
                "agile", "fast-paced", "wear multiple hats", "flexible",
                "growth-stage", "high-energy", "move fast"
            ],
            "default_weights": {
                "learning_velocity": 0.30,  # Must learn fast
                "technical_breadth": 0.20,  # Wear multiple hats
                "verified_skill_match": 0.20,
                "soft_skills_match": 0.10,
                "project_complexity": 0.10,
                "cultural_fit": 0.10
            },
            "description": "Startup - prioritizes learning speed, adaptability"
        },
        "tech_enterprise": {
            "keywords": [
                "enterprise", "FAANG", "tech giant", "infrastructure",
                "scale", "millions of users", "distributed systems",
                "microservices", "cloud-native", "SRE"
            ],
            "default_weights": {
                "technical_depth": 0.30,  # Deep expertise needed
                "verified_skill_match": 0.25,
                "project_complexity": 0.15,
                "learning_velocity": 0.10,
                "soft_skills_match": 0.10,
                "cultural_fit": 0.10
            },
            "description": "Tech Enterprise - prioritizes deep technical skills"
        },
        "ecommerce": {
            "keywords": [
                "e-commerce", "retail", "marketplace", "shopping",
                "inventory", "fulfillment", "logistics", "last-mile",
                "recommendation", "search", "catalog"
            ],
            "default_weights": {
                "verified_skill_match": 0.30,
                "technical_depth": 0.20,
                "project_complexity": 0.15,
                "learning_velocity": 0.15,
                "soft_skills_match": 0.10,
                "cultural_fit": 0.10
            },
            "description": "E-commerce - balanced technical + speed"
        },
        "ai_ml_research": {
            "keywords": [
                "research", "ML", "machine learning", "deep learning",
                "NLP", "computer vision", "AI", "model", "training",
                "paper", "publication", "PhD", "academic", "scientist",
                "algorithm", "optimization", "benchmark"
            ],
            "default_weights": {
                "technical_depth": 0.35,  # Must be cutting-edge
                "verified_skill_match": 0.25,
                "learning_velocity": 0.15,
                "project_complexity": 0.10,
                "soft_skills_match": 0.08,
                "cultural_fit": 0.07
            },
            "description": "AI/ML Research - prioritizes deep technical expertise"
        },
        "government": {
            "keywords": [
                "government", "federal", "state", "public sector",
                "clearance", "security clearance", "citizen",
                "civic", "department", "agency", "compliance"
            ],
            "default_weights": {
                "soft_skills_match": 0.25,
                "cultural_fit": 0.20,
                "verified_skill_match": 0.25,
                "project_complexity": 0.10,
                "learning_velocity": 0.10,
                "technical_depth": 0.10
            },
            "description": "Government - prioritizes soft skills, cultural fit"
        },
        "consulting": {
            "keywords": [
                "consulting", "client-facing", "stakeholder",
                "presentation", "workshop", "roadmap", "strategy",
                "advisory", "enterprise", "solutions architect"
            ],
            "default_weights": {
                "soft_skills_match": 0.30,  # Client interaction critical
                "cultural_fit": 0.15,
                "learning_velocity": 0.20,
                "verified_skill_match": 0.15,
                "technical_depth": 0.10,
                "project_complexity": 0.10
            },
            "description": "Consulting - prioritizes soft skills, adaptability"
        },
        "product": {
            "keywords": [
                "product", "PM", "product manager", "roadmap",
                "stakeholder", "user research", "A/B testing",
                "metrics", "KPI", "launch", "feature"
            ],
            "default_weights": {
                "soft_skills_match": 0.30,
                "learning_velocity": 0.20,
                "cultural_fit": 0.15,
                "verified_skill_match": 0.15,
                "technical_depth": 0.10,
                "project_complexity": 0.10
            },
            "description": "Product - prioritizes soft skills, learning agility"
        },
        "default": {
            "keywords": [],
            "default_weights": {
                "verified_skill_match": 0.30,
                "technical_depth": 0.20,
                "learning_velocity": 0.20,
                "soft_skills_match": 0.15,
                "project_complexity": 0.08,
                "cultural_fit": 0.07
            },
            "description": "General - balanced approach"
        }
    }

    # Seniority signal words
    SENIORITY_PATTERNS = {
        "entry": {
            "keywords": ["entry", "junior", "intern", "graduate", "new grad", "0-2", "0-3", "1-2"],
            "adjustments": {
                "learning_velocity": 0.05,  # Higher weight - can they grow?
                "soft_skills_match": 0.05,   # Higher - culture fit for learning
                "technical_depth": -0.10     # Lower - don't need deep expertise
            }
        },
        "mid": {
            "keywords": ["mid-level", "intermediate", "3-5", "4-6", "software engineer II", "developer II"],
            "adjustments": {
                "verified_skill_match": 0.05,
                "learning_velocity": 0.05,
                "technical_depth": 0.05,
                "project_complexity": -0.05,
                "soft_skills_match": -0.05
            }
        },
        "senior": {
            "keywords": ["senior", "Sr.", "Sr ", "5+", "7+", "10+", "lead", "principal", "staff"],
            "adjustments": {
                "technical_depth": 0.10,     # Higher - need expertise
                "project_complexity": 0.05,  # Higher - lead complex projects
                "soft_skills_match": 0.05,  # Higher - mentor others
                "verified_skill_match": -0.05,
                "learning_velocity": -0.10,  # Lower - fundamentals assumed
                "cultural_fit": -0.05
            }
        },
        "executive": {
            "keywords": ["director", "VP", "vice president", "chief", "CTO", "CISO", "CFO"],
            "adjustments": {
                "soft_skills_match": 0.15,
                "cultural_fit": 0.10,
                "learning_velocity": 0.05,
                "technical_depth": -0.15,
                "verified_skill_match": -0.10
            }
        }
    }

    # Role type patterns
    ROLE_TYPE_PATTERNS = {
        "frontend": {
            "skill_emphasis": ["javascript", "react", "vue", "angular", "css", "html", "typescript", "ui", "ux"],
            "weight_boost": {"technical_depth": 0.10, "verified_skill_match": 0.05}
        },
        "backend": {
            "skill_emphasis": ["python", "java", "go", "rust", "node", "api", "server", "database", "sql"],
            "weight_boost": {"technical_depth": 0.10, "project_complexity": 0.05}
        },
        "fullstack": {
            "skill_emphasis": ["full-stack", "fullstack", "end-to-end", "frontend", "backend"],
            "weight_boost": {"learning_velocity": 0.10, "technical_breadth": 0.05}
        },
        "devops": {
            "skill_emphasis": ["docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ci/cd", "devops", "sre"],
            "weight_boost": {"technical_depth": 0.10, "project_complexity": 0.05}
        },
        "ml_data": {
            "skill_emphasis": ["machine learning", "ml", "data science", "tensorflow", "pytorch", "ai", "nlp", "deep learning"],
            "weight_boost": {"technical_depth": 0.15, "learning_velocity": 0.05}
        },
        "mobile": {
            "skill_emphasis": ["ios", "android", "mobile", "swift", "kotlin", "react native", "flutter"],
            "weight_boost": {"technical_depth": 0.10, "verified_skill_match": 0.05}
        }
    }

    def analyze_jd_context(self, jd_text: str) -> Dict:
        """
        Analyze job description and return:
        1. Detected industry
        2. Detected seniority
        3. Detected role type
        4. Calculated adaptive weights
        """
        jd_lower = jd_text.lower()

        # Detect industry
        industry = self._detect_industry(jd_lower)

        # Detect seniority
        seniority = self._detect_seniority(jd_lower)

        # Detect role type
        role_type = self._detect_role_type(jd_lower)

        # Calculate adaptive weights
        weights = self._calculate_adaptive_weights(industry, seniority, role_type, jd_lower)

        return {
            "detected_industry": industry,
            "detected_seniority": seniority,
            "detected_role_type": role_type,
            "adaptive_weights": weights,
            "explanation": self._generate_weight_explanation(industry, seniority, role_type, weights),
            "jd_signals": self._extract_jd_signals(jd_text)
        }

    def _detect_industry(self, jd_lower: str) -> str:
        """Detect industry from JD keywords."""
        scores = {}

        for industry, config in self.INDUSTRY_PATTERNS.items():
            if industry == "default":
                continue

            score = 0
            for keyword in config["keywords"]:
                if keyword.lower() in jd_lower:
                    score += 1

            if score > 0:
                scores[industry] = score

        if scores:
            return max(scores, key=scores.get)

        return "default"

    def _detect_seniority(self, jd_lower: str) -> str:
        """Detect seniority level from JD."""
        for level, config in self.SENIORITY_PATTERNS.items():
            for keyword in config["keywords"]:
                if keyword.lower() in jd_lower:
                    return level

        return "mid"

    def _detect_role_type(self, jd_lower: str) -> str:
        """Detect role type from skill emphasis."""
        scores = {}

        for role, config in self.ROLE_TYPE_PATTERNS.items():
            score = 0
            for skill in config["skill_emphasis"]:
                if skill.lower() in jd_lower:
                    score += 1
            if score > 0:
                scores[role] = score

        if scores:
            return max(scores, key=scores.get)

        return "fullstack"

    def _calculate_adaptive_weights(
        self,
        industry: str,
        seniority: str,
        role_type: str,
        jd_lower: str
    ) -> Dict[str, float]:
        """Calculate final weights by applying adjustments."""
        industry_config = self.INDUSTRY_PATTERNS.get(industry, self.INDUSTRY_PATTERNS["default"])
        weights = industry_config["default_weights"].copy()

        seniority_config = self.SENIORITY_PATTERNS.get(seniority, {})
        seniority_adjustments = seniority_config.get("adjustments", {})

        for key, adjustment in seniority_adjustments.items():
            if key in weights:
                weights[key] = max(0.0, min(0.5, weights[key] + adjustment))

        role_config = self.ROLE_TYPE_PATTERNS.get(role_type, {})
        role_boosts = role_config.get("weight_boost", {})

        for key, boost in role_boosts.items():
            if key in weights:
                weights[key] = min(0.5, weights[key] + boost)

        weights = self._adjust_for_jd_emphasis(weights, jd_lower)

        total = sum(weights.values())
        if total > 0:
            weights = {k: round(v / total, 2) for k, v in weights.items()}

        # ── Floor enforcement: technical signals must always get reasonable weight ──
        # Even for "soft skills" industries (fintech, healthcare), technical_depth
        # and verified_skill_match should never collapse to near-zero for tech roles.
        # We use role type detection: if it's a technical role, enforce floors.
        is_technical_role = role_type in ("backend", "frontend", "fullstack", "devops", "ml_data", "mobile")
        is_tech_industry = industry in ("tech_startup", "tech_enterprise", "ai_ml_research", "ecommerce", "default")
        if is_technical_role or is_tech_industry:
            weights["technical_depth"] = max(weights.get("technical_depth", 0), 0.20)
            weights["verified_skill_match"] = max(weights.get("verified_skill_match", 0), 0.25)
        # Soft skills cap: never exceed 0.25 even in finance/healthcare
        weights["soft_skills_match"] = min(weights.get("soft_skills_match", 0), 0.25)

        # Re-normalize after floors
        total = sum(weights.values())
        if total > 0:
            weights = {k: round(v / total, 2) for k, v in weights.items()}

        all_keys = [
            "verified_skill_match", "technical_depth", "learning_velocity",
            "soft_skills_match", "project_complexity", "cultural_fit",
            "technical_breadth"
        ]
        for key in all_keys:
            weights.setdefault(key, 0.05)

        return weights

    def _adjust_for_jd_emphasis(self, weights: Dict, jd_lower: str) -> Dict:
        """Further adjust weights based on explicit JD emphasis."""
        soft_skill_mentions = sum(1 for word in ["communication", "leadership", "teamwork", "collaboration", "presentation", "stakeholder"] if word in jd_lower)
        technical_mentions = sum(1 for word in ["expert", "deep", "extensive", "proficient", "advanced"] if word in jd_lower)
        learning_mentions = sum(1 for word in ["adaptable", "learn quickly", "fast learner", "self-starter", "growth mindset"] if word in jd_lower)

        if soft_skill_mentions >= 3:
            weights["soft_skills_match"] = min(0.35, weights.get("soft_skills_match", 0.15) + 0.10)

        if technical_mentions >= 3:
            weights["technical_depth"] = min(0.40, weights.get("technical_depth", 0.20) + 0.10)

        if learning_mentions >= 2:
            weights["learning_velocity"] = min(0.35, weights.get("learning_velocity", 0.15) + 0.10)

        return weights

    def _extract_jd_signals(self, jd_text: str) -> Dict:
        """Extract key signals from JD for transparency."""
        jd_lower = jd_text.lower()

        return {
            "explicit_soft_skills": any(word in jd_lower for word in ["communication", "leadership", "teamwork", "presentation"]),
            "explicit_learning_mentioned": any(word in jd_lower for word in ["adaptable", "fast learner", "growth"]),
            "explicit_deep_expertise": any(word in jd_lower for word in ["expert", "deep expertise", "extensive experience"]),
            "mentioned_technologies": len(re.findall(r'(?:AWS|Azure|GCP|Kubernetes|TensorFlow|PyTorch|React|Python|JavaScript)', jd_text)),
        }

    def _generate_weight_explanation(
        self,
        industry: str,
        seniority: str,
        role_type: str,
        weights: Dict
    ) -> str:
        """Generate human-readable explanation of why weights were chosen."""
        parts = []

        industry_desc = self.INDUSTRY_PATTERNS.get(industry, {}).get("description", "")
        if industry_desc:
            parts.append(f"Industry: {industry_desc}")

        seniority_desc = {
            "entry": "Entry-level role - emphasizes learning potential",
            "mid": "Mid-level role - balanced experience and growth",
            "senior": "Senior role - prioritizes expertise and leadership",
            "executive": "Executive role - soft skills and strategic thinking critical"
        }.get(seniority, "")
        if seniority_desc:
            parts.append(f"Seniority: {seniority_desc}")

        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        top_factors = [f"{k.replace('_', ' ').title()} ({v:.0%})" for k, v in sorted_weights[:3]]
        parts.append(f"Top priorities: {', '.join(top_factors)}")

        return " | ".join(parts)

    def get_weighted_scoring_explanation(self, weights: Dict) -> str:
        """Explain what each weight means in context."""
        explanations = {
            "verified_skill_match": "How well candidate's verified skills match job requirements",
            "technical_depth": "Level of expertise and specialization in required technologies",
            "learning_velocity": "How quickly candidate can learn new skills",
            "soft_skills_match": "Alignment of communication and interpersonal skills",
            "project_complexity": "Experience with complex, large-scale projects",
            "cultural_fit": "Alignment with company values and work style",
            "technical_breadth": "Range of technologies candidate is familiar with"
        }

        lines = ["### Scoring Weight Explanation:"]
        for factor, explanation in explanations.items():
            weight = weights.get(factor, 0)
            lines.append(f"- **{factor.replace('_', ' ').title()} ({weight:.0%})**: {explanation}")

        return "\n".join(lines)


# Standalone function for easy use
def analyze_jd(jd_text: str) -> Dict:
    """Quick function to analyze JD and get adaptive weights."""
    analyzer = JDContextAnalyzer()
    return analyzer.analyze_jd_context(jd_text)


if __name__ == "__main__":
    bank_jd = """
    Senior Software Engineer - Banking Platform
    We are looking for a senior engineer with 7+ years experience.
    - Python, Java, SQL
    - Experience with financial systems, compliance, risk management
    - Strong communication and stakeholder management skills
    """

    print("=== BANKING JD ANALYSIS ===")
    result = analyze_jd(bank_jd)
    print(f"Industry: {result['detected_industry']}")
    print(f"Seniority: {result['detected_seniority']}")
    print(f"Weights: {json.dumps(result['adaptive_weights'], indent=2)}")
    print(f"Explanation: {result['explanation']}")
