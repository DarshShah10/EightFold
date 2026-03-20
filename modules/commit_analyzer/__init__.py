"""
Commit Intelligence Engine
==========================
State-of-the-art commit analysis extracting 30+ behavioral signals.

Submodules:
- analyzers: Individual signal analyzers (cognitive, temporal, hygiene, problem-solving, maturity)
- scoring: Commit Intelligence Score computation
- profiles: Developer personality classification
- types: Shared dataclass definitions
- jd_parser: Job description parsing for role-specific analysis
- llm_client: LLM integration for intelligent insights
- enhanced_engine: JD-driven and LLM-powered analysis
"""

from modules.commit_analyzer.engine import CommitIntelligenceEngine, analyze_commits
from modules.commit_analyzer.enhanced_engine import EnhancedIntelligenceEngine, analyze_with_jd
from modules.commit_analyzer.jd_parser import JDParser, JDParsed
from modules.commit_analyzer.llm_client import LLMClient, get_llm_client
from modules.commit_analyzer.types import (
    CommitIntelligenceResult,
    DeveloperProfile,
    CommitCitation,
)

__all__ = [
    # Core engine
    "CommitIntelligenceEngine",
    "analyze_commits",
    # Enhanced engine
    "EnhancedIntelligenceEngine",
    "analyze_with_jd",
    # JD parsing
    "JDParser",
    "JDParsed",
    # LLM
    "LLMClient",
    "get_llm_client",
    # Types
    "CommitIntelligenceResult",
    "DeveloperProfile",
    "CommitCitation",
]
