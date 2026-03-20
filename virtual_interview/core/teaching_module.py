"""
Teaching Module
==============
Provides targeted learning hints and explanations based on identified gaps.
Different from feedback - this teaches the concept, not just evaluates.
"""

import os
from openai import OpenAI
from virtual_interview.config import API_CONFIG

# Initialize OpenAI client
api_key = os.environ.get("OPENAI_API_KEY", API_CONFIG["api_key"])
client = OpenAI(
    api_key=api_key,
    base_url=API_CONFIG["base_url"]
)

def extract_text_content(response) -> str:
    """Extract text content from API response."""
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content.strip()
    if hasattr(response, 'content') and response.content:
        for item in response.content:
            if isinstance(item, dict) and item.get('type') == 'text':
                return item.get('text', '').strip()
        if isinstance(response.content[0], dict):
            return response.content[0].get('text', str(response.content[0])).strip()
    return str(response)

def build_combined_prompt(system_prompt: str, user_prompt: str) -> str:
    """Combine system and user prompts into a single message."""
    return f"{system_prompt}\n\n{user_prompt}"

def generate_concept_explanation(
    skill: str,
    concept: str,
    depth: str = "basic"
) -> str:
    """
    Generate a concise explanation of a specific concept.
    
    Args:
        skill: The skill being learned
        concept: The specific concept to explain
        depth: "basic", "intermediate", or "advanced"
    
    Returns:
        A concise explanation (1-3 sentences)
    """
    
    depth_prompts = {
        "basic": "Explain for someone new to the topic. Keep it simple and practical.",
        "intermediate": "Assume some familiarity. Focus on practical application.",
        "advanced": "Assume strong foundation. Focus on edge cases and best practices."
    }
    
    system_prompt = f"""You are a technical educator explaining concepts clearly.
{depth_prompts.get(depth, depth_prompts['basic'])}

Your explanation should:
- Be 1-3 sentences only
- Focus on the most important point
- Include a practical example if helpful
- Be easy to understand"""

    user_prompt = f"Explain the concept of '{concept}' in the context of {skill}."

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return extract_text_content(response)
    except Exception as e:
        return f"Error generating explanation: {str(e)}"

def generate_learning_path(
    skill: str,
    gaps: list,
    current_level: str = "beginner"
) -> dict:
    """
    Generate a personalized learning path based on identified gaps.
    
    Args:
        skill: The skill to learn
        gaps: List of identified knowledge gaps
        current_level: "beginner", "intermediate", or "advanced"
    
    Returns:
        Dict with learning path and resources
    """
    
    system_prompt = """You are a technical mentor creating a personalized learning path.
Based on the learner's current gaps, recommend:
1. Priority order of topics to learn
2. Key concepts to master for each topic
3. A brief note on why each topic matters

Keep it concise and actionable."""

    gaps_text = "\n".join([f"- {gap}" for gap in gaps])
    
    user_prompt = f"""Create a learning path for {skill} at {current_level} level.

Learner has gaps in:
{gaps_text}

Provide a prioritized list of what to learn next."""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return {
            "skill": skill,
            "current_level": current_level,
            "gaps": gaps,
            "learning_path": extract_text_content(response)
        }
    except Exception as e:
        return {
            "skill": skill,
            "current_level": current_level,
            "gaps": gaps,
            "learning_path": f"Error generating learning path: {str(e)}"
        }

def generate_quick_tip(
    skill: str,
    topic: str
) -> str:
    """
    Generate a quick practical tip for a topic.
    
    Args:
        skill: The skill
        topic: The topic to get a tip for
    
    Returns:
        A quick practical tip
    """
    
    system_prompt = """You are giving a quick technical tip.
Keep it to ONE sentence that someone can use immediately.
Make it practical and memorable."""

    user_prompt = f"Give me a quick tip for {topic} in {skill}."

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return extract_text_content(response)
    except Exception as e:
        return f"Quick tip: Practice {topic} in {skill} regularly."

# Common gap to concept mapping for Kubernetes
KUBERNETES_GAP_MAPPING = {
    "debugging": {
        "kubectl logs": "Shows container output, use --previous for last crash",
        "kubectl describe": "Shows detailed resource info and events",
        "kubectl exec": "Run commands inside a running container",
        "CrashLoopBackOff": "Container keeps restarting - check logs and events"
    },
    "architecture": {
        "pods": "Smallest deployable unit, contains one or more containers",
        "services": "Stable IP for accessing pods, handles load balancing",
        "deployments": "Manages pod replicas and rolling updates"
    }
}

def get_teaching_for_gap(skill: str, gap: str) -> str:
    """
    Get a teaching explanation for a specific gap.
    
    Args:
        skill: The skill (e.g., "Kubernetes", "Docker")
        gap: The gap description
    
    Returns:
        A brief teaching explanation
    """
    
    # Check if we have a direct mapping
    skill_lower = skill.lower()
    if skill_lower == "kubernetes":
        for category, mappings in KUBERNETES_GAP_MAPPING.items():
            for key, explanation in mappings.items():
                if key.lower() in gap.lower():
                    return explanation
    
    # Otherwise, generate one
    return generate_concept_explanation(skill, gap, "basic")

# Example usage
if __name__ == "__main__":
    print("Testing Teaching Module:")
    print("-" * 40)
    
    # Test concept explanation
    print("Concept Explanation:")
    print(generate_concept_explanation("Kubernetes", "CrashLoopBackOff"))
    print()
    
    # Test quick tip
    print("Quick Tip:")
    print(generate_quick_tip("Docker", "container debugging"))
    print()
    
    # Test gap teaching
    print("Gap Teaching:")
    print(get_teaching_for_gap("Kubernetes", "No mention of kubectl describe"))
