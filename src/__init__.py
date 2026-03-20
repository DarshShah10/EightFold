"""
EightFold Talent Intelligence - Integrated Modules
=================================================

Modules from the Techkriti collaboration that enhance the EightFold system:
- JD Context Analyzer (adaptive scoring weights)
- Adaptive Scoring Engine (gap analysis + time-to-productivity)
- Skill Embedder (FAISS semantic matching)
- JD Extractor (LLM + keyword fallback)
- PDF Resume Parser (Docling + PyMuPDF)
- Cross-Validator (resume vs GitHub authenticity)
"""

from .skill_embedder import SkillEmbedder, batch_normalize_skills, normalize_skill
from .jd_context_analyzer import JDContextAnalyzer, analyze_jd
from .scoring_engine import AdaptiveScoringEngine, AdaptiveWeights
from .jd_extractor import extract_skills_from_jd, extract_skills_fallback, get_skill_adjacent
from .cross_validator import CrossValidator, SkillTrajectoryAnalyzer, ProjectComplexityAnalyzer
from .pdf_resume_parser import AdvancedResumeParser, get_resume_parser
from .github_fetcher import generate_synthetic_profile

__all__ = [
    # Skill Embedding
    "SkillEmbedder",
    "batch_normalize_skills",
    "normalize_skill",
    # JD Context
    "JDContextAnalyzer",
    "analyze_jd",
    # Scoring
    "AdaptiveScoringEngine",
    "AdaptiveWeights",
    # JD Extraction
    "extract_skills_from_jd",
    "extract_skills_fallback",
    "get_skill_adjacent",
    # Cross-validation
    "CrossValidator",
    "SkillTrajectoryAnalyzer",
    "ProjectComplexityAnalyzer",
    # PDF Parsing
    "AdvancedResumeParser",
    "get_resume_parser",
    # Synthetic profiles
    "generate_synthetic_profile",
]
