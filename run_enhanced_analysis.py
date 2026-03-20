"""
Enhanced Commit Intelligence - Runner Script
============================================
Run JD-driven and LLM-powered commit analysis.

Usage:
    # Basic analysis
    python run_enhanced_analysis.py gvanrossum

    # With job description file
    python run_enhanced_analysis.py gvanrossum --jd-file sample_jd.txt

    # With job description text
    python run_enhanced_analysis.py gvanrossum --jd-text "Looking for Python developer..."

    # With LLM summary only
    python run_enhanced_analysis.py gvanrossum --llm-only
"""

import argparse
import json
import os
import sys

# Fix Windows Unicode issues
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print program banner."""
    print("=" * 70)
    print("  ENHANCED COMMIT INTELLIGENCE ENGINE")
    print("  JD-Driven & LLM-Powered Developer Analysis")
    print("=" * 70)
    print()


def print_scores(result: dict):
    """Print score breakdown."""
    print("\n📊 SCORES:")
    print(f"   Base Score:      {result.get('original_score', result.get('commit_intelligence_score', 0)):.1f}/100")

    if result.get('jd_adjusted_score') is not None:
        print(f"   JD-Adjusted:     {result['jd_adjusted_score']:.1f}/100")

    if result.get('llm_insights', {}).get('fit_score'):
        fit = result['llm_insights']['fit_score']
        print(f"   Role Fit Score:  {fit:.0f}/100")

    print("\n   Dimension Breakdown:")
    dims = result.get('dimensions', {})
    for dim, score in dims.items():
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        indicator = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
        print(f"   {indicator} {dim.replace('_', ' ').title():20} [{bar}] {score:.1f}")


def print_jd_analysis(result: dict):
    """Print JD analysis if available."""
    jd = result.get('jd_analysis', {})
    if not jd:
        return

    print("\n📋 JD ANALYSIS:")
    print(f"   Inferred Role Type: {jd.get('inferred_role_type', 'generalist').title()}")

    if jd.get('requirements'):
        print("\n   Key Requirements:")
        for req in jd['requirements'][:5]:
            importance = "★★★" if req['importance'] >= 1.0 else "★★" if req['importance'] >= 0.7 else "★"
            print(f"   {importance} {req['skill']} ({req['category']})")

    if jd.get('preferred_archetypes'):
        print(f"\n   Preferred Profiles: {', '.join(jd['preferred_archetypes'])}")


def print_profile(result: dict):
    """Print developer profile."""
    profile = result.get('profile')
    if not profile:
        return

    print("\n👤 DEVELOPER PROFILE:")
    print(f"   Archetype: {profile.get('archetype', 'Unknown')}")
    print(f"   Confidence: {profile.get('confidence', 0) * 100:.0f}%")
    print(f"   \"{profile.get('tagline', '')}\"")

    if profile.get('strengths'):
        print("\n   ⭐ Strengths:")
        for s in profile['strengths'][:3]:
            print(f"      • {s}")

    if profile.get('growth_areas'):
        print("\n   📈 Growth Areas:")
        for g in profile['growth_areas'][:2]:
            print(f"      • {g}")


def print_llm_insights(result: dict):
    """Print LLM-generated insights."""
    insights = result.get('llm_insights', {})
    if not insights:
        return

    print("\n🧠 LLM INSIGHTS:")

    if insights.get('fit_score'):
        print(f"   Role Fit Score: {insights['fit_score']:.0f}/100")
        if insights.get('fit_reasoning'):
            print(f"   Reasoning: {insights['fit_reasoning'][:150]}...")

    if insights.get('strengths'):
        print("\n   Key Strengths:")
        for s in insights['strengths'][:3]:
            print(f"      • {s}")

    if insights.get('red_flags'):
        print("\n   ⚠️  Red Flags:")
        for r in insights['red_flags'][:2]:
            print(f"      • {r}")


def print_citations(result: dict):
    """Print citations/achievements."""
    citations = result.get('citations', [])
    if not citations:
        return

    print(f"\n🏆 TOP ACHIEVEMENTS ({len(citations)} detected):")
    for i, c in enumerate(citations[:3], 1):
        print(f"\n   {i}. {c.get('title', 'Unknown')}")
        print(f"      {c.get('description', '')[:80]}...")


def print_llm_summary(result: dict):
    """Print LLM-generated summary."""
    summary = result.get('llm_summary')
    if not summary:
        return

    print("\n" + "─" * 50)
    print("📝 LLM SUMMARY:")
    print("─" * 50)
    print(f"\n{summary}")
    print("─" * 50)


def main():
    """Main entry point."""
    from modules.commit_analyzer import EnhancedIntelligenceEngine

    parser = argparse.ArgumentParser(
        description="Enhanced Commit Intelligence Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_enhanced_analysis.py gvanrossum
  python run_enhanced_analysis.py gvanrossum --jd-file sample_jd.txt
  python run_enhanced_analysis.py gvanrossum --jd-text "Python developer needed"
        """
    )

    parser.add_argument("handle", help="GitHub handle")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument("--jd-file", help="Path to job description file")
    parser.add_argument("--jd-text", help="Job description text (alternative to --jd-file)")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM features")

    args = parser.parse_args()

    print_banner()

    # Load raw data
    data_file = os.path.join(args.data_dir, f"{args.handle}_raw.json")

    if not os.path.exists(data_file):
        print(f"\n❌ Error: Data file not found: {data_file}")
        print("   Run Module 1 (harvester) first:")
        print(f"   python run_harvester.py {args.handle}")
        sys.exit(1)

    print(f"📂 Loading data from: {data_file}")
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    commits = data.get("commits", [])
    repos = data.get("repos", [])

    if not commits:
        print("\n❌ Error: No commits found in data file")
        sys.exit(1)

    print(f"📊 Analyzing {len(commits)} commits from {len(repos)} repositories...")

    # Load JD if provided
    jd_text = args.jd_text
    if args.jd_file:
        if os.path.exists(args.jd_file):
            print(f"📋 Loading JD from: {args.jd_file}")
            with open(args.jd_file, "r", encoding="utf-8") as f:
                jd_text = f.read()
        else:
            print(f"⚠️  JD file not found: {args.jd_file}")

    # Run analysis
    print("\n🔍 Running analysis...")
    if args.no_llm:
        # Patch to disable LLM
        from modules.commit_analyzer import llm_client as llm_module
        original_get = llm_module.get_llm_client
        llm_module.get_llm_client = lambda: type('MockClient', (), {'is_available': lambda self: False})()

    engine = EnhancedIntelligenceEngine()
    result = engine.analyze(commits, repos, jd_text=jd_text)

    if args.no_llm:
        llm_module.get_llm_client = original_get

    # Print results
    print_scores(result)
    print_jd_analysis(result)
    print_profile(result)
    print_citations(result)
    print_llm_insights(result)

    if result.get('llm_summary'):
        print_llm_summary(result)

    # Save results
    output_file = args.output or os.path.join(args.data_dir, f"{args.handle}_enhanced_analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: {output_file}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
