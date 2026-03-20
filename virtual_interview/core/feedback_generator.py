"""
Feedback Generator Module
=========================
Generates human-like, conversational interviewer feedback.
Acknowledges strengths, points out gaps, keeps it natural and encouraging.
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
    """
    Extract text content from custom API response format.
    Handles both standard OpenAI format and custom format.
    """
    # Try standard OpenAI format first
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content.strip()
    
    # Try custom format: response.content is a list of dicts
    if hasattr(response, 'content') and response.content:
        for item in response.content:
            if isinstance(item, dict) and item.get('type') == 'text':
                return item.get('text', '').strip()
        # If no 'text' type found, try first item
        if isinstance(response.content[0], dict):
            return response.content[0].get('text', str(response.content[0])).strip()
    
    return str(response)

def build_combined_prompt(system_prompt: str, user_prompt: str) -> str:
    """
    Combine system and user prompts into a single message.
    The codemax API doesn't support separate system messages.
    """
    return f"{system_prompt}\n\n{user_prompt}"

def generate_feedback(
    evaluation: dict,
    include_strengths: bool = True,
    include_gaps: bool = True,
    tone: str = "supportive"
) -> str:
    """
    Generate human-like feedback based on evaluation results.
    
    Args:
        evaluation: The evaluation dict from evaluate_answer
        include_strengths: Whether to mention strengths (default: True)
        include_gaps: Whether to mention gaps (default: True)
        tone: "supportive", "direct", or "encouraging"
    
    Returns:
        A conversational feedback string
    """
    
    depth = evaluation.get("depth", "medium")
    strengths = evaluation.get("strengths", [])
    gaps = evaluation.get("gaps", [])
    reasoning = evaluation.get("reasoning", "")
    skill = evaluation.get("skill", "the skill")
    
    # Tone-specific system prompts
    tone_prompts = {
        "supportive": "You are a supportive interviewer who wants the candidate to learn and improve. Be encouraging but honest.",
        "direct": "You are a direct interviewer who values precision. Be clear and straightforward in your feedback.",
        "encouraging": "You are an encouraging interviewer who focuses on growth mindset. Emphasize what's possible."
    }
    
    system_prompt = f"""{tone_prompts.get(tone, tone_prompts['supportive'])}

Generate feedback that:
- Is conversational, like a real interviewer speaking
- Acknowledges good work before pointing out issues
- Is specific, not generic ("You missed X" not just "Room for improvement")
- Suggests what to focus on for improvement
- Is encouraging even when pointing out gaps

Keep it concise: 2-4 sentences max."""
    
    # Build context for the feedback
    context_parts = []
    context_parts.append(f"Evaluating candidate for skill: {skill}")
    context_parts.append(f"Demonstrated depth: {depth.upper()}")
    
    if include_strengths and strengths:
        context_parts.append(f"Strengths demonstrated: {'; '.join(strengths)}")
    
    if include_gaps and gaps:
        context_parts.append(f"Gaps identified: {'; '.join(gaps)}")
    
    if reasoning:
        context_parts.append(f"Detailed reasoning: {reasoning}")
    
    context = "\n".join(context_parts)
    
    user_prompt = f"""Based on this evaluation:

{context}

Generate natural, conversational feedback that the candidate would hear from an interviewer.
Format: Just the feedback, no headers or bullet points."""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=API_CONFIG["max_tokens"],
            temperature=0.7
        )
        
        feedback = extract_text_content(response)
        return feedback
        
    except Exception as e:
        # Fallback feedback if API fails
        return generate_fallback_feedback(depth, strengths, gaps, skill)

def generate_hint(
    skill: str,
    gaps: list,
    context: str = ""
) -> str:
    """
    Generate a short hint (1-2 lines) to help the candidate.
    
    Args:
        skill: The skill being assessed
        gaps: List of gaps identified from evaluation
        context: Optional additional context
    
    Returns:
        A 1-2 line concept explanation/hint
    """
    
    system_prompt = """You are a helpful mentor providing a quick hint.
Generate a SHORT hint (1-2 lines max) that:
- Explains the missing concept clearly
- Gives enough to guide without giving away the answer
- Is educational and encouraging

Do NOT give the full answer - just a helpful nudge in the right direction."""

    gaps_text = "\n".join([f"- {gap}" for gap in gaps]) if gaps else "General understanding gap"
    
    user_prompt = f"""The candidate is learning: {skill}

Gaps identified:
{gaps_text}

{context}

Provide a 1-2 line hint to help them understand the missing concept."""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=150,  # Keep it short
            temperature=0.7
        )
        
        hint = extract_text_content(response)
        return hint
        
    except Exception as e:
        return f"Hint: Focus on understanding {skill} better - consider the practical aspects."

def generate_followup(
    question: str,
    answer: str,
    evaluation: dict,
    skill: str
) -> str:
    """
    Generate a follow-up question that targets the identified weakness.
    
    Args:
        question: The original question
        answer: The candidate's answer
        evaluation: The evaluation dict
        skill: The skill being assessed
    
    Returns:
        A follow-up question string
    """
    
    depth = evaluation.get("depth", "medium")
    gaps = evaluation.get("gaps", [])
    reasoning = evaluation.get("reasoning", "")
    
    system_prompt = """You are an interviewer generating a follow-up question.
The follow-up should:
- Target a specific weakness or gap in the candidate's previous answer
- Push for deeper thinking
- Be natural, like a real interviewer would ask
- Not be a completely new topic - should build on the previous answer

Format: Just the follow-up question, no explanation."""

    user_prompt = f"""Original question: {question}

Candidate's answer: {answer}

Evaluation depth: {depth.upper()}

Gaps identified: {', '.join(gaps) if gaps else 'None specified'}

Evaluation reasoning: {reasoning}

Generate a natural follow-up question that probes deeper into the weak areas."""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=API_CONFIG["max_tokens"],
            temperature=0.7
        )
        
        followup = extract_text_content(response)
        return followup
        
    except Exception as e:
        return f"Can you elaborate more on the {skill} aspects you mentioned?"

def generate_fallback_feedback(
    depth: str,
    strengths: list,
    gaps: list,
    skill: str
) -> str:
    """Generate basic feedback without LLM (fallback)."""
    
    if depth == "high":
        return f"Great job! You demonstrated strong understanding of {skill}. Your answer shows good depth and practical knowledge."
    elif depth == "medium":
        feedback = f"You're on the right track with {skill}. "
        if gaps:
            feedback += f"Consider focusing on: {', '.join(gaps[:2])}."
        return feedback
    else:
        feedback = f"Let's dig deeper into {skill}. "
        if gaps:
            feedback += f"Some areas to work on: {', '.join(gaps[:2])}."
        return feedback

def format_feedback_for_display(feedback: str, evaluation: dict) -> str:
    """
    Format feedback with additional context for display.
    
    Args:
        feedback: The feedback string
        evaluation: The evaluation dict
    
    Returns:
        Formatted string for display
    """
    lines = []
    lines.append("-" * 40)
    lines.append("📝 INTERVIEWER FEEDBACK")
    lines.append("-" * 40)
    lines.append(f'"{feedback}"')
    lines.append("-" * 40)
    lines.append(f"Depth Level: {evaluation.get('depth', 'N/A').upper()}")
    lines.append("")
    
    return "\n".join(lines)

# Example usage
if __name__ == "__main__":
    # Test with sample evaluation
    sample_evaluation = {
        "skill": "Kubernetes",
        "depth": "medium",
        "correctness": 0.6,
        "clarity": 0.7,
        "confidence": 0.8,
        "strengths": [
            "Understands basic pod lifecycle",
            "Mentioned checking pod status"
        ],
        "gaps": [
            "Missing debugging strategies",
            "Didn't mention logs analysis",
            "No mention of describe command"
        ],
        "reasoning": "Candidate showed basic knowledge but lacked depth in debugging approaches."
    }
    
    print("Sample Feedback:")
    print("-" * 40)
    
    feedback = generate_feedback(sample_evaluation, tone="supportive")
    print(feedback)
    
    print("\n" + "-" * 40)
    print("Sample Hint:")
    print("-" * 40)
    
    hint = generate_hint(
        sample_evaluation["skill"],
        sample_evaluation["gaps"]
    )
    print(hint)
    
    print("\n" + "-" * 40)
    print("Sample Follow-up Question:")
    print("-" * 40)
    
    followup = generate_followup(
        question="A pod is stuck in CrashLoopBackOff. Walk me through how you'd debug this.",
        answer="I would check the pod logs.",
        evaluation=sample_evaluation,
        skill=sample_evaluation["skill"]
    )
    print(followup)
