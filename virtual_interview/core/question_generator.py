"""
Question Generator - Easier Questions & Context-Aware Follow-ups
============================================================
"""

import os
import yaml
from openai import OpenAI
from virtual_interview.config import API_CONFIG

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", API_CONFIG["api_key"]),
    base_url=API_CONFIG["base_url"]
)

def extract_text(response):
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content.strip()
    return str(response)

def load_rubric(skill: str):
    """Load rubric for skill."""
    rubric_path = f"rubrics/{skill.lower()}.yaml"
    try:
        with open(rubric_path, 'r') as f:
            return yaml.safe_load(f)
    except:
        return None

import random

def generate_question(skill: str, difficulty: str = "easy") -> str:
    """Generate an EASY question for a skill."""
    
    rubric = load_rubric(skill)
    dimensions = rubric.get("dimensions", []) if rubric else []
    
    dimension_text = ""
    if dimensions:
        dimension_text = f"Focus on: {', '.join([d['name'] for d in dimensions[:2]])}"
    
    # Random variation
    question_types = [
        "Explain the main purpose of",
        "What is",
        "Describe how",
        "Give an example of",
        "How would you use",
        "What happens when you use"
    ]
    
    system_prompt = f"""You are generating EASY interview questions.
Keep questions simple and practical - like for a junior developer.
{dimension_text}

Rules:
- Use simple language anyone can understand
- Focus on basic concepts, not advanced topics
- Give real-world scenarios
- Keep questions short (1-2 sentences)
"""
    
    q_type = random.choice(question_types)
    user_prompt = f"""Generate ONE unique easy question about {skill}.
Format: "{q_type} [concept] in {skill}" or a scenario question.
Example: "Imagine you're explaining {skill} to a beginner. What would you say?"
Make it different from typical questions!"""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )
        return extract_text(response)
    except Exception as e:
        return f"Explain {skill} in simple terms. What is its main purpose?"

def generate_interview_question(skill: str, difficulty: str = "medium", context: dict = None) -> str:
    """Generate interview question with context awareness."""
    
    rubric = load_rubric(skill)
    dimensions = rubric.get("dimensions", []) if rubric else []
    
    system_prompt = """You are generating interview questions.
Generate follow-up questions that BUILD on previous answers.
"""
    
    # Context-aware prompt
    context_text = ""
    if context and context.get("last_answer"):
        system_prompt += """
IMPORTANT: The candidate just answered this:
---
{last_answer}
---

Generate a follow-up that asks them to EXPAND or OPTIMIZE what they said.
"""
        context_text = context.get("last_answer", "")
    
    user_prompt = f"""Generate an interview question about {skill}."""
    
    if context_text:
        user_prompt += f"""

Follow up on their previous answer about {context.get("topic", skill)}.
Ask something like:
- "How would you optimize this for 10000 users?"
- "What if the data is corrupted?"
- "Can you explain this with an example?"
- "What are the trade-offs?"
"""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt.format(last_answer=context_text)},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.8
        )
        return extract_text(response)
    except Exception as e:
        return f"Based on your previous answer, can you elaborate more about {skill}?"

def generate_followup_question(skill: str, previous_answer: str, depth: str = "medium") -> str:
    """Generate contextual follow-up based on previous answer."""
    
    system_prompt = f"""You are an interviewer asking follow-up questions.
The candidate just answered:
---
{previous_answer}
---

Generate a natural follow-up that digs deeper.
Examples:
- "That's interesting! How would you handle this at scale?"
- "Good answer! What are the limitations of this approach?"
- "Can you show me the code/implementation?"
- "What would you do differently if there were 10x more users?"

Keep it conversational and specific to what they said."""

    user_prompt = f"Ask a follow-up question about {skill}."

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.8
        )
        return extract_text(response)
    except Exception as e:
        return f"Can you tell me more about {skill}?"

if __name__ == "__main__":
    print("Testing Easy Questions:")
    print("-" * 40)
    print("Python:", generate_question("Python"))
    print()
    print("Kubernetes:", generate_question("Kubernetes"))
    print()
    print("Follow-up:", generate_followup_question("Python", "I use Docker to containerize apps"))
