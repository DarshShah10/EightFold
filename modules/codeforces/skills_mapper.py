"""
Codeforces Skills Mapper
======================
Maps Codeforces competitive programming topics to job-relevant skills.
Bridges the gap between competitive programming and real-world engineering.
"""

from typing import Any, Dict, List, Optional

# ─── Topic → Job Skill Mappings ────────────────────────────────────────────────

CF_TOPIC_TO_JOB_SKILLS: Dict[str, List[str]] = {
    # Dynamic Programming
    "dynamic-programming": [
        "System Design",
        "Optimization",
        "Algorithm Optimization",
        "Resource Allocation",
        "Memoization Patterns",
    ],
    "dp": [
        "System Design",
        "Optimization",
        "Algorithm Optimization",
        "Resource Allocation",
        "Memoization Patterns",
    ],

    # Graph Theory
    "graphs": [
        "Network Architecture",
        "Social Network Analysis",
        "Pathfinding Algorithms",
        "Graph Databases",
        "Routing Algorithms",
    ],
    "graph-theory": [
        "Network Architecture",
        "Social Network Analysis",
        "Pathfinding Algorithms",
        "Graph Databases",
        "Routing Algorithms",
    ],
    "shortest-paths": [
        "Routing Algorithms",
        "GPS/Navigation Systems",
        "Network Optimization",
        "Load Balancing",
    ],
    "trees": [
        "Data Structure Design",
        "File Systems",
        "DOM Manipulation",
        "Hierarchical Data",
    ],
    "graph-traversal": [
        "Tree Algorithms",
        "Web Crawling",
        "Network Analysis",
        "Game AI",
    ],
    "bfs": [
        "Shortest Path",
        "Level-order Traversal",
        "Web Crawling",
        "Social Networks",
    ],
    "dfs": [
        "Tree Traversal",
        "Backtracking",
        "Game AI",
        "Dependency Resolution",
    ],

    # Data Structures
    "data-structures": [
        "Clean Architecture",
        "API Design",
        "Database Indexing",
        "Caching Strategies",
    ],
    "hash-tables": [
        "Caching",
        "Lookups",
        "Dictionary Implementation",
        "Associative Arrays",
    ],
    "segment-tree": [
        "Range Queries",
        "Real-time Analytics",
        "Database Indexing",
        "Event Processing",
    ],
    "fenwick-tree": [
        "Range Queries",
        "Prefix Sums",
        "Binary Indexed Tree",
        "Cumulative Analytics",
    ],
    "sparse-table": [
        "Range Queries",
        "Static Data",
        "RMQ Problems",
        "Fast Lookups",
    ],
    "stl": [
        "C++ Standard Library",
        "Competitive Programming",
        "Performance Optimization",
    ],
    "binary-search": [
        "Search Algorithms",
        "Binary Search Trees",
        "Optimization Problems",
        "Parametric Search",
    ],
    "two-pointers": [
        "Array Processing",
        "Sliding Window",
        "Optimization",
        "Subarray Problems",
    ],

    # Math / Number Theory
    "math": [
        "Cryptography",
        "Security",
        "Scientific Computing",
        "Financial Algorithms",
        "Signal Processing",
    ],
    "number-theory": [
        "Cryptography",
        "Security",
        "Prime Number Algorithms",
        "Modular Arithmetic",
    ],
    "combinatorics": [
        "Probability & Statistics",
        "Permutations",
        "Algorithm Analysis",
        "Optimization",
    ],
    "probability": [
        "Statistical Analysis",
        "Risk Modeling",
        "Machine Learning",
        "A/B Testing",
    ],
    "fft": [
        "Signal Processing",
        "Polynomial Multiplication",
        "Image Processing",
        "Audio Analysis",
    ],
    "matrix-exponentiation": [
        "Dynamic Programming",
        "Linear Algebra",
        "Graph Algorithms",
        "Recursive Optimization",
    ],
    "games": [
        "Game Theory",
        "AI Development",
        "Minimax Algorithms",
        "Strategy Design",
    ],

    # String Algorithms
    "strings": [
        "Text Processing",
        "NLP",
        "Pattern Matching",
        "Search Algorithms",
    ],
    "string-suffix-structures": [
        "Text Indexing",
        "Pattern Matching",
        "Bioinformatics",
        "Search Engines",
    ],
    "hashing": [
        "Hash Maps",
        "Security",
        "Data Integrity",
        "Deduplication",
    ],
    "trie": [
        "Prefix Trees",
        "Autocomplete",
        "Spell Checking",
        "IP Routing",
    ],
    "suffix-automaton": [
        "Pattern Matching",
        "Text Indexing",
        "Bioinformatics",
        "Data Compression",
    ],

    # Geometry
    "geometry": [
        "Computer Graphics",
        "Computer Vision",
        "Game Development",
        "CAD Systems",
    ],
    "computational-geometry": [
        "Graphics Programming",
        "Collision Detection",
        "GIS Systems",
        "Robotics",
    ],

    # Sorting & Searching
    "sorting": [
        "Data Organization",
        "Order Statistics",
        "Pipeline Processing",
        "Batch Jobs",
    ],
    "binary-search": [
        "Efficient Search",
        "Parametric Search",
        "Optimization",
        "Database Indexing",
    ],

    # Greedy & Constructive
    "greedy": [
        "Optimization",
        "Resource Management",
        "Scheduling",
        "Approximation Algorithms",
    ],
    "constructive-algorithms": [
        "Algorithm Design",
        "Creative Problem Solving",
        "Proof Construction",
    ],

    # Divide & Conquer
    "divide-and-conquer": [
        "Algorithm Design",
        "Parallel Processing",
        "Merge Sort",
        "Complex Problem Solving",
    ],

    # Networking / Flow
    "flows": [
        "Network Flow",
        "Transportation Problems",
        "Resource Allocation",
        "Max-Cut Problems",
    ],
    "matching": [
        "Bipartite Matching",
        "Assignment Problems",
        "Recommendation Systems",
        "Stable Marriage",
    ],

    # Specialized
    "bitmasks": [
        "Bit Manipulation",
        "Flag Management",
        "Optimization",
        "Compression",
    ],
    "schedules": [
        "Task Scheduling",
        "Resource Allocation",
        "Calendar Systems",
        "Worker Pools",
    ],
    "chinese-remainder-theorem": [
        "Cryptography",
        "Modular Arithmetic",
        "Clock Problems",
    ],
    "eulerian-cycles": [
        "Path Finding",
        "Network Analysis",
        "Route Planning",
    ],

    # Machine Learning related
    "bayes-theorems": [
        "Machine Learning",
        "Statistical Inference",
        "Bayesian Networks",
        "Naive Bayes",
    ],
}

# ─── Rating Tier → Engineering Level ────────────────────────────────────────────

RATING_TIER_SCORES: Dict[str, float] = {
    "Legendary Grandmaster": 1.0,
    "International Grandmaster": 0.95,
    "Grandmaster": 0.90,
    "International Master": 0.85,
    "Master": 0.80,
    "Candidate Master": 0.70,
    "Expert": 0.55,
    "Specialist": 0.40,
    "Pupil": 0.25,
    "Newbie": 0.10,
    "unrated": 0.0,
}

# ─── Difficulty → Job Relevance ─────────────────────────────────────────────────

DIFFICULTY_JOB_RELEVANCE: Dict[str, str] = {
    "800 (Warmup)": "Basic Programming",
    "1000 (Easy)": "Entry-Level Tasks",
    "1200 (Easy-Med)": "Standard Development",
    "1400 (Medium)": "Complex Logic",
    "1600 (Medium-Hard)": "System Design Basics",
    "1800 (Hard)": "Advanced System Design",
    "2000 (Very Hard)": "Senior Engineer Level",
    "2200 (Expert)": "Staff Engineer Level",
    "2400 (Master)": "Principal Engineer Level",
    "2600 (Grandmaster)": "Distinguished Engineer",
    "2600+ (Extreme)": "Research Scientist",
}

# ─── Problem Solving Dimensions ────────────────────────────────────────────────

PROBLEM_SOLVING_DIMENSIONS: Dict[str, str] = {
    "dynamic-programming": "Algorithmic Thinking",
    "graphs": "Network & Connectivity",
    "data-structures": "Data Organization",
    "math": "Mathematical Reasoning",
    "strings": "Text Processing",
    "geometry": "Spatial Reasoning",
    "sorting": "Ordering & Optimization",
    "greedy": "Optimization",
    "divide-and-conquer": "Complex Problem Decomposition",
    "combinatorics": "Counting & Probability",
}


def map_cf_topics_to_job_skills(topics: List[str]) -> Dict[str, List[str]]:
    """
    Map Codeforces topics/tags to job-relevant skills.

    Args:
        topics: List of CF topic strings (e.g., ["dp", "graphs", "math"])

    Returns:
        Dict mapping CF topic → list of job skills
    """
    result = {}

    for topic in topics:
        topic_lower = topic.lower().strip()
        job_skills = CF_TOPIC_TO_JOB_SKILLS.get(topic_lower, [])

        if job_skills:
            result[topic] = job_skills

    return result


def get_job_skills_from_topics(topics: List[str]) -> List[str]:
    """
    Get a flat list of all job-relevant skills from CF topics.

    Args:
        topics: List of CF topic strings

    Returns:
        Deduplicated list of job-relevant skills
    """
    skills = []
    for topic in topics:
        mapped = CF_TOPIC_TO_JOB_SKILLS.get(topic.lower().strip(), [])
        skills.extend(mapped)

    return list(set(skills))


def get_problem_solving_score(
    rating: int,
    max_rating: int,
    problems_solved: int,
    topics: List[str],
    ac_rate: float,
    flag_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Compute a comprehensive problem-solving score for a candidate.

    Args:
        rating: Current rating
        max_rating: Maximum rating achieved
        problems_solved: Total problems solved
        topics: List of CF topics
        ac_rate: Accept rate (0-1)
        flag_score: Flag score (0-1, 0 = clean)

    Returns:
        Dict with score breakdown
    """
    # Flag penalty
    if flag_score >= 0.8:
        return {
            "problem_solving_score": 0.0,
            "verified": False,
            "reason": "User flagged for cheating",
            "breakdown": {},
        }

    # Rating contribution
    tier_score = RATING_TIER_SCORES.get(
        _get_tier_name(max_rating), 0.0
    )

    # Problems solved contribution
    if problems_solved >= 500:
        prob_score = 0.25
    elif problems_solved >= 200:
        prob_score = 0.20
    elif problems_solved >= 100:
        prob_score = 0.15
    elif problems_solved >= 50:
        prob_score = 0.10
    elif problems_solved >= 20:
        prob_score = 0.05
    else:
        prob_score = 0.02

    # AC rate contribution
    ac_score = min(ac_rate * 0.15, 0.15)

    # Topic breadth contribution
    unique_skills = get_job_skills_from_topics(topics)
    topic_score = min(len(unique_skills) * 0.02, 0.10)

    total = min(tier_score * 0.5 + prob_score + ac_score + topic_score, 1.0)

    # Apply flag penalty
    if flag_score >= 0.5:
        total *= 0.3

    breakdown = {
        "rating_score": round(tier_score * 0.5, 3),
        "problems_score": round(prob_score, 3),
        "ac_rate_score": round(ac_score, 3),
        "topic_breadth_score": round(topic_score, 3),
        "flag_penalty": round(flag_score, 3),
    }

    return {
        "problem_solving_score": round(total, 3),
        "verified": flag_score < 0.5,
        "reason": "Codeforces verified" if flag_score < 0.5 else "Flag detected",
        "breakdown": breakdown,
        "job_skills_count": len(unique_skills),
        "job_skills": unique_skills[:15],  # Top 15 skills
    }


def get_tier_description(tier_name: str) -> str:
    """Get a description of what a rating tier means for hiring."""
    descriptions = {
        "Legendary Grandmaster": "Exceptional algorithmic thinker. Suitable for research, competitive programming roles, or complex systems.",
        "International Grandmaster": "Top-tier problem solver. Strong for systems programming, ML research, or high-complexity backend.",
        "Grandmaster": "Expert-level algorithmic skills. Strong candidate for complex backend, ML, or systems roles.",
        "International Master": "Very strong problem-solving skills. Good for complex engineering challenges.",
        "Master": "Strong algorithmic background. Suitable for challenging engineering roles.",
        "Candidate Master": "Solid problem-solving foundation. Good for mid-to-senior engineering roles.",
        "Expert": "Competent with algorithms and data structures. Suitable for standard engineering roles.",
        "Specialist": "Working knowledge of algorithms. Good for general development.",
        "Pupil": "Learning algorithms. Entry-level or training required.",
        "Newbie": "Beginner level. Training and mentorship needed.",
        "unrated": "No competitive programming history. Skills not verified via CF.",
    }
    return descriptions.get(tier_name, "Unknown tier")


def _get_tier_name(rating: int) -> str:
    """Get tier name from rating."""
    tiers = [
        (3000, "Legendary Grandmaster"),
        (2600, "International Grandmaster"),
        (2400, "Grandmaster"),
        (2300, "International Master"),
        (2100, "Master"),
        (1900, "Candidate Master"),
        (1600, "Expert"),
        (1400, "Specialist"),
        (1200, "Pupil"),
        (0, "Newbie"),
    ]
    for threshold, name in tiers:
        if rating >= threshold:
            return name
    return "unrated"


def get_jd_relevance(
    cf_topics: List[str],
    jd_skills: List[str],
) -> Dict[str, Any]:
    """
    Compare CF topics against job description skills.

    Args:
        cf_topics: List of CF topics the candidate is strong in
        jd_skills: List of skills required by the job

    Returns:
        Dict with relevance analysis
    """
    job_skills = get_job_skills_from_topics(cf_topics)
    job_skills_lower = [s.lower() for s in job_skills]
    jd_skills_lower = [s.lower() for s in jd_skills]

    matched = []
    partial = []

    for jd_skill in jd_skills:
        jd_lower = jd_skill.lower()
        # Exact match
        if jd_lower in job_skills_lower:
            matched.append(jd_skill)
        # Partial match
        elif any(jd_lower in js or js in jd_lower for js in job_skills_lower):
            partial.append(jd_skill)

    coverage = len(matched) / len(jd_skills) if jd_skills else 0.0

    return {
        "matched_skills": matched,
        "partial_skills": partial,
        "coverage": round(coverage, 3),
        "cf_topics_analyzed": cf_topics,
        "job_skills_mapped": job_skills,
    }
