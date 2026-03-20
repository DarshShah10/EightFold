"""
SQLite Database for GitHub Signal Storage
==========================================
Stores all harvested data in a local SQLite database for fast queries.
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("data/github_signals.db")


def get_db_path() -> Path:
    """Get or create database path."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            github_handle TEXT UNIQUE NOT NULL,
            name TEXT,
            bio TEXT,
            company TEXT,
            location TEXT,
            blog TEXT,
            email TEXT,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0,
            public_repos INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            last_harvested TEXT
        )
    """)

    # Repositories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER,
            full_name TEXT UNIQUE NOT NULL,
            owner TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            language TEXT,
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            watchers INTEGER DEFAULT 0,
            open_issues INTEGER DEFAULT 0,
            size INTEGER DEFAULT 0,
            topics TEXT,  -- JSON array
            isFork INTEGER DEFAULT 0,
            isPrivate INTEGER DEFAULT 0,
            has_wiki INTEGER DEFAULT 1,
            default_branch TEXT,
            created_at TEXT,
            updated_at TEXT,
            pushed_at TEXT,
            owner_handle TEXT,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # Commits table (with code diffs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sha TEXT UNIQUE NOT NULL,
            repo_name TEXT NOT NULL,
            author_name TEXT,
            author_email TEXT,
            committer_name TEXT,
            message TEXT,
            message_full TEXT,
            commit_type TEXT,  -- feat, fix, refactor, etc.
            additions INTEGER DEFAULT 0,
            deletions INTEGER DEFAULT 0,
            total_lines INTEGER DEFAULT 0,
            num_files INTEGER DEFAULT 0,
            num_test_files INTEGER DEFAULT 0,
            num_docs_files INTEGER DEFAULT 0,
            is_merge INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            author_date TEXT,
            committer_date TEXT,
            hour_of_day INTEGER,
            day_of_week INTEGER,
            is_weekend INTEGER DEFAULT 0,
            owner_handle TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # Commit files table (actual code changes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commit_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commit_sha TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_extension TEXT,
            status TEXT,  -- added, modified, deleted
            additions INTEGER DEFAULT 0,
            deletions INTEGER DEFAULT 0,
            patch TEXT,  -- actual diff
            is_test INTEGER DEFAULT 0,
            is_docs INTEGER DEFAULT 0,
            is_config INTEGER DEFAULT 0,
            repo_name TEXT,
            FOREIGN KEY (commit_sha) REFERENCES commits(sha)
        )
    """)

    # Pull requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pull_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_id INTEGER,
            repo_name TEXT NOT NULL,
            number INTEGER NOT NULL,
            title TEXT,
            body TEXT,
            state TEXT,
            merged INTEGER DEFAULT 0,
            merged_by TEXT,
            author TEXT,
            created_at TEXT,
            updated_at TEXT,
            closed_at TEXT,
            merged_at TEXT,
            time_to_merge_hours REAL,
            time_to_close_hours REAL,
            num_commits INTEGER DEFAULT 0,
            num_files_changed INTEGER DEFAULT 0,
            num_comments INTEGER DEFAULT 0,
            num_review_comments INTEGER DEFAULT 0,
            num_additions INTEGER DEFAULT 0,
            num_deletions INTEGER DEFAULT 0,
            labels TEXT,  -- JSON array
            is_draft INTEGER DEFAULT 0,
            owner_handle TEXT,
            created_at_db TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # PR reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pr_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT NOT NULL,
            pr_number INTEGER NOT NULL,
            reviewer TEXT NOT NULL,
            state TEXT,
            body TEXT,
            submitted_at TEXT,
            commit_id TEXT,
            owner_handle TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # Issues table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER,
            repo_name TEXT NOT NULL,
            number INTEGER NOT NULL,
            title TEXT,
            body TEXT,
            state TEXT,
            author TEXT,
            created_at TEXT,
            updated_at TEXT,
            closed_at TEXT,
            comments INTEGER DEFAULT 0,
            labels TEXT,  -- JSON array
            is_pull_request INTEGER DEFAULT 0,
            owner_handle TEXT,
            created_at_db TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # Languages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT UNIQUE NOT NULL,
            languages TEXT NOT NULL,  -- JSON object {language: bytes}
            total_bytes INTEGER DEFAULT 0,
            owner_handle TEXT,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # Organizations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            name TEXT,
            description TEXT,
            public_repos INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0,
            owner_handle TEXT,
            FOREIGN KEY (owner_handle) REFERENCES users(github_handle)
        )
    """)

    # Create indexes for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_owner ON commits(owner_handle)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_repo ON commits(repo_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_type ON commits(commit_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(author_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prs_owner ON pull_requests(owner_handle)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_issues_owner ON issues(owner_handle)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repos_owner ON repositories(owner_handle)")

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {get_db_path()}")


def save_user(handle: str, user_data: Dict[str, Any]) -> None:
    """Save user data to database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users (
            github_handle, name, bio, company, location, blog, email,
            followers, following, public_repos, created_at, updated_at, last_harvested
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        handle,
        user_data.get('name'),
        user_data.get('bio'),
        user_data.get('company'),
        user_data.get('location'),
        user_data.get('blog'),
        user_data.get('email'),
        user_data.get('followers', 0),
        user_data.get('following', 0),
        user_data.get('public_repos', 0),
        user_data.get('created_at'),
        user_data.get('updated_at'),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def save_repos(handle: str, repos: List[Dict[str, Any]]) -> None:
    """Save repositories to database."""
    conn = get_connection()
    cursor = conn.cursor()

    for repo in repos:
        topics = json.dumps(repo.get('topics', []))
        cursor.execute("""
            INSERT OR REPLACE INTO repositories (
                repo_id, full_name, owner, name, description, language,
                stars, forks, watchers, open_issues, size, topics,
                isFork, isPrivate, has_wiki, default_branch,
                created_at, updated_at, pushed_at, owner_handle
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repo.get('id'),
            repo.get('full_name'),
            repo.get('owner'),
            repo.get('name'),
            repo.get('description'),
            repo.get('language'),
            repo.get('stargazers_count', 0),
            repo.get('forks_count', 0),
            repo.get('watchers_count', 0),
            repo.get('open_issues_count', 0),
            repo.get('size', 0),
            topics,
            int(repo.get('fork', False)),
            int(repo.get('private', False)),
            int(repo.get('has_wiki', True)),
            repo.get('default_branch'),
            repo.get('created_at'),
            repo.get('updated_at'),
            repo.get('pushed_at'),
            handle
        ))

    conn.commit()
    conn.close()


def save_commits(handle: str, commits: List[Dict[str, Any]]) -> None:
    """Save commits with full details to database."""
    conn = get_connection()
    cursor = conn.cursor()

    for commit in commits:
        # Skip commits with errors
        if commit.get('error'):
            continue

        sha = commit.get('sha', '')

        # Save commit
        cursor.execute("""
            INSERT OR REPLACE INTO commits (
                sha, repo_name, author_name, author_email, committer_name,
                message, message_full, commit_type,
                additions, deletions, total_lines, num_files,
                num_test_files, num_docs_files, is_merge, verified,
                author_date, committer_date, hour_of_day, day_of_week, is_weekend, owner_handle
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sha,
            commit.get('repo_name'),
            commit.get('author_name'),
            commit.get('author_email'),
            commit.get('committer_name'),
            commit.get('message'),
            commit.get('message_full'),
            commit.get('commit_type', 'other'),
            commit.get('additions', 0),
            commit.get('deletions', 0),
            commit.get('total_lines', 0),
            commit.get('num_files', 0),
            commit.get('num_test_files', 0),
            commit.get('num_docs_files', 0),
            int(commit.get('is_merge', False)),
            int(commit.get('verified', False)),
            commit.get('author_date'),
            commit.get('committer_date'),
            commit.get('hour_of_day'),
            commit.get('day_of_week'),
            int(commit.get('is_weekend', False)),
            handle
        ))

        # Save commit files (actual code changes)
        for file_data in commit.get('files', []):
            cursor.execute("""
                INSERT INTO commit_files (
                    commit_sha, filename, file_extension, status,
                    additions, deletions, patch, is_test, is_docs, is_config, repo_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sha,
                file_data.get('filename'),
                file_data.get('file_extension'),
                file_data.get('status'),
                file_data.get('additions', 0),
                file_data.get('deletions', 0),
                file_data.get('patch'),  # actual diff!
                int(file_data.get('is_test', False)),
                int(file_data.get('is_docs', False)),
                int(file_data.get('is_config', False)),
                commit.get('repo_name')
            ))

    conn.commit()
    conn.close()


def save_pull_requests(handle: str, prs: List[Dict[str, Any]]) -> None:
    """Save pull requests to database."""
    conn = get_connection()
    cursor = conn.cursor()

    for pr in prs:
        labels = json.dumps(pr.get('labels', []))
        cursor.execute("""
            INSERT OR REPLACE INTO pull_requests (
                pr_id, repo_name, number, title, body, state,
                merged, merged_by, author, created_at, updated_at,
                closed_at, merged_at, time_to_merge_hours, time_to_close_hours,
                num_commits, num_files_changed, num_comments, num_review_comments,
                num_additions, num_deletions, labels, is_draft, owner_handle
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pr.get('id'),
            pr.get('repo_name'),
            pr.get('number'),
            pr.get('title'),
            pr.get('body'),
            pr.get('state'),
            int(pr.get('merged', False)),
            pr.get('merged_by'),
            pr.get('user'),
            pr.get('created_at'),
            pr.get('updated_at'),
            pr.get('closed_at'),
            pr.get('merged_at'),
            pr.get('time_to_merge_hours'),
            pr.get('time_to_close_hours'),
            pr.get('num_commits', 0),
            pr.get('num_files_changed', 0),
            pr.get('num_comments', 0),
            pr.get('num_review_comments', 0),
            pr.get('num_additions', 0),
            pr.get('num_deletions', 0),
            labels,
            int(pr.get('is_draft', False)),
            handle
        ))

    conn.commit()
    conn.close()


def save_issues(handle: str, issues: List[Dict[str, Any]]) -> None:
    """Save issues to database."""
    conn = get_connection()
    cursor = conn.cursor()

    for issue in issues:
        labels = json.dumps(issue.get('labels', []))
        cursor.execute("""
            INSERT OR REPLACE INTO issues (
                issue_id, repo_name, number, title, body, state,
                author, created_at, updated_at, closed_at,
                comments, labels, is_pull_request, owner_handle
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            issue.get('id'),
            issue.get('repo_name'),
            issue.get('number'),
            issue.get('title'),
            issue.get('body'),
            issue.get('state'),
            issue.get('user'),
            issue.get('created_at'),
            issue.get('updated_at'),
            issue.get('closed_at'),
            issue.get('comments', 0),
            labels,
            int(issue.get('is_pull_request', False)),
            handle
        ))

    conn.commit()
    conn.close()


def save_languages(handle: str, lang_bytes: Dict[str, int], repo_name: str = None) -> None:
    """Save language data to database."""
    conn = get_connection()
    cursor = conn.cursor()

    if repo_name:
        # Single repo language data
        cursor.execute("""
            INSERT OR REPLACE INTO languages (repo_name, languages, total_bytes, owner_handle)
            VALUES (?, ?, ?, ?)
        """, (repo_name, json.dumps(lang_bytes), sum(lang_bytes.values()), handle))
    else:
        # Aggregate language data (just overwrite with same key)
        cursor.execute("""
            INSERT OR REPLACE INTO languages (repo_name, languages, total_bytes, owner_handle)
            VALUES (?, ?, ?, ?)
        """, (f"{handle}_aggregate", json.dumps(lang_bytes), sum(lang_bytes.values()), handle))

    conn.commit()
    conn.close()


def save_orgs(handle: str, orgs: List[Dict[str, Any]]) -> None:
    """Save organizations to database."""
    conn = get_connection()
    cursor = conn.cursor()

    for org in orgs:
        cursor.execute("""
            INSERT OR REPLACE INTO organizations (
                login, name, description, public_repos, followers, following, owner_handle
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            org.get('login'),
            org.get('name'),
            org.get('description'),
            org.get('public_repos', 0),
            org.get('followers', 0),
            org.get('following', 0),
            handle
        ))

    conn.commit()
    conn.close()


def get_user_stats(handle: str) -> Dict[str, Any]:
    """Get aggregated stats for a user from database."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get commit stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_commits,
            SUM(additions) as total_additions,
            SUM(deletions) as total_deletions,
            AVG(additions) as avg_additions,
            AVG(deletions) as avg_deletions,
            commit_type,
            COUNT(*) as type_count
        FROM commits
        WHERE owner_handle = ?
        GROUP BY commit_type
    """, (handle,))
    commit_types = [dict(row) for row in cursor.fetchall()]

    # Get language stats
    cursor.execute("""
        SELECT languages FROM languages WHERE owner_handle = ?
    """, (handle,))
    lang_rows = cursor.fetchall()
    all_langs = {}
    for row in lang_rows:
        langs = json.loads(row['languages'])
        for lang, bytes_count in langs.items():
            all_langs[lang] = all_langs.get(lang, 0) + bytes_count

    # Get PR stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_prs,
            SUM(merged) as merged_prs,
            AVG(time_to_merge_hours) as avg_time_to_merge
        FROM pull_requests
        WHERE owner_handle = ?
    """, (handle,))
    pr_stats = dict(cursor.fetchone())

    conn.close()

    return {
        'commit_types': commit_types,
        'languages': all_langs,
        'pr_stats': pr_stats
    }


def print_db_stats() -> None:
    """Print database statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 50)
    print("DATABASE STATS")
    print("=" * 50)

    # User count
    cursor.execute("SELECT COUNT(*) as count FROM users")
    print(f"Users: {cursor.fetchone()['count']}")

    # Commit count
    cursor.execute("SELECT COUNT(*) as count FROM commits")
    print(f"Commits: {cursor.fetchone()['count']}")

    # Files count
    cursor.execute("SELECT COUNT(*) as count FROM commit_files")
    print(f"Code files tracked: {cursor.fetchone()['count']}")

    # PR count
    cursor.execute("SELECT COUNT(*) as count FROM pull_requests")
    print(f"Pull Requests: {cursor.fetchone()['count']}")

    # Repo count
    cursor.execute("SELECT COUNT(*) as count FROM repositories")
    print(f"Repositories: {cursor.fetchone()['count']}")

    print(f"\nDatabase location: {get_db_path()}")
    print("=" * 50)

    conn.close()


# Initialize database on module load
init_database()
