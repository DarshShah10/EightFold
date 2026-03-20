"""
Scorer Module - Answer-Based Scoring
===================================
Computes final scores purely based on actual answers, NOT self-assessment.
"""

from typing import Dict, List, Any

def compute_score_delta(
    initial_score: float,  # Ignored - kept for compatibility
    assessment_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute final score PURELY based on actual answer performance.
    No self-assessment or arbitrary bonuses - just real evaluation.
    """
    
    breakdown = {
        "oa_correctness": 0.0,
        "oa_clarity": 0.0,
        "oa_depth": 0.0,
        "interview_correctness": 0.0,
        "interview_clarity": 0.0,
        "interview_depth": 0.0,
        "hint_penalty": 0.0,
        "final_score": 0.0
    }
    
    # OA Phase evaluation
    oa_phase = assessment_results.get("oa_phase", {})
    oa_questions = oa_phase.get("questions", [])
    hints_used = oa_phase.get("hints_used", 0)
    final_depth = oa_phase.get("final_depth", "low")
    
    # Interview Phase evaluation
    interview_phase = assessment_results.get("interview_phase", {})
    interview_questions = interview_phase.get("questions", [])
    
    # Calculate OA score
    if oa_questions:
        for q in oa_questions:
            ev = q.get("evaluation", {})
            breakdown["oa_correctness"] += ev.get("correctness", 0)
            breakdown["oa_clarity"] += ev.get("clarity", 0)
            depth_val = 1.0 if ev.get("depth") == "high" else (0.5 if ev.get("depth") == "medium" else 0)
            breakdown["oa_depth"] += depth_val
        
        breakdown["oa_correctness"] /= len(oa_questions)
        breakdown["oa_clarity"] /= len(oa_questions)
        breakdown["oa_depth"] /= len(oa_questions)
    
    # Calculate Interview score
    if interview_questions:
        for q in interview_questions:
            ev = q if isinstance(q, dict) else q.get("evaluation", {})
            breakdown["interview_correctness"] += ev.get("correctness", 0)
            breakdown["interview_clarity"] += ev.get("clarity", 0)
            depth_val = 1.0 if ev.get("depth") == "high" else (0.5 if ev.get("depth") == "medium" else 0)
            breakdown["interview_depth"] += depth_val
        
        breakdown["interview_correctness"] /= len(interview_questions)
        breakdown["interview_clarity"] /= len(interview_questions)
        breakdown["interview_depth"] /= len(interview_questions)
    
    # Hint penalty (reduce final score by 5% per hint)
    breakdown["hint_penalty"] = hints_used * 0.05
    
    # FINAL SCORE = Pure average of all evaluations
    # Correctness (40%), Clarity (30%), Depth (30%)
    oa_weight = 0.4 if oa_questions else 0
    int_weight = 0.6 if interview_questions else 0
    
    final_score = 0.0
    
    if oa_questions or interview_questions:
        # Correctness
        if oa_questions:
            final_score += breakdown["oa_correctness"] * 0.4 * oa_weight / (oa_weight + int_weight if (oa_weight + int_weight) > 0 else 1)
        if interview_questions:
            final_score += breakdown["interview_correctness"] * 0.4 * int_weight / (oa_weight + int_weight if (oa_weight + int_weight) > 0 else 1)
        
        # Clarity
        if oa_questions:
            final_score += breakdown["oa_clarity"] * 0.3 * oa_weight / (oa_weight + int_weight if (oa_weight + int_weight) > 0 else 1)
        if interview_questions:
            final_score += breakdown["interview_clarity"] * 0.3 * int_weight / (oa_weight + int_weight if (oa_weight + int_weight) > 0 else 1)
        
        # Depth
        if oa_questions:
            final_score += breakdown["oa_depth"] * 0.3 * oa_weight / (oa_weight + int_weight if (oa_weight + int_weight) > 0 else 1)
        if interview_questions:
            final_score += breakdown["interview_depth"] * 0.3 * int_weight / (oa_weight + int_weight if (oa_weight + int_weight) > 0 else 1)
    
    # Apply hint penalty
    final_score -= breakdown["hint_penalty"]
    
    # Cap score 0-100%
    final_score = min(max(final_score, 0.0), 1.0)
    breakdown["final_score"] = final_score
    
    return {
        "initial_score": 0.5,  # Placeholder
        "final_score": round(final_score * 100, 0),  # Return as percentage
        "delta": 0,  # No delta since no initial
        "breakdown": {k: round(v * 100 if k != "hint_penalty" else v * 100, 1) for k, v in breakdown.items()},
        "status": determine_status(final_score)
    }

def determine_status(final_score: float) -> str:
    """Determine status based purely on final score."""
    if final_score >= 0.7:
        return "verified"  # Strong competency
    elif final_score >= 0.4:
        return "partial"   # Some gaps
    else:
        return "needs_training"  # Significant gaps

def format_score_breakdown(breakdown: Dict[str, float]) -> str:
    """Format score breakdown for display."""
    lines = []
    lines.append("SCORE BREAKDOWN:")
    lines.append("-" * 25)
    lines.append(f"  OA Correctness: {breakdown.get('oa_correctness', 0):.0f}%")
    lines.append(f"  OA Clarity: {breakdown.get('oa_clarity', 0):.0f}%")
    lines.append(f"  OA Depth: {breakdown.get('oa_depth', 0):.0f}%")
    lines.append(f"  Interview Correctness: {breakdown.get('interview_correctness', 0):.0f}%")
    lines.append(f"  Interview Clarity: {breakdown.get('interview_clarity', 0):.0f}%")
    lines.append(f"  Interview Depth: {breakdown.get('interview_depth', 0):.0f}%")
    if breakdown.get('hint_penalty', 0) > 0:
        lines.append(f"  Hint Penalty: -{breakdown.get('hint_penalty', 0):.0f}%")
    lines.append("-" * 25)
    lines.append(f"  FINAL SCORE: {breakdown.get('final_score', 0):.0f}%")
    return "\n".join(lines)

if __name__ == "__main__":
    # Test
    results = {
        "oa_phase": {
            "questions": [{"evaluation": {"correctness": 0.6, "clarity": 0.5, "depth": "medium"}}],
            "hints_used": 0
        },
        "interview_phase": {
            "questions": [{"correctness": 0.7, "clarity": 0.6, "depth": "high"}]
        }
    }
    
    score = compute_score_delta(0.5, results)
    print(f"Final Score: {score['final_score']}%")
    print(f"Status: {score['status']}")
    print(format_score_breakdown(score['breakdown']))
