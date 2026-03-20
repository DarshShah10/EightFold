"""
Evaluator Module
================
Evaluates candidate answers with transparent, explainable reasoning.
NOT a black box - shows exactly what criteria are being evaluated.

Uses configurable rubrics and shows reasoning for each dimension.
"""

import os
import json
from openai import OpenAI
from virtual_interview.config import API_CONFIG, EVALUATION_CONFIG

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

def evaluate_answer(
    question: str, 
    answer: str, 
    skill: str,
    rubric: dict = None
) -> dict:
    """
    Evaluate a candidate's answer with transparent reasoning.
    
    Args:
        question: The question that was asked
        answer: The candidate's answer
        skill: The skill being evaluated
        rubric: Optional rubric dict with evaluation criteria
    
    Returns:
        A transparent evaluation dict with:
        - depth: "low", "medium", or "high"
        - correctness: 0-1 score
        - clarity: 0-1 score
        - confidence: 0-1 score
        - gaps: List of specific gaps identified
        - strengths: List of strengths demonstrated
        - reasoning: Detailed explanation of evaluation
        - dimensions: Per-dimension breakdown
    """
    
    # Default evaluation criteria if no rubric provided
    default_dimensions = [
        {
            "name": "correctness",
            "description": "Is the answer technically correct?",
            "weight": 0.4
        },
        {
            "name": "completeness",
            "description": "Does the answer cover all aspects of the question?",
            "weight": 0.3
        },
        {
            "name": "depth",
            "description": "Does the answer show deep understanding vs surface knowledge?",
            "weight": 0.3
        }
    ]
    
    dimensions = rubric.get("dimensions", default_dimensions) if rubric else default_dimensions
    
    # Build evaluation prompt with visible criteria
    dimensions_text = "\n".join([
        f"- {d['name']}: {d['description']} (weight: {d['weight']})"
        for d in dimensions
    ])
    
    system_prompt = """You are an expert technical interviewer evaluating a candidate's answer.
Your evaluation MUST be TRANSPARENT - explain your reasoning clearly.

For each dimension, provide:
1. A score from 0.0 to 1.0
2. Specific reasoning explaining WHY you gave that score
3. Evidence from the answer that supports your score

Return your evaluation as a JSON object with this structure:
{
    "depth": "low|medium|high",
    "correctness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "confidence": 0.0-1.0,
    "dimensions": {
        "dimension_name": {
            "score": 0.0-1.0,
            "reasoning": "explanation...",
            "evidence": "specific part of answer..."
        }
    },
    "gaps": ["specific gap 1", "specific gap 2"],
    "strengths": ["strength 1", "strength 2"],
    "reasoning": "Overall explanation of evaluation...",
    "recommendation": "proceed|followup|needs_help"
}"""

    user_prompt = f"""Evaluate this answer:

SKILL: {skill}
QUESTION: {question}

ANSWER: {answer}

EVALUATION CRITERIA (visible to user):
{dimensions_text}

Please evaluate thoroughly and honestly. Be specific in your feedback."""

    try:
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "user", "content": build_combined_prompt(system_prompt, user_prompt)}
            ],
            max_tokens=API_CONFIG["max_tokens"] * 2,
            temperature=0.3  # Lower temperature for more consistent evaluation
        )
        
        result_text = extract_text_content(response)
        
        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            evaluation = json.loads(result_text)
            
            # Add the original question and answer for reference
            evaluation["question"] = question
            evaluation["answer"] = answer
            evaluation["skill"] = skill
            
            return evaluation
            
        except json.JSONError:
            # If JSON parsing fails, return raw text with structure
            return {
                "depth": "medium",
                "correctness": 0.5,
                "clarity": 0.5,
                "confidence": 0.5,
                "gaps": ["Unable to parse evaluation"],
                "strengths": [],
                "reasoning": result_text,
                "error": "Failed to parse JSON response"
            }
            
    except Exception as e:
        return {
            "depth": "medium",
            "correctness": 0.0,
            "clarity": 0.0,
            "confidence": 0.0,
            "gaps": [f"Error during evaluation: {str(e)}"],
            "strengths": [],
            "reasoning": f"Error occurred: {str(e)}",
            "error": str(e)
        }

def compute_depth(score: float) -> str:
    """
    Compute depth level from score using configurable thresholds.
    
    Args:
        score: A score from 0.0 to 1.0
    
    Returns:
        "low", "medium", or "high"
    """
    thresholds = EVALUATION_CONFIG["depth_thresholds"]
    
    if score >= thresholds["high"]:
        return "high"
    elif score >= thresholds["low"]:
        return "medium"
    else:
        return "low"

def format_evaluation_for_display(evaluation: dict) -> str:
    """
    Format evaluation for human-readable display.
    
    Args:
        evaluation: The evaluation dict from evaluate_answer
    
    Returns:
        A formatted string for display
    """
    lines = []
    lines.append("=" * 50)
    lines.append("EVALUATION RESULTS")
    lines.append("=" * 50)
    lines.append(f"Skill: {evaluation.get('skill', 'N/A')}")
    lines.append(f"Depth: {evaluation.get('depth', 'N/A').upper()}")
    lines.append("")
    
    # Overall scores
    lines.append("OVERALL SCORES:")
    lines.append(f"  Correctness: {evaluation.get('correctness', 0):.2f}/1.0")
    lines.append(f"  Clarity:    {evaluation.get('clarity', 0):.2f}/1.0")
    lines.append(f"  Confidence: {evaluation.get('confidence', 0):.2f}/1.0")
    lines.append("")
    
    # Dimension breakdown
    if "dimensions" in evaluation:
        lines.append("DIMENSION BREAKDOWN:")
        for dim_name, dim_data in evaluation["dimensions"].items():
            score = dim_data.get("score", 0)
            reasoning = dim_data.get("reasoning", "No reasoning provided")
            lines.append(f"  [{dim_name.upper()}] {score:.2f}/1.0")
            lines.append(f"    Reasoning: {reasoning}")
        lines.append("")
    
    # Strengths
    if evaluation.get("strengths"):
        lines.append("STRENGTHS:")
        for strength in evaluation["strengths"]:
            lines.append(f"  ✓ {strength}")
        lines.append("")
    
    # Gaps
    if evaluation.get("gaps"):
        lines.append("AREAS FOR IMPROVEMENT:")
        for gap in evaluation["gaps"]:
            lines.append(f"  ✗ {gap}")
        lines.append("")
    
    # Reasoning
    if evaluation.get("reasoning"):
        lines.append("DETAILED REASONING:")
        lines.append(evaluation["reasoning"])
    
    lines.append("=" * 50)
    
    return "\n".join(lines)

# Example usage
if __name__ == "__main__":
    # Test with sample data
    skill = "Kubernetes"
    question = "A pod is stuck in CrashLoopBackOff. Walk me through how you'd debug this."
    answer = "I would check the pod logs and describe the pod to see what's happening."
    
    print(f"Evaluating answer for: {skill}")
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print()
    
    evaluation = evaluate_answer(question, answer, skill)
    print(format_evaluation_for_display(evaluation))
