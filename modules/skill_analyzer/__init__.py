"""
Skill Analyzer Package
=======================
State-of-the-art developer skill intelligence system.

Extracts 10+ signals from GitHub data:
1. Tech Stack Graph - Relationships between technologies
2. Semantic Skills - What developers actually built
3. Domain Fingerprint - Problem spaces (ML, Web3, DevOps)
4. Modernity Score - How current is their stack
5. Depth Index - Specialist vs generalist profile
6. Project Impact - Beyond stars - real significance
7. Ecosystem Alignment - Enterprise tool alignment
8. Learning Velocity - Tech adoption speed
9. Skill Level - Junior/Mid/Senior inference
10. Tech Maturity - Best practices signals
"""

from modules.skill_analyzer.types import (
    TechNode,
    TechGraph,
    SkillSignal,
    DomainProfile,
    DepthIndex,
    StackModernity,
    ProjectImpact,
    SkillProfile,
    SkillIntelligenceResult,
)

from modules.skill_analyzer.engine import SkillAnalyzer

__all__ = [
    # Types
    "TechNode",
    "TechGraph",
    "SkillSignal",
    "DomainProfile",
    "DepthIndex",
    "StackModernity",
    "ProjectImpact",
    "SkillProfile",
    "SkillIntelligenceResult",
    # Main class
    "SkillAnalyzer",
]
