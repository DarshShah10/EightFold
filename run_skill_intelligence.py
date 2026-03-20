"""
Module 3: Developer Skill Intelligence
======================================
Standalone runner for the SOTA Skill Intelligence Analyzer.

Usage:
    python run_skill_intelligence.py <github_handle> [--data-dir data] [--jd-file job_description.txt]

Features:
- Tech Stack Graph: Relationships between technologies
- Semantic Skills: What developers actually built
- Domain Fingerprint: Problem spaces (ML, Web3, DevOps, etc.)
- Modernity Score: How current is their stack
- Depth Index: Specialist vs generalist profile
- Project Impact: Beyond stars - real significance
- Ecosystem Alignment: Enterprise tool alignment
- Learning Velocity: Tech adoption speed
- Skill Level: Junior/Mid/Senior inference
- Tech Maturity: Best practices signals
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.skill_analyzer import SkillAnalyzer
from modules.dependency_analyzer import analyze_dependencies
from modules.candidate_profile import build_candidate_profile
from modules.explainability import explain_skill_intelligence
from modules.jd_matcher import match_jd_dynamic, parse_job_description, format_match_result, extract_skills_with_llm
from modules.storage import load_json


def main():
    parser = argparse.ArgumentParser(
        description="Developer Skill Intelligence Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_skill_intelligence.py gvanrossum
    python run_skill_intelligence.py torvalds --data-dir data
    python run_skill_intelligence.py octocat --jd-file senior_backend_jd.txt
        """
    )
    parser.add_argument("handle", help="GitHub handle to analyze")
    parser.add_argument("--data-dir", default="data", help="Data directory (default: data)")
    parser.add_argument("--jd-file", help="Path to job description file for JD matching")
    parser.add_argument("--output", help="Output file path (default: {data_dir}/{handle}_skill_intelligence.json)")
    parser.add_argument("--explainable", action="store_true",
                       help="Generate explainable output with full evidence chains")

    args = parser.parse_args()

    # Load raw data
    data_file = Path(args.data_dir) / f"{args.handle}_raw.json"

    if not data_file.exists():
        print(f"Error: Data file not found: {data_file}")
        print("Run the harvester first to fetch GitHub data:")
        print(f"  python run_harvester.py {args.handle}")
        sys.exit(1)

    print(f"Loading data from {data_file}...")
    raw_data = load_json(data_file)

    if not raw_data:
        print("Error: Could not load data file")
        sys.exit(1)

    # Extract data for skill analysis - use FULL harvested data
    repos = raw_data.get("repos", []) or []
    commits = raw_data.get("commits", []) or []
    issues = raw_data.get("issues", []) or []
    pull_requests = raw_data.get("pull_requests", []) or []
    branches = raw_data.get("branches", {}) or {}
    releases = raw_data.get("releases", {}) or {}
    aggregates = raw_data.get("aggregates", {}) or {}
    dep_files = raw_data.get("dep_files", {}) or {}

    print(f"Analyzing {len(repos)} repositories with {len(commits)} commits...")

    # Build skill analysis input with ALL data
    skill_raw_data = {
        "repos": repos,
        "lang_bytes": raw_data.get("lang_bytes", {}),
        "commits": commits,
        "issues": issues,
        "pull_requests": pull_requests,
        "branches": branches,
        "releases": releases,
        "aggregates": aggregates,
    }

    # Load JD if provided
    jd_requirements = None
    if args.jd_file:
        print(f"Loading job description from {args.jd_file}...")
        with open(args.jd_file, "r", encoding="utf-8") as f:
            jd_text = f.read()
        # Simple JD parsing - extract requirements
        jd_requirements = extract_jd_requirements(jd_text)

    # Run skill analysis
    print("Running Skill Intelligence analysis...")
    analyzer = SkillAnalyzer()
    skill_result = analyzer.analyze(skill_raw_data, jd_requirements=jd_requirements)

    # Run dependency analysis
    print("Running Dependency Analysis...")
    dep_raw_data = {
        "dep_files": dep_files,
        "repos": repos,
    }
    dep_result = analyze_dependencies(dep_raw_data)

    # Build output
    output_data = {
        "handle": args.handle,
        "skill_profile": {
            "skill_level": skill_result.skill_profile.skill_level,
            "skill_level_confidence": round(skill_result.skill_profile.skill_level_confidence, 2),
            "primary_domains": skill_result.skill_profile.primary_domains,
            "secondary_domains": skill_result.skill_profile.secondary_domains,
            "depth_index": {
                "specialist_language": skill_result.skill_profile.depth_index.specialist_language,
                "specialist_score": round(skill_result.skill_profile.depth_index.specialist_score, 2),
                "breadth_score": skill_result.skill_profile.depth_index.breadth_score,
                "category": skill_result.skill_profile.depth_index.depth_category,
            },
            "years_experience_estimate": skill_result.skill_profile.years_experience_estimate,
            "organization_ready": skill_result.skill_profile.organization_ready,
            "growth_indicators": skill_result.skill_profile.growth_indicators,
        },
        "tech_stack": {
            "primary_stack": skill_result.skill_profile.tech_graph.primary_stack,
            "related_stacks": skill_result.skill_profile.tech_graph.related_stacks,
            "language_depth": skill_result.language_depth,
            "frameworks": skill_result.frameworks,
            "infrastructure": skill_result.infrastructure,
        },
        "modernity": {
            "overall_score": skill_result.skill_profile.modernity_score.overall_score,
            "age_score": skill_result.skill_profile.modernity_score.age_score,
            "ecosystem_score": skill_result.skill_profile.modernity_score.ecosystem_score,
            "patterns_score": skill_result.skill_profile.modernity_score.patterns_score,
            "signals": skill_result.skill_profile.modernity_score.signals,
            "warnings": skill_result.skill_profile.modernity_score.warnings,
        },
        "domains": [
            {
                "domain": d.domain,
                "confidence": round(d.confidence, 2),
                "signals": d.signals,
            }
            for d in skill_result.detected_domains
        ],
        "top_repos": [
            {
                "name": r["name"],
                "impact_score": round(r.get("impact", {}).get("impact_score", 0), 1),
                "stars": r.get("stars", 0),
                "forks": r.get("forks", 0),
                "project_type": r.get("project_type", ""),
                "recency_score": round(r.get("recency_score", 0), 2),
            }
            for r in skill_result.top_repos
        ],
        "insights": skill_result.insights,
        "jd_fit": skill_result.jd_fit,
        "signals": {k: round(v, 3) for k, v in skill_result.signals.items()},
        # Dependency analysis
        "dependencies": {
            "philosophy": dep_result.get("engineering_philosophy", {}),
            "scores": dep_result.get("philosophy_scores", {}),
            "ecosystem": dep_result.get("ecosystem", {}),
            "trends": dep_result.get("trends", []),
        },
    }

    # Save output
    output_file = args.output or f"{args.data_dir}/{args.handle}_skill_intelligence.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SKILL INTELLIGENCE REPORT")
    print("=" * 60)

    print(f"\nSkill Level: {output_data['skill_profile']['skill_level']} "
          f"(confidence: {output_data['skill_profile']['skill_level_confidence']:.0%})")

    print(f"\nPrimary Domains: {', '.join(output_data['skill_profile']['primary_domains'])}")
    if output_data['skill_profile']['secondary_domains']:
        print(f"Secondary Domains: {', '.join(output_data['skill_profile']['secondary_domains'])}")

    print(f"\nDepth Index: {output_data['skill_profile']['depth_index']['category']} "
          f"(specialist: {output_data['skill_profile']['depth_index']['specialist_language']})")

    print(f"\nModernity Score: {output_data['modernity']['overall_score']:.1f}%")
    if output_data['modernity']['warnings']:
        print(f"  Warnings: {', '.join(set(output_data['modernity']['warnings']))}")

    print(f"\nTech Stack: {output_data['tech_stack']['primary_stack']}")
    if output_data['tech_stack']['frameworks']:
        print(f"  Frameworks: {', '.join(output_data['tech_stack']['frameworks'][:5])}")
    if output_data['tech_stack']['infrastructure']:
        print(f"  Infrastructure: {', '.join(output_data['tech_stack']['infrastructure'][:5])}")

    print(f"\nTop Repositories by Impact:")
    for i, repo in enumerate(output_data['top_repos'][:3], 1):
        print(f"  {i}. {repo['name']} (score: {repo['impact_score']:.1f}, stars: {repo['stars']})")

    print(f"\nInsights:")
    for insight in output_data['insights']:
        print(f"  • {insight}")

    if output_data['jd_fit']:
        print(f"\nJD Match Score: {output_data['jd_fit']['score']:.0f}%")
        print(f"  {output_data['jd_fit']['summary']}")

    print(f"\nResults saved to: {output_file}")
    print("=" * 60)

    # Generate explainable output if requested
    if args.explainable:
        print("\n" + "=" * 60)
        print("GENERATING EXPLAINABLE REPORT...")
        print("=" * 60)

        # Build raw data with handle
        raw_data["handle"] = args.handle

        # Generate explainable result
        explainable = explain_skill_intelligence(raw_data, skill_result)

        # Convert to dict for JSON serialization
        explainable_dict = {
            "candidate": explainable.candidate,
            "confidence": round(explainable.confidence, 2),
            "summary": explainable.summary,
            "primary_language": explainable.primary_language,
            "primary_language_depth": round(explainable.primary_language_depth, 2),
            "domains": explainable.domains,
            "caveats": explainable.caveats,
            "skill_assessment": {
                name: {
                    "skill": skill.skill,
                    "level": skill.level,
                    "confidence": round(skill.confidence, 2),
                    "evidence": skill.evidence,
                    "reasoning": skill.reasoning,
                    "gaps": skill.gaps,
                    "contributing_repos": skill.contributing_repos,
                    "supporting_signals": skill.supporting_signals,
                }
                for name, skill in explainable.skill_assessment.items()
            },
            "project_evidence": [
                {
                    "name": p.name,
                    "full_name": p.full_name,
                    "impact": p.impact,
                    "stars": p.stars,
                    "forks": p.forks,
                    "skills_demonstrated": p.skills_demonstrated,
                    "signals": p.signals,
                    "why_it_matters": p.why_it_matters,
                    "complexity_signals": p.complexity_signals,
                }
                for p in explainable.project_evidence
            ],
            "problem_solving_traces": [
                {
                    "type": t.type,
                    "repo": t.repo,
                    "repo_name": t.repo_name,
                    "commit_hash": t.commit_hash,
                    "summary": t.summary,
                    "quality_signal": t.quality_signal,
                    "files_changed": t.files_changed,
                    "lines_added": t.lines_added,
                    "lines_deleted": t.lines_deleted,
                    "is_verified": t.is_verified,
                }
                for t in explainable.problem_solving_traces
            ],
        }

        # Save explainable output
        explainable_file = args.output or f"{args.data_dir}/{args.handle}_explainable.json"
        with open(explainable_file, "w", encoding="utf-8") as f:
            json.dump(explainable_dict, f, indent=2, ensure_ascii=False)

        # Print explainable summary
        print(f"\nEXPLAINABLE ASSESSMENT")
        print("=" * 60)
        print(f"\nWe believe: {explainable.summary}")

        print(f"\nSkills with Evidence:")
        for name, skill in explainable.skill_assessment.items():
            print(f"\n  {skill.skill} ({skill.level}, confidence: {skill.confidence:.0%})")
            if skill.reasoning:
                print(f"    Because:")
                for reason in skill.reasoning[:2]:  # Show top 2 reasons
                    print(f"      • {reason}")
            if skill.gaps:
                print(f"    Gaps: {', '.join(skill.gaps[:2])}")

        if explainable.project_evidence:
            print(f"\n  Key Projects:")
            for proj in explainable.project_evidence[:3]:
                print(f"    • {proj.name}: {proj.why_it_matters[:80]}...")

        if explainable.problem_solving_traces:
            print(f"\n  Notable Problem-Solving Traces:")
            for trace in explainable.problem_solving_traces[:3]:
                print(f"    • [{trace.type}] {trace.repo}: {trace.summary[:60]}...")

        if explainable.caveats:
            print(f"\n  Caveats:")
            for caveat in explainable.caveats:
                print(f"    ⚠ {caveat}")

        print(f"\nFull explainable report saved to: {explainable_file}")
        print("=" * 60)

    # Run JD matching if jd-file is provided
    if args.jd_file:
        print("\n" + "=" * 60)
        print("RUNNING JD MATCHING ANALYSIS...")
        print("=" * 60)

        # Load JD
        print(f"\nLoading job description from {args.jd_file}...")
        with open(args.jd_file, "r", encoding="utf-8") as f:
            jd_text = f.read()

        # Extract skills dynamically (LLM-powered if available)
        print("\nExtracting skills from job description...")
        extracted_skills = extract_skills_with_llm(jd_text)
        print(f"  Skills extracted: {', '.join(extracted_skills[:10])}")
        if len(extracted_skills) > 10:
            print(f"  ... and {len(extracted_skills) - 10} more")

        # Run JD matching (dynamic v2)
        print("\nMatching candidate against job requirements (dynamic matching)...")
        jd_match_result = match_jd_dynamic(args.handle, raw_data, jd_text)

        # Print formatted report
        report = format_match_result(jd_match_result)
        print("\n" + report)

        # Save JD match result
        jd_match_file = f"{args.data_dir}/{args.handle}_jd_match_{Path(args.jd_file).stem}.json"

        # Convert to dict for JSON serialization
        jd_match_dict = {
            "candidate": jd_match_result.candidate,
            "job_title": jd_match_result.job_title,
            "overall_match_score": round(jd_match_result.overall_match_score, 1),
            "recommendation": jd_match_result.recommendation,
            "summary": jd_match_result.summary,
            "matched_count": jd_match_result.matched_count,
            "missing_count": jd_match_result.missing_count,
            "category_scores": jd_match_result.category_scores,
            "strengths": jd_match_result.strengths,
            "gaps": jd_match_result.gaps,
            "critical_gaps": jd_match_result.critical_gaps,
            "analysis_timestamp": jd_match_result.analysis_timestamp,
            "mandatory_skills": [
                {
                    "skill": m.skill_key,
                    "category": m.category,
                    "is_match": m.match_result.is_match,
                    "confidence": round(m.match_result.confidence, 2),
                    "evidence_summary": m.match_result.evidence_summary,
                    "missing_reason": m.match_result.missing_reason,
                    "evidence": [
                        {
                            "url": e.url,
                            "type": e.type,
                            "description": e.description,
                            "weight": e.weight,
                            "verified": e.verified,
                        }
                        for e in m.match_result.evidence
                    ],
                    "contributing_repos": m.match_result.contributing_repos,
                }
                for m in jd_match_result.mandatory_skills
            ],
            "nice_to_have_skills": [
                {
                    "skill": m.skill_key,
                    "category": m.category,
                    "is_match": m.match_result.is_match,
                    "confidence": round(m.match_result.confidence, 2),
                    "evidence_summary": m.match_result.evidence_summary,
                }
                for m in jd_match_result.nice_to_have_skills
            ],
        }

        with open(jd_match_file, "w", encoding="utf-8") as f:
            json.dump(jd_match_dict, f, indent=2, ensure_ascii=False)

        print(f"\nJD match report saved to: {jd_match_file}")


def extract_jd_requirements(jd_text: str) -> list[str]:
    """Extract requirements from job description text."""
    requirements = []

    # Look for common section headers
    import re
    sections = re.split(r"(?:requirements?|skills?|must-?have|needed)", jd_text.lower())

    for section in sections[1:]:  # Skip the first part (before first requirement)
        # Extract bullet points and line items
        lines = re.split(r"[-•*•]\s*|\n+", section)
        for line in lines:
            line = line.strip()
            if len(line) > 5 and len(line) < 100:  # Reasonable requirement length
                requirements.append(line)

    return requirements[:20]  # Limit to 20 requirements


if __name__ == "__main__":
    main()
