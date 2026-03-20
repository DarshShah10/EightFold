"""
Dependency Analyzer Package
==========================
Analyzes dependency files to determine engineering philosophy.

Extracts:
- Engineering philosophy (productivity vs performance, research vs production)
- Ecosystem alignment
- Technology trends
"""

from modules.dependency_analyzer.analyzer import DependencyAnalyzer, analyze_dependencies

__all__ = [
    "DependencyAnalyzer",
    "analyze_dependencies",
]
