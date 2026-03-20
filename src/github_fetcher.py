"""
GitHub Profile Fetcher - Synthetic Profile Generator
Fallback profiles for demo/testing when no GitHub token is available.
"""

import random
from typing import Dict, List


def generate_synthetic_profile(username: str, skill_focus: List[str] = None) -> Dict:
    """
    Generate synthetic candidate profile for testing/demo.

    This is used when:
    - No GitHub token is available
    - The user wants to test the system without API access
    - Demo purposes during hackathon presentation
    """
    if skill_focus is None:
        skill_focus = ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS"]

    return {
        "username": username,
        "name": f"Candidate {username}",
        "raw_skills_list": skill_focus,
        "seniority_indicators": random.sample(
            ["recognized_projects", "community_contributor", "high_quality_repos"],
            k=min(2, 3)
        ),
        "metrics": {
            "total_stars": random.randint(10, 500),
            "total_forks": random.randint(5, 100),
            "avg_stars_per_repo": round(random.uniform(5, 50), 2),
            "activity_consistency": round(random.uniform(0.5, 1.0), 2),
            "recent_activity_count": random.randint(3, 15),
            "total_repos": random.randint(5, 30),
        },
        "repositories": [
            {
                "name": f"project-{i}",
                "description": f"A {skill_focus[i % len(skill_focus)]} project",
                "language": skill_focus[i % len(skill_focus)],
                "stars": random.randint(0, 50),
                "forks": random.randint(0, 20),
                "topics": [skill_focus[i % len(skill_focus)].lower()],
            }
            for i in range(random.randint(5, 12))
        ],
        "bio": f"Software developer passionate about {', '.join(skill_focus[:3])}",
        "location": "Remote",
        "account_metrics": {
            "account_age_days": random.randint(365, 2000),
            "followers": random.randint(10, 500),
            "following": random.randint(20, 200),
        }
    }
