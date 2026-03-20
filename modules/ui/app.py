"""
EightFold Talent Intelligence - Streamlit UI
==========================================
Interactive UI for analyzing GitHub profiles against job descriptions.

Features:
- GitHub profile analysis with skill intelligence
- JD parsing with LLM-powered skill extraction
- Evidence-backed candidate scoring
- Beautiful visualization of results
"""

import streamlit as st
import json
import os
import time
from pathlib import Path
from typing import Optional

# Page config
st.set_page_config(
    page_title="EightFold - Talent Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 1rem;
    }
    .skill-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .match-high { color: #22c55e; font-weight: bold; }
    .match-medium { color: #eab308; font-weight: bold; }
    .match-low { color: #ef4444; font-weight: bold; }
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap-gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


def load_json_safe(path: Path) -> Optional[dict]:
    """Load JSON file safely."""
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_data_dir() -> Path:
    """Get data directory."""
    return Path(__file__).parent.parent.parent / "data"


def check_candidate_exists(handle: str) -> bool:
    """Check if candidate data exists."""
    data_dir = get_data_dir()
    raw_file = data_dir / f"{handle}_raw.json"
    return raw_file.exists()


def get_candidate_results(handle: str) -> dict:
    """Get all analysis results for a candidate."""
    data_dir = get_data_dir()

    results = {
        "raw": load_json_safe(data_dir / f"{handle}_raw.json"),
        "skill_intelligence": load_json_safe(data_dir / f"{handle}_skill_intelligence.json"),
        "explainable": load_json_safe(data_dir / f"{handle}_explainable.json"),
        "jd_match": {},
    }

    # Load JD match files
    for f in data_dir.glob(f"{handle}_jd_match_*.json"):
        key = f.stem.replace(f"{handle}_jd_match_", "")
        results["jd_match"][key] = load_json_safe(f)

    return results


def extract_jd_skills(jd_text: str) -> list[str]:
    """Extract skills from JD using LLM or fallback."""
    try:
        from modules.jd_matcher.llm_parser import extract_skills_with_llm
        skills = extract_skills_with_llm(jd_text)
        if skills:
            return skills
    except Exception:
        pass

    # Fallback to basic extraction
    try:
        from modules.jd_matcher.jd_parser import extract_skills_basic
        return extract_skills_basic(jd_text)
    except Exception:
        return []


def run_analysis(handle: str, jd_file: Optional[Path] = None) -> dict:
    """Run full analysis pipeline."""
    data_dir = get_data_dir()

    # Import analysis modules
    from modules.storage import load_json
    from modules.skill_analyzer import SkillAnalyzer
    from modules.explainability import explain_skill_intelligence
    from modules.jd_matcher import match_jd, parse_job_description

    results = {
        "status": "running",
        "harvested": False,
        "skill_result": None,
        "explainable": None,
        "jd_match": None,
        "error": None
    }

    # Check if already harvested
    raw_file = data_dir / f"{handle}_raw.json"
    if not raw_file.exists():
        # Run harvester
        try:
            from modules.harvester import harvest
            with st.spinner(f"Harvesting data for @{handle}..."):
                raw_data = harvest(handle)
                results["harvested"] = True
        except Exception as e:
            results["error"] = f"Harvest failed: {str(e)}"
            return results
    else:
        with st.spinner("Loading cached data..."):
            raw_data = load_json(raw_file)

    results["raw"] = raw_data

    # Run skill analysis
    try:
        with st.spinner("Analyzing skills..."):
            analyzer = SkillAnalyzer()
            repos = raw_data.get("repos", []) or []
            commits = raw_data.get("commits", []) or []
            issues = raw_data.get("issues", []) or []
            prs = raw_data.get("pull_requests", []) or []
            branches = raw_data.get("branches", {}) or {}
            releases = raw_data.get("releases", {}) or {}
            aggregates = raw_data.get("aggregates", {}) or {}

            skill_raw_data = {
                "repos": repos,
                "lang_bytes": raw_data.get("lang_bytes", {}),
                "commits": commits,
                "issues": issues,
                "pull_requests": prs,
                "branches": branches,
                "releases": releases,
                "aggregates": aggregates,
            }

            skill_result = analyzer.analyze(skill_raw_data)
            results["skill_result"] = skill_result

            # Generate explainable result
            explainable = explain_skill_intelligence(raw_data, skill_result)
            results["explainable"] = explainable

    except Exception as e:
        results["error"] = f"Skill analysis failed: {str(e)}"
        return results

    # Run JD matching if JD provided
    if jd_file and jd_file.exists():
        try:
            with st.spinner("Matching against job description..."):
                with open(jd_file, 'r', encoding='utf-8') as f:
                    jd_text = f.read()

                jd_match = match_jd(handle, raw_data, skill_result, jd_text)
                results["jd_match"] = jd_match

        except Exception as e:
            results["error"] = f"JD matching failed: {str(e)}"

    results["status"] = "complete"
    return results


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_header():
    """Render main header."""
    st.markdown('<p class="main-header">🎯 EightFold Talent Intelligence</p>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Candidate Assessment with Evidence-Backed Insights")

    # Sidebar info
    with st.sidebar:
        st.markdown("### About")
        st.markdown("""
        **EightFold** analyzes GitHub profiles to provide:

        - Skill Intelligence
        - Evidence-Backed Assessments
        - JD Match Scoring
        - Problem-Solving Traces
        """)

        st.markdown("---")
        st.markdown("### How It Works")
        st.markdown("""
        1. Enter a GitHub handle
        2. Upload a job description (optional)
        3. Click **Analyze**
        4. View detailed results with evidence
        """)


def render_input_section():
    """Render input form."""
    col1, col2 = st.columns([2, 1])

    with col1:
        handle = st.text_input(
            "GitHub Handle",
            placeholder="e.g., gvanrossum, torvalds, facebook",
            help="Enter the GitHub username to analyze"
        )

    with col2:
        st.markdown("&nbsp;")  # Spacing
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

    # JD upload
    jd_file = st.file_uploader(
        "📄 Job Description (optional)",
        type=['txt', 'md'],
        help="Upload a job description for matching"
    )

    return handle, analyze_button, jd_file


def render_candidate_summary(raw_data: dict, skill_data: dict):
    """Render candidate summary card."""
    repos = raw_data.get("repos", []) or []
    commits = raw_data.get("commits", []) or []

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Repositories", len(repos))

    with col2:
        st.metric("Commits Analyzed", len(commits))

    with col3:
        if skill_data:
            level = skill_data.get("skill_profile", {}).get("skill_level", "Unknown")
            confidence = skill_data.get("skill_profile", {}).get("skill_level_confidence", 0)
            st.metric("Skill Level", f"{level} ({confidence:.0%})")
        else:
            st.metric("Skill Level", "N/A")

    with col4:
        if skill_data:
            domains = skill_data.get("skill_profile", {}).get("primary_domains", [])
            st.metric("Primary Domain", domains[0] if domains else "N/A")
        else:
            st.metric("Primary Domain", "N/A")


def render_skills_tab(explainable_data: dict):
    """Render skills tab."""
    skill_assessment = explainable_data.get("skill_assessment", {})

    if not skill_assessment:
        st.info("No skill assessment available")
        return

    # Sort skills by confidence
    sorted_skills = sorted(
        skill_assessment.items(),
        key=lambda x: x[1].get("confidence", 0),
        reverse=True
    )

    # Create skill cards
    for skill_name, skill_info in sorted_skills[:10]:
        confidence = skill_info.get("confidence", 0)
        level = skill_info.get("level", "")
        evidence = skill_info.get("evidence", {})
        reasoning = skill_info.get("reasoning", [])
        gaps = skill_info.get("gaps", [])

        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"#### {skill_name}")
                st.markdown(f"**Level:** {level} | **Confidence:** {confidence:.0%}")

                # Show reasoning
                if reasoning:
                    st.markdown("**Why we believe this:**")
                    for r in reasoning[:2]:
                        st.markdown(f"- {r}")

                # Show key evidence
                if evidence:
                    st.markdown("**Evidence:**")
                    for src, finding in list(evidence.items())[:2]:
                        st.markdown(f"- *{src}:* {finding}")

            with col2:
                # Confidence meter
                st.markdown("###")
                st.progress(confidence)
                st.caption(f"{confidence:.0%} confidence")

                # Gaps
                if gaps:
                    with st.expander("⚠️ Gaps"):
                        for gap in gaps[:3]:
                            st.markdown(f"- {gap}")

            st.markdown("---")


def render_jd_match_tab(jd_data: dict):
    """Render JD match tab."""
    if not jd_data:
        st.info("No JD matching results available")
        return

    overall_score = jd_data.get("overall_match_score", 0)
    recommendation = jd_data.get("recommendation", "")

    # Score display
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Match Score")
        st.markdown(f"## {overall_score:.0f}")
        st.markdown(f"**{recommendation.replace('_', ' ').title()}**")

    with col2:
        # Score bar
        st.markdown("###")
        st.progress(overall_score / 100)

        # Recommendation text
        summary = jd_data.get("summary", "")
        st.markdown(f"_{summary}_")

    st.markdown("---")

    # Matched skills
    mandatory = jd_data.get("mandatory_skills", [])
    matched = [s for s in mandatory if s.get("is_match")]
    missing = [s for s in mandatory if not s.get("is_match")]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### ✅ Matched ({len(matched)}/{len(mandatory)})")

        for skill in matched[:8]:
            skill_name = skill.get("skill", "")
            confidence = skill.get("confidence", 0)
            evidence = skill.get("evidence", [])

            with st.expander(f"**{skill_name}** ({confidence:.0%})"):
                if evidence:
                    for e in evidence[:3]:
                        st.markdown(f"- {e.get('description', '')}")
                        st.markdown(f"  [View →]({e.get('url', '')})")

    with col2:
        st.markdown(f"### ❌ Missing ({len(missing)}/{len(mandatory)})")

        for skill in missing[:8]:
            skill_name = skill.get("skill", "")
            reason = skill.get("missing_reason", "No evidence found")

            with st.expander(f"**{skill_name}**"):
                st.markdown(f"_{reason}_")

    # Category breakdown
    category_scores = jd_data.get("category_scores", {})
    if category_scores:
        st.markdown("### Category Coverage")

        for cat, score in sorted(category_scores.items(), key=lambda x: -x[1]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{cat.title()}**")
                st.progress(score / 100)
            with col2:
                st.markdown(f"{score:.0f}%")

    # Strengths and Gaps
    strengths = jd_data.get("strengths", [])
    critical_gaps = jd_data.get("critical_gaps", [])

    col1, col2 = st.columns(2)

    with col1:
        if strengths:
            st.markdown("### 💪 Strengths")
            for s in strengths[:5]:
                st.markdown(f"- {s}")

    with col2:
        if critical_gaps:
            st.markdown("### ⚠️ Critical Gaps")
            for g in critical_gaps[:5]:
                st.markdown(f"- {g}")


def render_projects_tab(explainable_data: dict):
    """Render projects tab."""
    projects = explainable_data.get("project_evidence", [])

    if not projects:
        st.info("No project evidence available")
        return

    for proj in projects[:10]:
        name = proj.get("name", "")
        full_name = proj.get("full_name", "")
        stars = proj.get("stars", 0)
        impact = proj.get("impact", "")
        skills_demo = proj.get("skills_demonstrated", [])
        why_it_matters = proj.get("why_it_matters", "")

        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### {name}")
                st.markdown(f"[GitHub →](https://github.com/{full_name})")
                st.markdown(f"_{why_it_matters}_")

            with col2:
                st.metric("Stars", f"⭐ {stars:,}" if stars > 0 else "Private")

            with col3:
                if skills_demo:
                    st.markdown("**Skills:**")
                    for skill in skills_demo[:3]:
                        st.markdown(f"- {skill}")

            st.markdown("---")


def render_raw_data_tab(raw_data: dict):
    """Render raw data tab (for debugging)."""
    st.json(raw_data, expanded=False)


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    render_header()

    # Input section
    handle, analyze_button, jd_file = render_input_section()

    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'handle' not in st.session_state:
        st.session_state.handle = None

    # Run analysis
    if analyze_button and handle:
        st.session_state.handle = handle

        with st.spinner(f"Analyzing @{handle}..."):
            results = run_analysis(handle, jd_file)

            if results.get("error"):
                st.error(results["error"])
            else:
                st.session_state.results = results

                if results.get("harvested"):
                    st.success(f"✅ Data harvested for @{handle}")

    # Show results
    if st.session_state.results and st.session_state.handle:
        results = st.session_state.results

        if results["status"] == "complete":
            st.markdown("---")
            st.markdown("## 📊 Analysis Results")

            # Candidate summary
            if results.get("raw"):
                render_candidate_summary(results["raw"], results.get("skill_result", {}))

            # Tabs for different views
            tab_names = ["Skills Assessment", "JD Match", "Projects", "Raw Data"]
            tabs = st.tabs(tab_names)

            with tabs[0]:
                if results.get("explainable"):
                    # Convert to dict for display
                    explainable_dict = {
                        "skill_assessment": {},
                        "project_evidence": [],
                    }

                    # Convert explainable object to dict
                    exp = results["explainable"]
                    if hasattr(exp, 'skill_assessment'):
                        for name, skill in exp.skill_assessment.items():
                            explainable_dict["skill_assessment"][name] = {
                                "confidence": skill.confidence,
                                "level": skill.level,
                                "evidence": skill.evidence,
                                "reasoning": skill.reasoning,
                                "gaps": skill.gaps,
                            }

                    render_skills_tab(explainable_dict)
                else:
                    st.info("Skill assessment not available")

            with tabs[1]:
                if results.get("jd_match"):
                    render_jd_match_tab(results["jd_match"])
                else:
                    st.info("Upload a job description to see JD matching results")

            with tabs[2]:
                if results.get("explainable"):
                    explainable_dict = {"project_evidence": []}
                    exp = results["explainable"]
                    if hasattr(exp, 'project_evidence'):
                        for proj in exp.project_evidence:
                            explainable_dict["project_evidence"].append({
                                "name": proj.name,
                                "full_name": proj.full_name,
                                "stars": proj.stars,
                                "impact": proj.impact,
                                "skills_demonstrated": proj.skills_demonstrated,
                                "why_it_matters": proj.why_it_matters,
                            })
                    render_projects_tab(explainable_dict)
                else:
                    st.info("Project evidence not available")

            with tabs[3]:
                render_raw_data_tab(results.get("raw", {}))

    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ by EightFold | "
        "[GitHub](https://github.com) | "
        "Powered by AI + Evidence Analysis"
    )


if __name__ == "__main__":
    main()
