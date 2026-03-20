"""
Virtual Interview Module
========================
Adaptive micro-assessment engine for interviewing candidates.
This module provides skill-based assessment with adaptive difficulty.
"""

from .config import API_CONFIG, ASSESSMENT_CONFIG, SCORING_CONFIG, RECOMMENDATION_CONFIG

__all__ = [
    'API_CONFIG',
    'ASSESSMENT_CONFIG',
    'SCORING_CONFIG',
    'RECOMMENDATION_CONFIG',
]
