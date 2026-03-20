"""
LLM Integration for Intelligent Analysis
=======================================
Uses OpenAI-compatible API to enhance commit analysis with
contextual understanding and personalized insights.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from modules.commit_analyzer.types import DeveloperProfile, CommitCitation

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for OpenAI-compatible API to power intelligent commit analysis.

    Features:
    - Intelligent commit message analysis
    - Personalized developer insights
    - Role-specific recommendations
    - Gap analysis vs job requirements
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = "https://api.codemax.pro",
        model: str = "claude-opus-4-6",
        timeout: float = 60.0,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: API key (defaults to GITHUB_TOKEN or env)
            api_base: API base URL
            model: Model name
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("GITHUB_TOKEN") or os.environ.get("LLM_API_KEY")
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

        if not self.api_key:
            logger.warning("No API key provided - LLM features will be disabled")

    def is_available(self) -> bool:
        """Check if LLM is available."""
        return bool(self.api_key)

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[str]:
        """
        Make a request to the Anthropic Messages API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt (becomes first user message)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text or None on failure
        """
        if not self.is_available():
            return None

        # Build Anthropic format messages
        anthropic_messages = []

        # System prompt becomes first user message if provided
        if system:
            anthropic_messages.append({"role": "user", "content": f"<system>\n{system}\n</system>"})

        # Convert messages
        for msg in messages:
            role = msg.get("role", "user")
            # Anthropic uses 'user' and 'assistant', not 'system'
            if role == "system":
                role = "user"
            anthropic_messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
        }

        # Add temperature if not default
        if temperature != 0.7:
            payload["temperature"] = temperature

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.api_base}/v1/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Handle Anthropic response format
                # Format: {"content": [{"type": "text", "text": "..."}]}
                content = data.get("content", [])
                if content and isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            return item.get("text", "")

                return ""

        except httpx.HTTPError as e:
            logger.warning(f"LLM API request failed: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.warning(f"LLM API response parsing failed: {e}")
            return None
            return None

    def analyze_commit_context(
        self,
        commits: List[Dict[str, Any]],
        max_commits: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze commit context to understand patterns and themes.

        Args:
            commits: List of commit dicts
            max_commits: Maximum commits to include in analysis

        Returns:
            Dict with themes, insights, and patterns
        """
        if not self.is_available():
            return None

        # Format commits for analysis
        commit_summaries = []
        for commit in commits[:max_commits]:
            summary = {
                "sha": commit.get("sha", "")[:7],
                "type": commit.get("commit_type", "other"),
                "message": commit.get("message", "")[:100],
                "files": len(commit.get("files", [])),
                "additions": sum(f.get("additions", 0) for f in commit.get("files", [])),
                "deletions": sum(f.get("deletions", 0) for f in commit.get("files", [])),
            }
            commit_summaries.append(summary)

        messages = [
            {
                "role": "user",
                "content": f"""Analyze these commits and identify:

1. **Themes**: What are the main patterns/types of work?
2. **Complexity indicators**: Are there signs of complex architectural work?
3. **Collaboration style**: How do they work with others (PRs, reviews)?
4. **Quality signals**: Signs of testing, documentation, refactoring?

Commits:
{json.dumps(commit_summaries, indent=2)}

Return a JSON object with: themes (list), complexity_assessment (string), collaboration_style (string), quality_signals (list), overall_impression (string)"""
            }
        ]

        system = """You are a senior software engineer analyzing GitHub commit history.
Provide insights that help understand the developer's work patterns and skills.
Always return valid JSON."""

        result = self._make_request(messages, system=system, max_tokens=1500)

        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw_insights": result}

        return None

    def generate_personalized_insights(
        self,
        signals: Dict[str, float],
        profile: DeveloperProfile,
        role_type: str = "generalist"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate personalized insights based on signals and target role.

        Args:
            signals: Extracted signals
            profile: Developer profile
            role_type: Target role type

        Returns:
            Personalized insights and recommendations
        """
        if not self.is_available():
            return None

        messages = [
            {
                "role": "user",
                "content": f"""As a technical recruiter, analyze this developer's profile for a {role_type} role:

**Profile**:
- Archetype: {profile.archetype}
- Tagline: {profile.tagline}
- Confidence: {profile.confidence:.0%}

**Top Signals**:
{json.dumps(dict(list(signals.items())[:20]), indent=2)}

Provide:
1. **Strengths**: Top 3-5 strengths for this role
2. **Growth Areas**: 2-3 areas to develop
3. **Interview Questions**: 3 specific questions to ask
4. **Red Flags**: Any concerns to investigate
5. **Fit Assessment**: How well they match {role_type} role (1-10)

Return JSON with: strengths (list), growth_areas (list), interview_questions (list), red_flags (list), fit_score (float), fit_reasoning (string)"""
            }
        ]

        system = """You are an expert technical recruiter specializing in software engineering roles.
Provide honest, actionable insights about candidate profiles.
Always return valid JSON."""

        result = self._make_request(messages, system=system, max_tokens=2000)

        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw_insights": result}

        return None

    def analyze_jd_fit(
        self,
        signals: Dict[str, float],
        profile: DeveloperProfile,
        jd_requirements: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze how well developer matches job requirements.

        Args:
            signals: Developer signals
            profile: Developer profile
            jd_requirements: Parsed JD requirements

        Returns:
            Fit analysis with scores per requirement
        """
        if not self.is_available():
            return None

        # Convert JobRequirement objects to dicts if needed
        requirements_list = []
        for req in jd_requirements[:10]:
            if hasattr(req, '__dict__'):
                requirements_list.append({
                    'skill': req.skill,
                    'category': req.category,
                    'importance': req.importance
                })
            else:
                requirements_list.append(req)

        messages = [
            {
                "role": "user",
                "content": f"""Analyze this candidate's fit for the job requirements:

**Candidate Profile**:
- Archetype: {profile.archetype} ({profile.confidence:.0%} confidence)
- Tagline: {profile.tagline}

**Key Signals**:
{json.dumps(dict(list(signals.items())[:25]), indent=2)}

**Job Requirements**:
{json.dumps(requirements_list, indent=2)}

For each requirement, assess:
1. How well the candidate matches (0-100%)
2. Evidence from their GitHub profile
3. Risk level (low/medium/high)

Return JSON:
{{
  "overall_fit_score": float,
  "requirement_matches": [
    {{"requirement": str, "match_score": float, "evidence": str, "risk": str}}
  ],
  "strongest_match": str,
  "weakest_match": str,
  "recommendation": str
}}"""
            }
        ]

        system = """You are a technical screening assistant.
Assess candidate-job fit objectively based on available evidence.
Always return valid JSON."""

        result = self._make_request(messages, system=system, max_tokens=2000)

        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw_insights": result}

        return None

    def generate_developer_summary(
        self,
        signals: Dict[str, float],
        profile: DeveloperProfile,
        citations: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate a natural language summary of the developer.

        Args:
            signals: Developer signals
            profile: Developer profile
            citations: Notable achievements
            stats: Basic statistics

        Returns:
            Natural language summary
        """
        if not self.is_available():
            return None

        messages = [
            {
                "role": "user",
                "content": f"""Write a concise, professional summary of this software developer:

**Profile**: {profile.archetype}
**Tagline**: {profile.tagline}

**Statistics**:
- Commits analyzed: {stats.get('commits_analyzed', 0)}
- Repositories: {stats.get('repos_analyzed', 0)}
- Date range: {stats.get('date_range_days', 0)} days

**Top Achievements**:
{json.dumps([c.get('title') for c in citations[:5]], indent=2)}

**Key Metrics**:
- Consistency: {signals.get('consistency_score', 0):.0f}%
- Code Hygiene: {signals.get('overall_hygiene_score', 0):.0f}%
- Problem Solving: {signals.get('problem_solving_score', 0):.0f}%
- Architectural Complexity: {signals.get('architectural_complexity_score', 0):.0f}%

Write a 3-4 sentence professional summary suitable for a recruiter or hiring manager.
Focus on what makes this developer unique and valuable."""
            }
        ]

        system = """You are a professional technical writer.
Write clear, concise summaries that highlight developer strengths.
Do not be overly promotional - be honest and specific."""

        result = self._make_request(
            messages,
            system=system,
            temperature=0.7,
            max_tokens=500
        )

        return result

    def extract_citation_evidence(
        self,
        commit_shas: List[str],
        citation_type: str
    ) -> Optional[List[str]]:
        """
        Extract specific evidence for a citation type.

        Args:
            commit_shas: List of commit SHAs that qualify for citation
            citation_type: Type of citation (e.g., "architectural_master")

        Returns:
            List of evidence descriptions
        """
        if not self.is_available() or not commit_shas:
            return None

        messages = [
            {
                "role": "user",
                "content": f"""For the citation type "{citation_type}", the following commits were identified.

Commit SHAs (first 7 chars): {commit_shas[:10]}

Describe in 2-3 bullet points what evidence these commits provide
for this citation. Focus on specific, observable patterns.
Example: "The developer consistently touches 5+ modules per commit,
indicating system-level thinking." """
            }
        ]

        system = """You are a code analyst. Describe evidence patterns briefly and specifically."""

        result = self._make_request(messages, system=system, max_tokens=300)

        if result:
            return [line.strip() for line in result.split("\n") if line.strip()]

        return None


# =============================================================================
# Configuration
# =============================================================================

def get_llm_client() -> LLMClient:
    """
    Get configured LLM client from environment.

    Returns:
        LLMClient instance (may be unavailable if no API key)
    """
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GITHUB_TOKEN")
    api_base = os.environ.get("LLM_API_BASE", "https://api.codemax.pro")
    model = os.environ.get("LLM_MODEL", "claude-opus-4-6")

    return LLMClient(
        api_key=api_key,
        api_base=api_base,
        model=model,
    )
