"""
Evidence Builder — Builds skill evidence chains from harvester/DB data.
============================================================
Produces GitHub-backed evidence for every skill claim:
- Language search URLs
- Repo links
- Commit URLs showing skill usage
- Adjacency reasoning
"""

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EvidenceBuilder:
    """
    Builds rich evidence chains from GitHub data.
    Uses DB cache or live harvester data to link skills to real artifacts.
    """

    def __init__(self):
        self._lang_map = self._build_lang_map()

    # ── Language → file extensions mapping ─────────────────────────────────────

    def _build_lang_map(self) -> Dict[str, list]:
        return {
            "python": [".py", ".pyx", ".pyi", ".pyw"],
            "javascript": [".js", ".jsx", ".mjs", ".cjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "kotlin": [".kt", ".kts"],
            "swift": [".swift"],
            "go": [".go"],
            "rust": [".rs"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh"],
            "csharp": [".cs"],
            "ruby": [".rb"],
            "php": [".php"],
            "scala": [".scala"],
            "html": [".html", ".htm"],
            "css": [".css", ".scss", ".sass"],
            "vue": [".vue"],
            "shell": [".sh", ".bash", ".zsh"],
            "sql": [".sql"],
            "terraform": [".tf"],
            "dockerfile": ["dockerfile", ".dockerfile"],
        }

    def _get_extensions(self, lang: str) -> list:
        lang = lang.lower()
        for key, exts in self._lang_map.items():
            if lang == key or lang in key:
                return exts
        return [f".{lang}"]

    # ── Core evidence building ────────────────────────────────────────────────

    def build_evidence_chains(
        self,
        github_handle: str,
        raw_data: Dict[str, Any],
        skill_intel: Dict[str, Any],
        scoring_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Build evidence chains from harvester data.
        Each chain = one skill + GitHub links + reasoning.
        """
        chains = []
        repos = raw_data.get("repos", [])
        commits = raw_data.get("commits", [])
        commit_files = raw_data.get("commit_files", [])
        lang_bytes = raw_data.get("lang_bytes", {})
        aggregates = raw_data.get("aggregates", {})

        # Build lookup maps
        lang_to_repos = self._build_lang_to_repos_map(repos)
        sha_to_commit = {c.get("sha", ""): c for c in commits}
        sha_to_repo = {c.get("sha", ""): c.get("repo_name", "") for c in commits}
        sha_to_files: Dict[str, list] = {}
        for cf in commit_files:
            sha = cf.get("commit_sha", "")
            fname = cf.get("filename", "")
            if sha and fname:
                sha_to_files.setdefault(sha, []).append(fname)

        # Collect languages to cover
        languages = self._collect_languages(lang_bytes, repos, skill_intel)

        # Get JD skills for ranking
        jd_skills = scoring_result.get("jd_skills_extracted", {})
        must_have = {s.lower() for s in jd_skills.get("must_have", [])}
        nice_to_have = {s.lower() for s in jd_skills.get("nice_to_have", [])}
        matched_skills = self._get_matched_set(scoring_result)

        # Score and rank languages
        lang_scores = self._score_languages(
            languages, lang_bytes, repos, must_have, nice_to_have, matched_skills
        )

        for lang_lower, info in sorted(lang_scores.items(), key=lambda x: x[1]["score"], reverse=True)[:10]:
            chain = self._build_lang_chain(
                github_handle, lang_lower, info, lang_to_repos,
                sha_to_files, sha_to_commit, sha_to_repo,
            )
            if chain:
                chains.append(chain)

        # Adjacency chains (e.g., Python → likely knows Flask)
        adj_chains = self._build_adjacency_chains(
            github_handle, repos, matched_skills, must_have
        )
        chains.extend(adj_chains)

        # Gap chains (missing skills)
        missing = scoring_result.get("missing_skills", [])
        for m in (missing or [])[:5]:
            skill = m.get("skill", "") if isinstance(m, dict) else str(m)
            learning = m.get("learning_time", "?") if isinstance(m, dict) else "?"
            chains.append({
                "skill": skill.title(),
                "type": "missing",
                "confidence": 0.0,
                "evidence_summary": f"No GitHub evidence for '{skill}'",
                "reasoning": f"Ramp-up estimate: {learning}",
                "github_links": [],
                "commits": [],
            })

        return chains

    def _build_lang_to_repos_map(self, repos: list) -> Dict[str, list]:
        m = {}
        for r in repos:
            lang = (r.get("language") or "").lower()
            if lang:
                m.setdefault(lang, []).append(r)
        return m

    def _collect_languages(
        self,
        lang_bytes: Dict,
        repos: list,
        skill_intel: Dict[str, Any],
    ) -> Dict[str, float]:
        """Collect all languages with their byte percentages."""
        languages = {}

        # From lang_bytes (most reliable)
        total_bytes = sum(lang_bytes.values()) or 1
        for lang, bytes_count in lang_bytes.items():
            languages[lang.lower()] = bytes_count / total_bytes

        # From repo languages
        lang_to_repos = self._build_lang_to_repos_map(repos)
        for lang, repo_list in lang_to_repos.items():
            if lang not in languages:
                languages[lang] = len(repo_list) / max(len(repos), 1)

        return languages

    def _score_languages(
        self,
        languages: Dict[str, float],
        lang_bytes: Dict,
        repos: list,
        must_have: Set[str],
        nice_to_have: Set[str],
        matched_skills: Set[str],
    ) -> Dict[str, Dict]:
        """Score each language for ranking (repos > bytes > JD relevance)."""
        lang_to_repos = self._build_lang_to_repos_map(repos)
        scores = {}

        for lang_lower, byte_pct in languages.items():
            repo_list = lang_to_repos.get(lang_lower, [])
            repo_count = len(repo_list)
            byte_pct_val = byte_pct * 100  # Convert to %

            # JD relevance boost (only proper matches, not substring matches like "c" in "machine learning")
            jd_boost = 0
            for m in must_have:
                # Exact match OR proper substring match (lang is part of multi-word skill, min 4 chars)
                if lang_lower == m or (len(lang_lower) >= 4 and lang_lower in m):
                    jd_boost = 50
                    break
            if jd_boost == 0:
                for n in nice_to_have:
                    if lang_lower == n or (len(lang_lower) >= 4 and lang_lower in n):
                        jd_boost = 20
                        break
            if jd_boost == 0 and lang_lower in matched_skills:
                jd_boost = 30

            # Score: repos are most important, then JD boost
            score = (repo_count * 15) + min(byte_pct_val, 100) + jd_boost
            scores[lang_lower] = {
                "repo_count": repo_count,
                "byte_pct": byte_pct_val,
                "jd_boost": jd_boost,
                "score": score,
                "repos": repo_list,
            }

        return scores

    def _build_lang_chain(
        self,
        github_handle: str,
        lang_lower: str,
        info: Dict,
        lang_to_repos: Dict,
        sha_to_files: Dict,
        sha_to_commit: Dict,
        sha_to_repo: Dict,
    ) -> Optional[Dict]:
        """Build a single evidence chain for one language."""
        repo_count = info["repo_count"]
        matching_repos = info["repos"]
        is_jd = info["jd_boost"] > 0

        github_links = []

        # Link 1: GitHub language search
        lang_search_url = (
            f"https://github.com/{github_handle}?tab=repositories&q=&type=&language={lang_lower.replace(' ', '+')}&sort=updated"
        )
        github_links.append({
            "url": lang_search_url,
            "label": f"Search {lang_lower} repos",
            "type": "language_search",
            "desc": f"Find all {lang_lower} code across @{github_handle}'s repositories",
        })

        # Links 2+: Individual repos
        for repo in matching_repos[:4]:
            repo_full = repo.get("full_name") or repo.get("name", "")
            repo_short = repo.get("name", repo_full)
            stars = repo.get("stars", 0) or 0
            desc = (repo.get("description") or "")[:100]
            if repo_full:
                github_links.append({
                    "url": f"https://github.com/{repo_full}",
                    "label": repo_short,
                    "stars": stars,
                    "type": "repo",
                    "desc": desc,
                })

        # Find relevant commits (files touched)
        relevant_commits = []
        seen_shas = set()
        exts = self._get_extensions(lang_lower)

        for sha, files in sha_to_files.items():
            for fname in files:
                fname_lower = fname.lower()
                if any(ext in fname_lower for ext in exts):
                    if sha not in seen_shas:
                        seen_shas.add(sha)
                        commit = sha_to_commit.get(sha, {})
                        msg = (commit.get("message") or "")[:80]
                        repo_name = sha_to_repo.get(sha, "")
                        full_sha = sha[:7] if sha else ""
                        relevant_commits.append({
                            "url": f"https://github.com/{repo_name}/commit/{full_sha}" if repo_name and full_sha else "",
                            "sha": full_sha,
                            "message": msg,
                            "repo": repo_name,
                            "files": [f for f in files if any(ext in f.lower() for ext in exts)][:3],
                        })
                    break

        # Confidence based on repo count + JD relevance
        confidence = min(0.99, (repo_count * 0.15) + (0.5 if is_jd else 0) + 0.1)

        # Evidence summary
        parts = []
        if repo_count > 0:
            parts.append(f"{repo_count} repo(s)")
        if info["byte_pct"] > 1:
            parts.append(f"{info['byte_pct']:.0f}% code")
        if relevant_commits:
            parts.append(f"{len(relevant_commits)} commit(s)")

        return {
            "skill": lang_lower.title(),
            "type": "language",
            "confidence": round(confidence, 2),
            "evidence_summary": f"{lang_lower.title()} — {'; '.join(parts) if parts else 'Evidence found'}",
            "github_links": github_links,
            "commits": relevant_commits[:5],
            "num_matching_repos": repo_count,
            "is_jd_relevant": is_jd,
        }

    def _build_adjacency_chains(
        self,
        github_handle: str,
        repos: list,
        matched_skills: Set[str],
        must_have: Set[str],
    ) -> List[Dict]:
        """Build adjacency chains (knows X → likely knows Y)."""
        adjacency_map = {
            "python": ["Django", "Flask", "FastAPI", "Pandas", "NumPy"],
            "javascript": ["TypeScript", "React", "Node.js", "Vue"],
            "java": ["Spring", "Spring Boot", "Kotlin"],
            "typescript": ["React", "Vue", "Node.js"],
            "kubernetes": ["Docker", "Helm", "Terraform"],
            "aws": ["EC2", "S3", "Lambda", "ECS", "EKS"],
        }

        chains = []
        seen_adj = set()

        for skill in matched_skills:
            adj_list = adjacency_map.get(skill.lower(), [])
            for adj in adj_list[:2]:
                adj_lower = adj.lower()
                if adj_lower in seen_adj:
                    continue
                for repo in repos:
                    desc = (repo.get("description") or "").lower()
                    topics = " ".join(repo.get("topics", []) or []).lower()
                    if adj_lower in desc or adj_lower in topics:
                        repo_full = repo.get("full_name") or repo.get("name", "")
                        repo_short = repo.get("name", repo_full)
                        seen_adj.add(adj_lower)
                        chains.append({
                            "skill": adj,
                            "type": "adjacent",
                            "confidence": 0.60,
                            "evidence_summary": f"Adjacent to {skill.title()}",
                            "reasoning": f"@{github_handle} works with {skill.title()}, so likely knows {adj}",
                            "github_links": [{
                                "url": f"https://github.com/{repo_full}" if repo_full else "",
                                "label": repo_short,
                                "type": "repo",
                                "desc": f"'{adj}' found in {skill.title()} project: {desc[:80]}",
                            }],
                            "commits": [],
                        })
                        break

        return chains

    def _get_matched_set(self, scoring_result: Dict) -> Set[str]:
        matched = scoring_result.get("matched_skills", [])
        return {m.get("skill", "").lower() if isinstance(m, dict) else str(m).lower() for m in matched}
