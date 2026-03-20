"""
Explainability Package
======================
Generates human-readable explanations for skill assessments.

Provides "We believe X because Y" style output with full provenance chains.

Usage:
    from modules.explainability import ExplainabilityEngine, explain_skill_intelligence

    explainable_result = explain_skill_intelligence(raw_data, skill_result)
"""

from modules.explainability.explainer import ExplainabilityEngine, explain_skill_intelligence
from modules.explainability.types import (
    EvidenceItem,
    EvidenceSource,
    ExplainableSkill,
    ExplainableResult,
    ProjectEvidence,
    ProblemTrace,
)

__version__ = "1.0.0"

__all__ = [
    "ExplainabilityEngine",
    "explain_skill_intelligence",
    "EvidenceItem",
    "EvidenceSource",
    "ExplainableSkill",
    "ExplainableResult",
    "ProjectEvidence",
    "ProblemTrace",
]
