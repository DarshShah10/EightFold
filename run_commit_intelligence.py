"""
Module 2: Commit Intelligence Engine - Runner Script
=====================================================
Run this to analyze commits and generate intelligence report.

Usage:
    python run_commit_intelligence.py [github_handle] [data_dir]

Example:
    python run_commit_intelligence.py gvanrossum data
"""

import json
import os
import sys

# Fix Windows Unicode issues
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.commit_analyzer import analyze_commits


def print_banner():
    """Print program banner."""
    print("=" * 70)
    print("  COMMIT INTELLIGENCE ENGINE")
    print("  State-of-the-art developer profiling from GitHub commits")
    print("=" * 70)
    print()


def print_dimension_score(name: str, score: float, width: int = 30):
    """Print a dimension score with a visual bar."""
    name_formatted = name.replace('_', ' ').title()
    bar_length = int(score / 100 * width)
    bar = "█" * bar_length + "░" * (width - bar_length)
    color_indicator = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
    print(f"  {color_indicator} {name_formatted:25} [{bar}] {score:.1f}")


def print_profile(profile: dict):
    """Print developer profile."""
    if not profile:
        print("  No profile available")
        return

    print(f"\n  👤 ARCHETYPE: {profile.get('archetype', 'Unknown')}")
    print(f"  📊 Confidence: {profile.get('confidence', 0) * 100:.0f}%")
    print(f"  📝 \"{profile.get('tagline', '')}\"")

    if profile.get('strengths'):
        print("\n  ⭐ Strengths:")
        for strength in profile['strengths'][:3]:
            print(f"     • {strength}")

    if profile.get('growth_areas'):
        print("\n  📈 Growth Areas:")
        for area in profile['growth_areas'][:2]:
            print(f"     • {area}")


def print_citations(citations: list):
    """Print top citations."""
    if not citations:
        print("\n  No notable achievements detected")
        return

    print(f"\n  🏆 TOP ACHIEVEMENTS ({len(citations)} detected):")
    for i, citation in enumerate(citations[:5], 1):
        print(f"\n  {i}. {citation['title']}")
        print(f"     {citation['description'][:80]}...")


def print_signals(signals: dict):
    """Print top signals."""
    # Select most interesting signals to display
    key_signals = [
        "files_per_commit_mean",
        "avg_commit_size",
        "refactor_ratio",
        "fix_ratio",
        "feat_ratio",
        "test_coverage_ratio",
        "conventional_commit_ratio",
        "weekend_commit_ratio",
        "consistency_score",
        "architectural_complexity_score",
    ]

    print("\n  📊 KEY SIGNALS:")
    for signal in key_signals:
        if signal in signals:
            value = signals[signal]
            name = signal.replace('_', ' ').title()
            if isinstance(value, float):
                print(f"     • {name}: {value:.2f}")
            else:
                print(f"     • {name}: {value}")


def run_analysis(handle: str, data_dir: str = "data") -> dict:
    """
    Run commit intelligence analysis on a user's data.

    Args:
        handle: GitHub username
        data_dir: Directory containing raw data

    Returns:
        Analysis result dictionary
    """
    # Find data file
    data_file = os.path.join(data_dir, f"{handle}_raw.json")

    if not os.path.exists(data_file):
        print(f"\n❌ Error: Raw data file not found: {data_file}")
        print("   Run Module 1 (harvester) first:")
        print(f"   python run_harvester.py {handle}")
        return None

    print(f"📂 Loading data from: {data_file}")

    # Load raw data
    with open(data_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    commits = raw_data.get("commits", [])
    repos = raw_data.get("repos", [])

    if not commits:
        print("\n❌ Error: No commits found in data file")
        print("   Run Module 1 (harvester) first to fetch commits")
        return None

    print(f"📊 Analyzing {len(commits)} commits from {len(repos)} repositories...")
    print()

    # Run analysis
    result = analyze_commits(commits, repos)

    return result


def main():
    """Main entry point."""
    print_banner()

    # Get arguments
    handle = sys.argv[1] if len(sys.argv) > 1 else None
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "data"

    if not handle:
        handle = input("Enter GitHub handle: ").strip()
        if not handle:
            print("No handle provided. Exiting.")
            sys.exit(1)

    # Run analysis
    result = run_analysis(handle, data_dir)

    if not result:
        sys.exit(1)

    # Display results
    print()
    print("=" * 70)
    print("  ANALYSIS RESULTS")
    print("=" * 70)

    # Overall score
    print(f"\n  🎯 COMMIT INTELLIGENCE SCORE: {result['commit_intelligence_score']:.1f}/100")

    # Dimension scores
    print("\n  DIMENSION SCORES:")
    for dim_name, score in result.get("dimensions", {}).items():
        print_dimension_score(dim_name, score)

    # Profile
    print_profile(result.get("profile"))

    # Citations
    print_citations(result.get("citations"))

    # Key signals
    print_signals(result.get("signals", {}))

    # Metadata
    meta = result.get("metadata", {})
    print(f"\n  📅 Analysis Period: {meta.get('date_range_days', 0)} days")
    print(f"  📝 Commits Analyzed: {meta.get('commits_analyzed', 0)}")

    # Save results
    output_file = os.path.join(data_dir, f"{handle}_commit_intelligence.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n  💾 Results saved to: {output_file}")
    print()
    print("=" * 70)
    print("  ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
