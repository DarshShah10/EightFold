"""
Quick Test Script for Harvester
================================
Run this to test the harvester with a sample GitHub handle.
"""

import os
import sys
import json
import time
import logging

# Fix Windows Unicode issues
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.harvester import harvest
from modules.client import get_github_token


def test_harvester(github_handle: str = None, output_dir: str = "data"):
    """
    Test the harvester on a GitHub handle.

    Args:
        github_handle: GitHub username (default: gvanrossum)
        output_dir: Directory to save output
    """
    if github_handle is None:
        github_handle = "gvanrossum"  # Python creator

    # Check for token (from .env or environment)
    token = get_github_token()
    if token:
        print(f"[OK] GitHub token: {token[:4]}...{token[-4:]}")
        print(f"[OK] Proceeding with harvest...")
    else:
        print("[WARNING] No GITHUB_TOKEN - using unauthenticated access")
        print("   Rate limited to 60 requests/hour")

    print("\n" + "-" * 60)
    print("Starting harvest... (target: under 5 minutes)")
    print("-" * 60)
    print()

    start_time = time.time()

    try:
        result = harvest(github_handle, output_dir)

        elapsed = time.time() - start_time

        # Check for errors
        errors = result.get("metadata", {}).get("errors", [])
        if errors:
            print("\n[WARNING] Harvest completed with errors:")
            for error in errors:
                print(f"   - {error}")

        # Print summary
        print("\n" + "=" * 60)
        print(f"HARVEST COMPLETE - @{github_handle}")
        print("=" * 60)

        meta = result.get("metadata", {})
        print(f"\nTotal Duration: {elapsed:.1f}s")

        # Speed indicator
        if elapsed <= 300:
            print(f"[OK] Within 5-minute target!")
        else:
            print(f"[SLOW] Exceeded 5-minute target by {elapsed - 300:.0f}s")

        print(f"\nDATA COLLECTED:")
        print(f"   Repositories: {meta.get('repos_count', 0)}")
        print(f"   Commits: {meta.get('commits_count', 0)}")
        print(f"   Pull Requests: {meta.get('prs_count', 0)}")
        print(f"   PR Reviews: {meta.get('reviews_count', 0)}")
        print(f"   Issues: {meta.get('issues_count', 0)}")
        print(f"   Issue Comments: {meta.get('comments_count', 0)}")
        print(f"   Contribution Events: {meta.get('events_count', 0)}")
        print(f"   Starred Repos: {meta.get('starred_count', 0)}")
        print(f"   Gists: {meta.get('gists_count', 0)}")
        print(f"   Organizations: {meta.get('orgs_count', 0)}")

        # User info
        user = result.get("user", {})
        if user and "error" not in user:
            print(f"\nUSER INFO:")
            print(f"   Name: {user.get('name', 'N/A')}")
            print(f"   Bio: {user.get('bio', 'N/A')}")
            print(f"   Location: {user.get('location', 'N/A')}")
            print(f"   Followers: {user.get('followers', 0)}")
            print(f"   Following: {user.get('following', 0)}")

        # Aggregates
        agg = result.get("aggregates", {})
        if agg:
            print(f"\nKEY METRICS:")
            print(f"   Avg Commit Size: {agg.get('avg_commit_size', 0):.1f} lines")
            print(f"   Avg Files/Commit: {agg.get('avg_files_per_commit', 0):.1f}")
            print(f"   Merge Rate: {agg.get('merge_rate', 0):.1%}")
            print(f"   Avg PR Size: {agg.get('avg_pr_size', 0):.1f} lines")
            print(f"   Test Coverage: {agg.get('test_coverage_ratio', 0):.1%}")
            print(f"   CI Usage: {agg.get('ci_usage_ratio', 0):.1%}")
            print(f"   Weekend Coding: {agg.get('weekend_coding_ratio', 0):.1%}")
            print(f"   Contributions/week: {agg.get('contributions_per_week', 0):.1f}")

        # Language breakdown
        lang_bytes = result.get("lang_bytes", {})
        if lang_bytes:
            print(f"\nLANGUAGES ({len(lang_bytes)} detected):")
            sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:5]
            for lang, bytes_count in sorted_langs:
                mb = bytes_count / (1024 * 1024)
                print(f"   {lang}: {mb:.1f} MB")

        # Output file
        output_file = os.path.join(output_dir, f"{github_handle}_raw.json")
        print(f"\nDATA SAVED TO: {output_file}")

        # Show file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"   File size: {size:.2f} MB")

        print("\n" + "=" * 60)
        print("HARVEST TEST SUCCESSFUL!")
        print("=" * 60)

        return result

    except Exception as e:
        print(f"\n[ERROR] HARVEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Get handle from command line or use default
    handle = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else "data"

    if handle == "--help":
        print("Usage: python run_harvester.py [github_handle] [output_dir]")
        print("Example: python run_harvester.py gvanrossum data")
        sys.exit(0)

    result = test_harvester(handle, output)
