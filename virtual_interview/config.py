"""
Configuration for Virtual Interview Engine
==========================================
All settings are centralized here - no magic numbers in code.
Modify this file to customize behavior.
"""

# API Configuration (OpenAI-compatible with Claude model)
API_CONFIG = {
    "base_url": "https://api.codemax.pro/v1",
    "api_key": "sk-cp-6e5fac61711d4d1e8b57cf2d35315cf1", 
    "model": "claude-opus-4-6",
    "max_tokens": 2000,
    "temperature": 0.7
}

# Evaluation Configuration
EVALUATION_CONFIG = {
    # Depth thresholds (0-1 scale)
    "depth_thresholds": {
        "low": 0.4,      # Below this = low depth
        "medium": 0.7,   # Above low, below high = medium
        "high": 0.7      # This and above = high
    },
    
    # Score weights for computing overall score
    "weights": {
        "correctness": 0.4,
        "clarity": 0.3,
        "depth": 0.3
    }
}

# Assessment Configuration
ASSESSMENT_CONFIG = {
    "max_hints_per_skill": 2,           # Max hints before moving on
    "max_questions_per_skill": 5,       # Max questions per skill
    "reask_improvement_threshold": 0.2, # Must improve by this after hint
    "min_answer_length": 10,            # Minimum characters for valid answer
}

# Scoring Configuration
SCORING_CONFIG = {
    "base_score_per_question": 0.15,   # Points per question answered
    "hint_penalty": 0.05,              # Deducted per hint used
    "followup_bonus": 0.05,            # Bonus for completing follow-up
    "interview_bonus": 0.10,           # Bonus for passing interview phase
}

# Recommendation Thresholds
RECOMMENDATION_CONFIG = {
    "hire_threshold": 0.75,            # Final score >= this = Hire
    "maybe_threshold": 0.5,            # Final score >= this = Maybe
    # Below maybe_threshold = No
}

# TTS Configuration
TTS_CONFIG = {
    "enabled": True,
    "lang": "en",
    "slow": False,  # Normal speed
}

# Avatar Configuration (HeyGen)
AVATAR_CONFIG = {
    "enabled": False,  # Set to True when HeyGen is configured
    "api_key": "your-heygen-api-key",
    "avatar_id": "your-avatar-id",
    "use_for": ["intro", "summary"]  # Only use avatar at start/end
}

# File Paths
PATHS = {
    "rubrics_dir": "rubrics",
    "prompts_dir": "prompts",
    "output_dir": "output",
    "sample_input": "sample_input.json",
    "output_file": "assessment_delta.json",
}

def get_config(key: str) -> dict:
    """Get a configuration section by key."""
    return {
        "api": API_CONFIG,
        "evaluation": EVALUATION_CONFIG,
        "assessment": ASSESSMENT_CONFIG,
        "scoring": SCORING_CONFIG,
        "recommendation": RECOMMENDATION_CONFIG,
        "tts": TTS_CONFIG,
        "avatar": AVATAR_CONFIG,
        "paths": PATHS,
    }.get(key, {})

def validate_config():
    """Validate that all required configuration values are set."""
    errors = []
    
    if "your-api-key" in API_CONFIG["api_key"]:
        errors.append("API key not configured - please update config.py")
    
    if API_CONFIG["base_url"] == "":
        errors.append("API base URL is empty")
    
    return errors
