"""
Virtual Interview Engine - Main Entry Point
===========================================
Orchestrates the full interview assessment flow.

Usage:
    python main.py --input sample_input.json
    python main.py --skill "Kubernetes"  # Test single skill
    streamlit run main.py               # Run with UI
"""

import argparse
import json
import sys
from datetime import datetime

from virtual_interview.config import API_CONFIG, ASSESSMENT_CONFIG, SCORING_CONFIG, RECOMMENDATION_CONFIG
from virtual_interview.core.question_generator import generate_question, generate_interview_question
from virtual_interview.core.evaluator import evaluate_answer, format_evaluation_for_display
from virtual_interview.core.feedback_generator import generate_feedback, generate_hint, generate_followup

def load_input(file_path: str) -> dict:
    """Load input JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{file_path}'")
        sys.exit(1)

def run_assessment(skill: str, initial_score: float = 0.5) -> dict:
    """
    Run a complete assessment for a single skill.
    
    Args:
        skill: The skill to assess
        initial_score: The candidate's current score for this skill
    
    Returns:
        Assessment results dict
    """
    
    print(f"\n{'='*60}")
    print(f"ASSESSING: {skill}")
    print(f"Initial Score: {initial_score}")
    print(f"{'='*60}\n")
    
    results = {
        "skill": skill,
        "initial_score": initial_score,
        "oa_phase": {
            "questions": [],
            "hints_used": 0,
            "final_depth": None
        },
        "interview_phase": {
            "questions": []
        },
        "final_score": initial_score,
        "score_delta": 0.0,
        "status": "pending"
    }
    
    # ========== OA PHASE ==========
    print("📋 OA PHASE - Testing practical understanding...\n")
    
    # Generate OA question
    question = generate_question(skill)
    print(f"QUESTION: {question}\n")
    
    # Get answer from user
    answer = input("Your answer: ").strip()
    
    if len(answer) < ASSESSMENT_CONFIG["min_answer_length"]:
        print("Answer too short. Please provide a more complete answer.")
        answer = input("Your answer: ").strip()
    
    # Evaluate answer
    print("\n🔍 Evaluating...")
    evaluation = evaluate_answer(question, answer, skill)
    print(format_evaluation_for_display(evaluation))
    
    # Store OA phase results
    results["oa_phase"]["questions"].append({
        "question": question,
        "answer": answer,
        "evaluation": evaluation
    })
    
    # Adaptive logic based on depth
    depth = evaluation.get("depth", "medium")
    results["oa_phase"]["final_depth"] = depth
    
    # ========== HINT + RE-ASK (if low depth) ==========
    if depth == "low" and results["oa_phase"]["hints_used"] < ASSESSMENT_CONFIG["max_hints_per_skill"]:
        print("\n💡 LOW DEPTH DETECTED - Providing hint and re-asking...\n")
        
        hint = generate_hint(skill, evaluation.get("gaps", []))
        print(f"HINT: {hint}\n")
        
        results["oa_phase"]["hints_used"] += 1
        
        # Re-ask
        answer2 = input("Try again with the hint in mind: ").strip()
        
        # Re-evaluate
        evaluation2 = evaluate_answer(question, answer2, skill)
        print(format_evaluation_for_display(evaluation2))
        
        results["oa_phase"]["questions"].append({
            "question": question,
            "answer": answer2,
            "evaluation": evaluation2,
            "hint_provided": hint
        })
        
        # Update depth based on improved answer
        depth = evaluation2.get("depth", depth)
        results["oa_phase"]["final_depth"] = depth
    
    # ========== INTERVIEW PHASE (if medium or high) ==========
    if depth in ["medium", "high"]:
        print("\n\n🎤 INTERVIEW PHASE - Deep dive questions...\n")
        
        # Interview Question 1
        q1 = generate_interview_question(skill, "medium")
        print(f"INTERVIEW Q1: {q1}\n")
        
        answer1 = input("Your answer: ").strip()
        eval1 = evaluate_answer(q1, answer1, skill)
        feedback1 = generate_feedback(eval1)
        
        print(f"\nFEEDBACK: {feedback1}\n")
        
        results["interview_phase"]["questions"].append({
            "question": q1,
            "answer": answer1,
            "evaluation": eval1,
            "feedback": feedback1
        })
        
        # Interview Question 2
        q2 = generate_interview_question(skill, "medium")
        print(f"\nINTERVIEW Q2: {q2}\n")
        
        answer2 = input("Your answer: ").strip()
        eval2 = evaluate_answer(q2, answer2, skill)
        feedback2 = generate_feedback(eval2)
        
        print(f"\nFEEDBACK: {feedback2}\n")
        
        results["interview_phase"]["questions"].append({
            "question": q2,
            "answer": answer2,
            "evaluation": eval2,
            "feedback": feedback2
        })
        
        # Calculate final score
        avg_interview_score = (eval1.get("correctness", 0.5) + eval2.get("correctness", 0.5)) / 2
        final_score = initial_score + (avg_interview_score * SCORING_CONFIG["interview_bonus"])
        final_score = min(final_score, 1.0)  # Cap at 1.0
        
        results["final_score"] = round(final_score, 2)
        results["score_delta"] = round(final_score - initial_score, 2)
        results["status"] = "verified" if final_score >= 0.7 else "partial"
    
    else:
        # Low depth after hints - needs more training
        results["status"] = "needs_training"
        results["final_score"] = initial_score * 0.8  # Slight decrease
        results["score_delta"] = results["final_score"] - initial_score
    
    # ========== FINAL SUMMARY ==========
    print("\n" + "="*60)
    print("ASSESSMENT COMPLETE")
    print("="*60)
    print(f"Skill: {skill}")
    print(f"Final Score: {results['final_score']}")
    print(f"Score Delta: {'+' if results['score_delta'] > 0 else ''}{results['score_delta']}")
    print(f"Status: {results['status'].upper()}")
    print("="*60 + "\n")
    
    return results

def run_micro_assessment(input_dict: dict) -> dict:
    """
    Main entry point for running the full micro assessment.
    
    Args:
        input_dict: Dict with missing skills from P2
    
    Returns:
        assessment_delta.json structure
    """
    
    print("🚀 Virtual Interview Engine - Starting Assessment")
    print("="*60)
    
    # Extract candidate info
    candidate_id = input_dict.get("candidate_id", "unknown")
    missing_skills = input_dict.get("missing_skills", [])
    
    if not missing_skills:
        print("No missing skills to assess.")
        return {
            "candidate_id": candidate_id,
            "status": "no_assessment_needed",
            "skills_assessed": []
        }
    
    print(f"Candidate: {candidate_id}")
    print(f"Skills to assess: {', '.join([s['skill'] for s in missing_skills])}")
    print()
    
    # Run assessment for each missing skill
    skills_assessed = []
    
    for skill_data in missing_skills:
        skill = skill_data.get("skill", "Unknown")
        current_score = skill_data.get("current_score", 0.5)
        
        result = run_assessment(skill, current_score)
        skills_assessed.append(result)
    
    # Calculate overall summary
    total_skills = len(skills_assessed)
    verified = sum(1 for s in skills_assessed if s["status"] == "verified")
    partial = sum(1 for s in skills_assessed if s["status"] == "partial")
    needs_training = sum(1 for s in skills_assessed if s["status"] == "needs_training")
    
    # Determine recommendation
    verified_ratio = verified / total_skills if total_skills > 0 else 0
    if verified_ratio >= RECOMMENDATION_CONFIG["hire_threshold"]:
        recommendation = "Hire"
    elif verified_ratio >= RECOMMENDATION_CONFIG["maybe_threshold"]:
        recommendation = "Maybe"
    else:
        recommendation = "No"
    
    # Build output
    output = {
        "candidate_id": candidate_id,
        "interview_date": datetime.now().isoformat(),
        "skills_assessed": skills_assessed,
        "overall_summary": {
            "total_skills_assessed": total_skills,
            "verified": verified,
            "partial": partial,
            "needs_training": needs_training,
            "final_recommendation": recommendation
        }
    }
    
    # Save to file
    output_path = "assessment_delta.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")
    print(f"\n📊 SUMMARY:")
    print(f"   Verified: {verified}/{total_skills}")
    print(f"   Partial: {partial}/{total_skills}")
    print(f"   Needs Training: {needs_training}/{total_skills}")
    print(f"   Recommendation: {recommendation}")
    
    return output

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Virtual Interview Engine")
    parser.add_argument("--input", type=str, help="Input JSON file with missing skills")
    parser.add_argument("--skill", type=str, help="Test a single skill")
    parser.add_argument("--api-key", type=str, help="Override API key")
    
    args = parser.parse_args()
    
    # Override API key if provided
    if args.api_key:
        import os
        os.environ["OPENAI_API_KEY"] = args.api_key
        print(f"Using API key: {args.api_key[:10]}...")
    
    if args.skill:
        # Test single skill mode
        result = run_assessment(args.skill)
        print(json.dumps(result, indent=2))
        
    elif args.input:
        # Full assessment from file
        input_data = load_input(args.input)
        output = run_micro_assessment(input_data)
        
    else:
        # Interactive mode
        print("Virtual Interview Engine - Interactive Mode")
        print("Enter 'quit' to exit\n")
        
        while True:
            skill = input("Enter a skill to assess (or 'quit' to exit): ").strip()
            
            if skill.lower() == 'quit':
                print("Goodbye!")
                break
            
            if skill:
                result = run_assessment(skill)
                print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
