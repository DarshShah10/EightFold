"""
Database Query Tools for GitHub Signals
=======================================
Quick queries to explore harvested data.
"""

import sqlite3
import json
from pathlib import Path
from modules.database import get_db_path, get_connection


def get_user_commits(handle: str, limit: int = 50) -> list:
    """Get recent commits for a user with code diffs."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.*, cf.filename, cf.patch, cf.additions as file_additions, cf.deletions as file_deletions
        FROM commits c
        LEFT JOIN commit_files cf ON c.sha = cf.commit_sha
        WHERE c.owner_handle = ?
        ORDER BY c.author_date DESC
        LIMIT ?
    """, (handle, limit))

    return [dict(row) for row in cursor.fetchall()]


def get_commit_code_diff(handle: str, sha: str) -> dict:
    """Get full code diff for a specific commit."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get commit info
    cursor.execute("SELECT * FROM commits WHERE sha = ? AND owner_handle = ?", (sha, handle))
    commit = dict(cursor.fetchone()) if cursor.fetchone() else None

    # Get files changed
    cursor.execute("""
        SELECT filename, status, additions, deletions, patch, is_test, is_docs, file_extension
        FROM commit_files
        WHERE commit_sha = ?
    """, (sha,))
    files = [dict(row) for row in cursor.fetchall()]

    return {
        "commit": commit,
        "files": files
    }


def get_code_stats_by_type(handle: str) -> dict:
    """Get code statistics grouped by commit type."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            commit_type,
            COUNT(*) as commit_count,
            SUM(additions) as total_additions,
            SUM(deletions) as total_deletions,
            SUM(num_files) as total_files,
            AVG(additions) as avg_additions,
            AVG(num_files) as avg_files
        FROM commits
        WHERE owner_handle = ?
        GROUP BY commit_type
        ORDER BY commit_count DESC
    """, (handle,))

    return [dict(row) for row in cursor.fetchall()]


def get_top_languages(handle: str) -> dict:
    """Get language breakdown from database."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT languages FROM languages
        WHERE owner_handle = ?
    """, (handle,))

    all_langs = {}
    for row in cursor.fetchall():
        langs = json.loads(row['languages'])
        for lang, bytes_count in langs.items():
            all_langs[lang] = all_langs.get(lang, 0) + bytes_count

    # Sort by bytes
    sorted_langs = dict(sorted(all_langs.items(), key=lambda x: x[1], reverse=True))
    total = sum(sorted_langs.values()) if sorted_langs else 1

    # Convert to MB and percentages
    result = {}
    for lang, bytes_count in sorted_langs.items():
        result[lang] = {
            "mb": round(bytes_count / (1024 * 1024), 2),
            "percent": round(bytes_count / total * 100, 1)
        }

    return result


def get_files_changed(handle: str, extension: str = None) -> list:
    """Get all files changed by a user."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if extension:
        cursor.execute("""
            SELECT DISTINCT cf.filename, cf.file_extension,
                   SUM(cf.additions) as total_add,
                   SUM(cf.deletions) as total_del,
                   COUNT(*) as commit_count
            FROM commit_files cf
            JOIN commits c ON cf.commit_sha = c.sha
            WHERE c.owner_handle = ? AND cf.file_extension = ?
            GROUP BY cf.filename
            ORDER BY commit_count DESC
            LIMIT 100
        """, (handle, extension))
    else:
        cursor.execute("""
            SELECT DISTINCT cf.filename, cf.file_extension,
                   SUM(cf.additions) as total_add,
                   SUM(cf.deletions) as total_del,
                   COUNT(*) as commit_count
            FROM commit_files cf
            JOIN commits c ON cf.commit_sha = c.sha
            WHERE c.owner_handle = ?
            GROUP BY cf.filename
            ORDER BY commit_count DESC
            LIMIT 100
        """, (handle,))

    return [dict(row) for row in cursor.fetchall()]


def get_pr_activity(handle: str) -> dict:
    """Get PR activity stats."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_prs,
            SUM(merged) as merged_prs,
            SUM(CASE WHEN merged = 0 THEN 1 ELSE 0 END) as closed_prs,
            AVG(time_to_merge_hours) as avg_time_to_merge,
            AVG(num_additions) as avg_pr_size,
            SUM(num_additions) as total_additions,
            SUM(num_deletions) as total_deletions
        FROM pull_requests
        WHERE owner_handle = ?
    """, (handle,))

    row = cursor.fetchone()
    return dict(row) if row else {}


def print_user_summary(handle: str) -> None:
    """Print comprehensive summary for a user."""
    print("\n" + "=" * 60)
    print(f"GITHUB SIGNALS SUMMARY - @{handle}")
    print("=" * 60)

    # Commit stats
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt, SUM(additions) as total_add, SUM(deletions) as total_del FROM commits WHERE owner_handle = ?", (handle,))
    row = cursor.fetchone()
    if row and row['cnt']:
        print(f"\nCOMMITS: {row['cnt']}")
        print(f"  Total additions: {row['total_add'] or 0:,} lines")
        print(f"  Total deletions: {row['total_del'] or 0:,} lines")

    # Commit types
    print("\nBY COMMIT TYPE:")
    for stat in get_code_stats_by_type(handle):
        print(f"  {stat['commit_type']:12} {stat['commit_count']:4} commits, "
              f"+{stat['total_additions']:,} -{stat['total_deletions']:,} lines")

    # Languages
    print("\nLANGUAGES:")
    for lang, info in list(get_top_languages(handle).items())[:5]:
        print(f"  {lang:15} {info['mb']:6.1f} MB ({info['percent']:5.1f}%)")

    # PRs
    print("\nPULL REQUESTS:")
    pr_stats = get_pr_activity(handle)
    if pr_stats and pr_stats.get('total_prs'):
        merge_rate = (pr_stats['merged_prs'] / pr_stats['total_prs'] * 100) if pr_stats['total_prs'] else 0
        print(f"  Total: {pr_stats['total_prs']}")
        print(f"  Merged: {pr_stats['merged_prs']} ({merge_rate:.0f}%)")
        print(f"  Avg time to merge: {pr_stats['avg_time_to_merge'] or 0:.1f} hours")
        print(f"  Avg PR size: +{pr_stats['avg_pr_size'] or 0:.0f} / -{pr_stats.get('avg_deletions', 0) or 0:.0f} lines")

    # Files
    print("\nTOP FILES CHANGED:")
    for file in get_files_changed(handle)[:5]:
        print(f"  {file['filename'][:50]:50} ({file['commit_count']} commits)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import sys
    handle = sys.argv[1] if len(sys.argv) > 1 else "gvanrossum"
    print_user_summary(handle)
