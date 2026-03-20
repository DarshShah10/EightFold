"""
Talent Intelligence - Unified Streamlit App
=============================================
Techkriti '26 x EightFold AI — Impact Area 01: Signal Extraction & Verification

A unified 4-tab interface combining:
- EightFold's deep behavioral signal extraction (commit intelligence, skill profiling)
- Talent Intelligence's adaptive scoring (context-aware weights, gap analysis)

Tabs:
  1. JD Analysis — Context detection + adaptive weight preview + skill extraction
  2. Candidates — Deep profile generation from GitHub handles
  3. Scoring Results — Adaptive scoring with gap analysis + time-to-productivity
  4. Explainability — Evidence chains + reasoning traces

Run with: streamlit run unified_app.py
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Talent Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #1f77b4; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 1.5rem; }
    .metric-card { background: #f0f2f6; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }
    .score-excellent { color: #00c853; font-weight: 700; }
    .score-good { color: #64dd17; font-weight: 700; }
    .score-moderate { color: #ffc107; font-weight: 700; }
    .score-weak { color: #ff6d00; font-weight: 700; }
    .score-poor { color: #d50000; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 6px 6px 0 0; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #1f77b4; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ─── Imports ──────────────────────────────────────────────────────────────────
try:
    from integrator import TalentIntelligenceIntegrator, analyze, analyze_batch, analyze_codeforces, analyze_full
    from src import JDContextAnalyzer, AdaptiveScoringEngine, CrossValidator
    INTEGRATOR_OK = True
except ImportError as e:
    INTEGRATOR_OK = False
    IMPORT_ERROR = str(e)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─── Helper functions ─────────────────────────────────────────────────────────

def get_score_class(score: float) -> str:
    if score >= 0.75: return "score-excellent"
    elif score >= 0.60: return "score-good"
    elif score >= 0.45: return "score-moderate"
    elif score >= 0.30: return "score-weak"
    return "score-poor"


def get_recommendation_badge(recommendation: str) -> str:
    colors = {
        "STRONG HIRE": "🟢",
        "CONSIDER": "🟡",
        "MAYBE": "🟠",
        "PASS": "🔴",
    }
    return colors.get(recommendation, "⚪")


def render_score_bar(score: float, label: str = "") -> None:
    color = "#00c853" if score >= 0.75 else "#64dd17" if score >= 0.60 else "#ffc107" if score >= 0.45 else "#ff6d00" if score >= 0.30 else "#d50000"
    st.progress(score, text=f"{label} {score:.1%}" if label else f"{score:.1%}")


def render_signal_breakdown(signals: dict) -> None:
    """Render signal breakdown as horizontal bars."""
    signal_names = {
        "verified_skill_match": "Skill Match",
        "technical_depth": "Tech Depth",
        "learning_velocity": "Learning Velocity",
        "soft_skills_match": "Soft Skills",
        "project_complexity": "Project Complexity",
        "cultural_fit": "Cultural Fit",
        "technical_breadth": "Tech Breadth",
    }
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    fig = go.Figure()
    for i, (key, val) in enumerate(signals.items()):
        if key in signal_names:
            fig.add_trace(go.Bar(
                y=[signal_names[key]],
                x=[val],
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=[f"{val:.1%}"],
                textposition='inside',
                insidetextanchor='start',
                textfont=dict(color='white', size=11),
                hovertemplate=f"<b>{signal_names[key]}</b>: {val:.1%}<extra></extra>",
            ))

    fig.update_layout(
        height=280,
        margin=dict(l=150, r=20, t=10, b=10),
        xaxis=dict(range=[0, 1], tickformat=".0%", title=""),
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        plot_bgcolor="white",
        xaxis_gridcolor="#f0f0f0",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_adaptive_weights(weights: dict) -> None:
    """Render adaptive weights as a radar-like bar chart."""
    labels = list(weights.keys())
    values = list(weights.values())

    label_display = [l.replace("_", " ").title() for l in labels]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=label_display,
        x=values,
        orientation='h',
        marker_color=px.colors.sequential.Blues[len(values) - 1],
        text=[f"{v:.0%}" for v in values],
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color='white', size=10),
    ))

    fig.update_layout(
        height=max(200, len(labels) * 45),
        margin=dict(l=160, r=20, t=10, b=10),
        xaxis=dict(range=[0, max(values) * 1.3], tickformat=".0%", title=""),
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── Tab 1: JD Analysis ────────────────────────────────────────────────────────

def tab_jd_analysis():
    st.markdown('<p class="main-header">📋 Job Description Analysis</p>', unsafe_allow_html=True)
    st.markdown("Paste a job description below to detect context, preview adaptive weights, and extract required skills.")

    jd_text = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste the full job description here...\n\nExample: 'We are looking for a Senior Machine Learning Engineer with 5+ years of experience in Python, TensorFlow, and AWS. The ideal candidate will have experience building production ML systems and working with large-scale data pipelines.'",
        key="jd_text_input",
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        use_llm = st.checkbox("🧠 Use LLM for skill extraction (requires ANTHROPIC_API_KEY)", value=True)

    with col2:
        st.caption("💡 Tip: Disable LLM to use fast keyword-based extraction")

    if st.button("🔍 Analyze JD", type="primary", use_container_width=True):
        if len(jd_text.strip()) < 50:
            st.warning("Please paste a longer job description (at least 50 characters).")
            return

        with st.spinner("Analyzing job description context..."):
            try:
                analyzer = JDContextAnalyzer()
                context_result = analyzer.analyze_jd_context(jd_text)

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    industry = context_result.get("detected_industry", "unknown").replace("_", " ").title()
                    st.metric("🏭 Industry", industry)

                with col_b:
                    seniority = context_result.get("detected_seniority", "unknown").replace("_", " ").title()
                    st.metric("📊 Seniority", seniority)

                with col_c:
                    role_type = context_result.get("detected_role_type", "unknown").replace("_", " ").title()
                    st.metric("💼 Role Type", role_type)

                st.divider()

                # Explanation
                st.markdown("#### 💡 Context Explanation")
                st.info(context_result.get("explanation", ""))

                st.divider()

                # Adaptive weights preview
                st.markdown("#### ⚖️ Adaptive Scoring Weights (Preview)")
                st.caption("These weights will be applied when scoring candidates against this JD.")
                weights = context_result.get("adaptive_weights", {})
                if weights:
                    render_adaptive_weights(weights)

                st.divider()

                # Skill extraction
                st.markdown("#### 🛠️ Extracted Skills")
                if use_llm:
                    try:
                        from src import extract_skills_from_jd, extract_skills_fallback
                        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                        if api_key and "your-api-key" not in api_key:
                            skills = extract_skills_from_jd(jd_text)
                        else:
                            st.warning("⚠️ ANTHROPIC_API_KEY not set. Using keyword-based extraction.")
                            skills = extract_skills_fallback(jd_text)
                    except Exception as e:
                        from src import extract_skills_fallback
                        skills = extract_skills_fallback(jd_text)
                else:
                    from src import extract_skills_fallback
                    skills = extract_skills_fallback(jd_text)

                must_have = skills.get("must_have", [])
                nice_to_have = skills.get("nice_to_have", [])
                soft_skills = skills.get("soft_skills", [])
                seniority_signals = skills.get("seniority_signals", [])

                if must_have:
                    st.markdown(f"**Must Have ({len(must_have)})**")
                    st.markdown(", ".join([f"`{s}`" for s in must_have]))

                if nice_to_have:
                    st.markdown(f"**Nice to Have ({len(nice_to_have)})**")
                    st.markdown(", ".join([f"`{s}`" for s in nice_to_have[:10]]))
                    if len(nice_to_have) > 10:
                        st.caption(f"...and {len(nice_to_have) - 10} more")

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    if soft_skills:
                        st.markdown(f"**Soft Skills ({len(soft_skills)})**")
                        st.markdown(", ".join([f"`{s}`" for s in soft_skills]))
                with col_s2:
                    if seniority_signals:
                        st.markdown(f"**Seniority Signals**")
                        for sig in seniority_signals:
                            st.markdown(f"- {sig}")

            except Exception as e:
                st.error(f"Error analyzing JD: {e}")
                if "OPENAI" in str(e).upper() or "API" in str(e).upper():
                    st.info("💡 Try disabling LLM extraction above for a faster keyword-based analysis.")


# ─── Tab 2: Candidate Profiles ─────────────────────────────────────────────────

def tab_candidates():
    st.markdown('<p class="main-header">👥 Candidate Profiles</p>', unsafe_allow_html=True)
    st.markdown("Enter GitHub handles to generate deep behavioral profiles. Each profile includes commit intelligence, skill analysis, and project impact.")

    # Show cached users
    try:
        integrator = TalentIntelligenceIntegrator()
        cached = integrator.list_cached_users()
        if cached:
            st.markdown(f"**📦 {len(cached)} user(s) in local cache** — these will use instant DB lookup")
            with st.expander("View cached users"):
                for u in cached[:10]:
                    last = u["last_harvested"] or "unknown"
                    st.text(f"  @{u['handle']} — last harvested: {last}")
    except Exception:
        pass

    # GitHub handles input
    handles_text = st.text_area(
        "GitHub Handles",
        height=80,
        placeholder="Enter GitHub handles (one per line)\n\ne.g.:\ngvanrossum\ntwisted\nvadimdn\n",
        key="handles_input",
    )

    handles = [h.strip() for h in handles_text.strip().split("\n") if h.strip()]

    # Options
    col_opt1, col_opt2, col_opt3 = st.columns([1, 1, 1])
    with col_opt1:
        st.session_state.setdefault("candidate_mode", "demo")
        mode = st.radio("Analysis Mode", ["🤖 Demo (Synthetic)", "🔴 Live (GitHub Token)"], horizontal=True, index=0)

    with col_opt2:
        github_token = st.text_input("GitHub Token", type="password", placeholder="ghp_...", help="Required for live mode. Reads from GITHUB_TOKEN env var if empty.")

    with col_opt3:
        force_refresh = st.checkbox("🔄 Force Re-fetch", help="Ignore cached DB data and re-harvest from GitHub")

    if st.button("🔎 Generate Profiles", type="primary", use_container_width=True):
        if not handles:
            st.warning("Please enter at least one GitHub handle.")
            return

        token = github_token or os.environ.get("GITHUB_TOKEN")

        if mode == "🔴 Live (GitHub Token)" and not token:
            st.error("GitHub token required for live mode. Enter it above or set GITHUB_TOKEN env var.")
            return

        for handle in handles:
            with st.spinner(f"Analyzing {handle}..."):
                try:
                    result = analyze(handle, " ", github_token=token, force_refresh=force_refresh)
                except Exception as e:
                    st.error(f"Error analyzing {handle}: {e}")
                    continue

                st.divider()
                st.markdown(f"### 🧑‍💻 {handle}")

                # Basic info
                candidate = result.get("candidate", {})
                ci = result.get("commit_intelligence", {})
                si = result.get("skill_intelligence", {})

                col_h, col_h2, col_h3, col_h4 = st.columns(4)
                with col_h:
                    name = candidate.get("name", "—")
                    st.markdown(f"**Name:** {name}")
                with col_h2:
                    loc = candidate.get("location", "—")
                    st.markdown(f"**Location:** {loc}")
                with col_h3:
                    repos = candidate.get("public_repos", 0)
                    st.metric("Public Repos", repos)
                with col_h4:
                    mode_emoji = "🤖" if candidate.get("use_mode") == "synthetic" else "🔴"
                    data_src = candidate.get("data_source", "")
                    src_emoji = "📦" if data_src == "db_cache" else "🌐" if data_src == "live_api" else "🤖"
                    src_label = "DB Cache" if data_src == "db_cache" else "Live API" if data_src == "live_api" else data_src
                    st.markdown(f"**Mode:** {mode_emoji} {candidate.get('use_mode', '')}")
                    st.caption(f"**Source:** {src_emoji} {src_label}")

                # Commit Intelligence
                st.markdown("#### 🧠 Commit Intelligence")
                score = ci.get("score", 0)
                render_score_bar(score / 100, "Intelligence Score")

                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    archetype = ci.get("archetype", "Unknown")
                    tagline = ci.get("archetype_tagline", "")
                    st.markdown(f"**Archetype:** {archetype}")
                    if tagline:
                        st.caption(tagline)
                with col_d2:
                    dims = ci.get("dimensions", {})
                    if dims:
                        top_dim = max(dims.items(), key=lambda x: x[1])
                        st.markdown(f"**Strongest Dimension:** {str(top_dim[0]).replace('_', ' ').title()}")
                        st.caption(f"Score: {top_dim[1]:.1%}")
                with col_d3:
                    commits_n = ci.get("commits_analyzed", 0)
                    st.metric("Commits Analyzed", commits_n)

                # Citations
                citations = ci.get("citations", [])
                if citations:
                    with st.expander("🏆 Notable Achievements"):
                        for cit in citations[:3]:
                            cit_text = cit.get("title", cit.get("text", str(cit)))
                            st.markdown(f"- {cit_text}")

                # Skill Intelligence
                st.markdown("#### 🛠️ Skill Intelligence")
                col_sk1, col_sk2, col_sk3 = st.columns(3)
                with col_sk1:
                    sl = si.get("skill_level", "—")
                    conf = si.get("skill_level_confidence", 0)
                    st.markdown(f"**Skill Level:** {sl}")
                    if conf > 0:
                        st.caption(f"Confidence: {conf:.0%}")
                with col_sk2:
                    domains = si.get("primary_domains", [])
                    if domains:
                        st.markdown(f"**Primary Domains:** {', '.join(domains[:3])}")
                with col_sk3:
                    depth = si.get("depth_category", "—")
                    st.markdown(f"**Depth:** {depth}")

                # Languages
                langs = si.get("primary_language", {})
                if langs:
                    with st.expander("💻 Languages Used"):
                        for lang, score_val in list(langs.items())[:8]:
                            st.progress(min(score_val, 1.0) if isinstance(score_val, (int, float)) else 0.5,
                                       text=f"{lang}: {score_val:.0%}" if isinstance(score_val, (int, float)) else f"{lang}")

                st.divider()


# ─── Tab 3: Scoring Results ───────────────────────────────────────────────────

def tab_scoring_results():
    st.markdown('<p class="main-header">📊 Scoring Results</p>', unsafe_allow_html=True)
    st.markdown("Enter a job description and GitHub handles to score candidates with adaptive weights, gap analysis, and hiring recommendations.")

    # JD input
    jd_text = st.text_area(
        "Job Description",
        height=150,
        placeholder="Paste job description here...",
        key="scoring_jd_input",
    )

    # Handles input
    scoring_handles_text = st.text_area(
        "GitHub Handles (one per line)",
        height=80,
        placeholder="Enter GitHub handles...",
        key="scoring_handles",
    )

    col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
    with col_t1:
        use_llm = st.checkbox("🧠 Use LLM for JD skill extraction", value=True)
    with col_t2:
        github_token = st.text_input("GitHub Token (optional)", type="password", placeholder="ghp_...")
    with col_t3:
        force_refresh = st.checkbox("🔄 Force Re-fetch", help="Ignore DB cache, re-harvest from GitHub")

    if st.button("🎯 Score Candidates", type="primary", use_container_width=True):
        handles = [h.strip() for h in scoring_handles_text.strip().split("\n") if h.strip()]

        if not handles:
            st.warning("Please enter at least one GitHub handle.")
            return
        if len(jd_text.strip()) < 50:
            st.warning("Please enter a longer job description.")
            return

        token = github_token or os.environ.get("GITHUB_TOKEN")

        with st.spinner(f"Scoring {len(handles)} candidate(s)..."):
            try:
                results = analyze_batch(handles, jd_text, github_token=token, force_refresh=force_refresh)
            except Exception as e:
                st.error(f"Scoring error: {e}")
                return

        if not results:
            st.error("No results returned.")
            return

        # ── Summary Cards ──────────────────────────────────────────────────
        st.divider()
        st.markdown("## 🏆 Candidate Rankings")

        for i, result in enumerate(results):
            ranking = result.get("ranking", i + 1)
            handle = result.get("candidate", {}).get("github_handle", "unknown")
            scoring = result.get("scoring", {})
            unified = result.get("unified_recommendation", {})
            recommendation = unified.get("recommendation", scoring.get("hiring_recommendation", "UNKNOWN"))
            badge = get_recommendation_badge(recommendation)
            score = scoring.get("match_score", 0)
            score_class = get_score_class(score)
            data_src = result.get("candidate", {}).get("data_source", "")
            src_emoji = "📦" if data_src == "db_cache" else "🌐" if data_src == "live_api" else "🤖"
            src_label = "DB" if data_src == "db_cache" else "Live" if data_src == "live_api" else "Demo"

            with st.container():
                st.markdown(f"### {badge} #{ranking} — {handle}  {src_emoji}*{src_label}*")
                st.markdown(f'<span class="{score_class}">Match Score: {score:.1%}</span> | '
                           f'<span class="{score_class}">{recommendation}</span>', unsafe_allow_html=True)

                col_main1, col_main2, col_main3, col_main4 = st.columns([1, 1, 1, 1])
                with col_main1:
                    st.metric("Overall", f"{score:.1%}", help="Composite match score")
                with col_main2:
                    jd_ctx = scoring.get("jd_context", {})
                    industry = jd_ctx.get("detected_industry", "unknown").replace("_", " ").title()
                    st.metric("JD Context", industry)
                with col_main3:
                    gap = scoring.get("gap_analysis", {})
                    missing = len(gap.get("missing_skills", []))
                    st.metric("Missing Skills", missing)
                with col_main4:
                    time_prod = gap.get("time_to_productivity", "—")
                    st.metric("Time to Productivity", time_prod)

                # Signal breakdown
                with st.expander("📊 Signal Breakdown"):
                    signals = scoring.get("signal_breakdown", {})
                    if signals:
                        render_signal_breakdown(signals)
                    else:
                        st.info("No signal breakdown available")

                # Adaptive weights
                with st.expander("⚖️ Adaptive Weights Applied"):
                    weights = scoring.get("adaptive_weights", {})
                    if weights:
                        render_adaptive_weights(weights)

                # Gap Analysis
                with st.expander("🔍 Gap Analysis"):
                    gap = scoring.get("gap_analysis", {})
                    if gap:
                        matched = gap.get("matched_skills", [])
                        missing = gap.get("missing_skills", [])
                        adjacent = gap.get("adjacent_skills", [])

                        if matched:
                            st.markdown(f"✅ **Matched ({len(matched)})**")
                            cols = st.columns(3)
                            for idx, m in enumerate(matched[:9]):
                                with cols[idx % 3]:
                                    st.markdown(f"- `{m.get('skill', m)}`")

                        if missing:
                            st.markdown(f"❌ **Missing ({len(missing)})**")
                            for m in missing[:6]:
                                lt = m.get("learning_time", "—")
                                st.markdown(f"- `{m.get('skill', m)}` — {lt}")
                            if len(missing) > 6:
                                st.caption(f"...and {len(missing) - 6} more")

                        if adjacent:
                            st.markdown(f"🔶 **Adjacent Skills ({len(adjacent)})**")
                            for a in adjacent[:6]:
                                st.markdown(f"- `{a.get('required', '')}` ← has `{a.get('candidate_has', '')}`")

                        # Gap summary
                        summary = gap.get("gap_summary", "")
                        if summary:
                            st.info(f"📝 {summary}")

                # Unified recommendation
                if unified:
                    with st.expander("🎯 Unified Recommendation"):
                        st.markdown(f"**Score:** {unified.get('unified_score', 0):.1%}")
                        st.markdown(f"**Recommendation:** {badge} {recommendation}")
                        st.markdown(f"**Rationale:** {unified.get('rationale', '')}")
                        st.caption(f"Confidence: {unified.get('confidence', 0):.1%}")

                # Commit Intelligence (if available)
                ci = result.get("commit_intelligence", {})
                if ci.get("score", 0) > 0:
                    with st.expander("🧠 Commit Intelligence"):
                        st.markdown(f"**Score:** {ci.get('score', 0):.0f}/100")
                        st.markdown(f"**Archetype:** {ci.get('archetype', 'Unknown')} — {ci.get('archetype_tagline', '')}")
                        dims = ci.get("dimensions", {})
                        if dims:
                            for dim, val in dims.items():
                                if isinstance(val, (int, float)):
                                    st.progress(min(val, 1.0),
                                               text=f"{str(dim).replace('_', ' ').title()}: {val:.1%}")

                # Cross-validation (if available)
                cv = result.get("cross_validation", {})
                if cv and cv.get("validation_result"):
                    with st.expander("🔏 Resume Cross-Validation"):
                        vr = cv["validation_result"]
                        st.markdown(f"**Authenticity Rating:** {vr.get('authenticity_rating', 'Unknown')}")
                        st.markdown(f"**Verification Rate:** {vr.get('verification_rate', 0):.0%}")
                        st.markdown(f"**Verified:** {vr.get('verified_skills', 0)}/{vr.get('total_skills_claimed', 0)} skills")
                        vr_skills = vr.get("validated_skills", [])
                        if vr_skills:
                            for vs in vr_skills[:5]:
                                status = "✅" if vs.get("verified") else "❌"
                                conf = vs.get("confidence", 0)
                                st.markdown(f"{status} `{vs.get('skill', '')}` — {conf:.0%} confidence")

                st.divider()

        # ── Comparative Chart ───────────────────────────────────────────────
        if len(results) > 1:
            st.markdown("#### 📈 Score Comparison")
            fig = go.Figure()
            for i, result in enumerate(results):
                handle = result.get("candidate", {}).get("github_handle", f"Candidate {i+1}")
                score = result.get("scoring", {}).get("match_score", 0)
                ci_score = result.get("commit_intelligence", {}).get("score", 0) / 100
                unified_score = result.get("unified_recommendation", {}).get("unified_score", 0)

                fig.add_trace(go.Bar(
                    name=handle,
                    x=["Match Score", "Commit Intel", "Unified Score"],
                    y=[score, ci_score, unified_score],
                    text=[f"{score:.0%}", f"{ci_score:.0%}", f"{unified_score:.0%}"],
                    textposition='outside',
                ))

            fig.update_layout(
                barmode='group',
                yaxis_tickformat=".0%",
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=20, t=50, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)


# ─── Tab 4: Explainability ────────────────────────────────────────────────────

def tab_explainability():
    st.markdown('<p class="main-header">🔍 Explainability Engine</p>', unsafe_allow_html=True)
    st.markdown("See the full reasoning chain behind candidate scores — evidence, citations, and bias checks.")

    # Single candidate deep-dive
    handle = st.text_input("GitHub Handle", placeholder="e.g., gvanrossum", key="explain_handle")
    jd_explain = st.text_area("Job Description", height=120, placeholder="Paste JD...", key="explain_jd")

    if st.button("🔬 Generate Explanation", type="primary", use_container_width=True):
        if not handle or len(jd_explain.strip()) < 30:
            st.warning("Please enter a GitHub handle and a job description.")
            return

        github_token = os.environ.get("GITHUB_TOKEN")

        with st.spinner("Generating full explainability report..."):
            try:
                result = analyze(handle, jd_explain, github_token=github_token)
            except Exception as e:
                st.error(f"Error: {e}")
                return

        scoring = result.get("scoring", {})
        explainability = result.get("explainability", {})
        cv = result.get("cross_validation", {})
        ci = result.get("commit_intelligence", {})
        si = result.get("skill_intelligence", {})

        # Overall score
        score = scoring.get("match_score", 0)
        score_class = get_score_class(score)
        st.markdown(f"### Overall Match: <span class='{score_class}'>{score:.1%}</span>", unsafe_allow_html=True)

        # Reasoning chain
        st.markdown("#### 🧩 Reasoning Chain")
        reasoning = scoring.get("reasoning", "No reasoning generated.")
        st.info(f"💡 {reasoning}")

        # ── NEW: Skill Evidence Chains with GitHub Links ──────────────────────
        st.markdown("#### 🔗 Skill Evidence Chains (Source Tracking)")
        chains = explainability.get("reasoning_chains", [])
        if chains:
            for chain in chains:
                skill = chain.get("skill", "")
                chain_type = chain.get("type", "unknown")
                conf = chain.get("confidence", 0)
                evidence_summary = chain.get("evidence_summary", "")
                reasoning_text = chain.get("reasoning", "")
                github_links = chain.get("github_links", [])
                commits = chain.get("commits", [])

                icon = "✅" if chain_type == "language" else "🔶" if chain_type == "adjacent" else "❌"
                color = "green" if chain_type == "language" else "orange" if chain_type == "adjacent" else "red"

                with st.expander(f"{icon} **{skill}** — {evidence_summary} (confidence: {conf:.0%})"):
                    if reasoning_text:
                        st.markdown(f"**Why we believe this:** {reasoning_text}")

                    if github_links:
                        st.markdown(f"**📦 Repositories providing evidence:**")
                        for link in github_links:
                            url = link.get("url", "")
                            label = link.get("label", "")
                            desc = link.get("desc", "")
                            stars = link.get("stars", 0)
                            st.markdown(
                                f"- [{label}]({url}) {'⭐' + str(stars) if stars else ''} "
                                f"{f'— {desc[:60]}' if desc else ''}"
                            )

                    if commits:
                        st.markdown(f"**💻 Commits showing this skill:**")
                        for commit in commits[:3]:
                            url = commit.get("url", "")
                            sha = commit.get("sha", "")
                            msg = commit.get("message", "")
                            repo = commit.get("repo", "")
                            if url:
                                st.markdown(f"- [`{sha}`]({url}) in *{repo}* — {msg[:60]}")
                            else:
                                st.markdown(f"- `{sha}` in *{repo}* — {msg[:60]}")

                    st.markdown(f"**Confidence:** {conf:.0%}")
        else:
            st.info("No evidence chains generated yet. Try scoring with a GitHub handle that has cached data.")

        # Evidence per signal
        st.markdown("#### 📊 Signal Breakdown")

        # Evidence per signal
        st.markdown("#### 📋 Evidence Per Signal")
        signals = scoring.get("signal_breakdown", {})
        for signal_key, signal_val in signals.items():
            label = signal_key.replace("_", " ").title()
            color = "#00c853" if signal_val >= 0.7 else "#ffc107" if signal_val >= 0.4 else "#d50000"
            st.markdown(
                f"<div style='display:flex;align-items:center;margin:4px 0;'>"
                f"<div style='width:{signal_val*100:.0f}%;background:{color};opacity:0.7;height:8px;border-radius:4px;'></div>"
                f"<span style='margin-left:8px;font-weight:600;'>{label}: {signal_val:.0%}</span></div>",
                unsafe_allow_html=True
            )

        # Commit intelligence citations
        st.markdown("#### 🏆 Commit Intelligence Citations")
        citations = ci.get("citations", [])
        if citations:
            for j, cit in enumerate(citations[:5]):
                cit_text = cit.get("title", cit.get("text", str(cit)))
                cit_type = cit.get("category", cit.get("type", "achievement"))
                emoji = "⭐" if "star" in str(cit_type).lower() else "🔧" if "fix" in str(cit_type).lower() else "📝"
                st.markdown(f"{emoji} *{cit_text}*")
        else:
            st.info("No commit citations available (insufficient commit data)")

        # Cross-validation evidence
        st.markdown("#### 🔏 Resume vs GitHub Verification")
        if cv and cv.get("validation_result"):
            vr = cv["validation_result"]
            for vs in vr.get("validated_skills", []):
                skill = vs.get("skill", "")
                verified = vs.get("verified", False)
                conf = vs.get("confidence", 0)
                evidence = vs.get("evidence", [])
                gap_exp = vs.get("gap_explanation", "")

                status = "✅" if verified else "⚠️"
                with st.expander(f"{status} `{skill}` — {conf:.0%} confidence"):
                    st.markdown(f"**Gap:** {gap_exp}")
                    if evidence:
                        st.markdown("**Evidence:**")
                        for e in evidence:
                            st.markdown(f"- {e}")
        else:
            st.info("No resume cross-validation available. Provide a PDF resume in the Candidates tab to enable this.")

        # JD context explanation
        st.markdown("#### 🎯 JD Context & Weight Rationale")
        jd_ctx = scoring.get("jd_context", {})
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.metric("Industry", jd_ctx.get("detected_industry", "—").replace("_", " ").title())
        with col_e2:
            st.metric("Seniority", jd_ctx.get("detected_seniority", "—").replace("_", " ").title())
        with col_e3:
            st.metric("Role Type", jd_ctx.get("detected_role_type", "—").replace("_", " ").title())
        st.markdown(f"**Explanation:** {jd_ctx.get('weight_explanation', '')}")

        # Warnings / bias check
        st.markdown("#### ⚠️ Bias Check & Warnings")
        warnings = explainability.get("warnings", [])
        if warnings:
            for w in warnings:
                st.warning(w)
        else:
            st.success("No warnings detected. Reasoning chain appears robust.")

        confidence = explainability.get("confidence_score", 0)
        st.markdown(f"**Explainability Confidence:** {confidence:.0%}")


# ─── Tab 5: Codeforces ─────────────────────────────────────────────────────────

def tab_codeforces():
    st.markdown('<p class="main-header">🏆 Codeforces Verification</p>', unsafe_allow_html=True)
    st.markdown("Verify competitive programming skills and detect potential cheating on Codeforces. This provides a 10% signal boost to the overall scoring score.")

    # Warning banner
    st.warning(
        "🚨 **Flag Detection Active**: This module detects if a candidate skipped ALL problems in contests "
        "(cheated pattern). Hard-flagged users get 0 problem-solving score. "
        "This is a **port of the CFCheatDetector Cheated.jsx logic**."
    )

    col_cf1, col_cf2 = st.columns([1, 1])
    with col_cf1:
        cf_handle = st.text_input(
            "Codeforces Handle",
            placeholder="e.g., tourist, Petr, tourist",
            help="Enter the Codeforces username to analyze"
        )
    with col_cf2:
        st.markdown("")  # Spacer
        st.markdown("")  # Spacer
        st.caption("Enter a handle above to analyze competitive programming profile")

    # Optional JD input for skill relevance
    st.markdown("**Job Description for Skill Relevance (Optional)**")
    cf_jd = st.text_area(
        "Job Description (for JD skill matching)",
        height=100,
        placeholder="Paste JD here to see how CF topics map to required skills...",
        key="cf_jd_input",
    )

    if st.button("🔬 Analyze Codeforces Profile", type="primary", use_container_width=True):
        if not cf_handle.strip():
            st.warning("Please enter a Codeforces handle.")
            return

        with st.spinner(f"Analyzing Codeforces profile: {cf_handle}..."):
            try:
                cf_result = analyze_codeforces(cf_handle, cf_jd)
            except Exception as e:
                st.error(f"Error: {e}")
                return

        # Handle errors
        if cf_result.get("error"):
            if "not found" in str(cf_result.get("error", "")).lower():
                st.error(f"User '{cf_handle}' not found on Codeforces.")
            else:
                st.error(f"Error: {cf_result.get('error')}")
            return

        # ── Skipped Contests Banner (Show prominently) ─────────────────────
        cheated = cf_result.get("cheated_contests", [])
        is_flagged = cf_result.get("is_flagged", False)
        flag_type = cf_result.get("flag_type", "none")
        
        if cheated:
            st.error(f"**{len(cheated)} contest(s) with ALL problems skipped** — possible cheating detected")
            for c in cheated[:3]:
                name = c.get("contest_name", "Unknown Contest")
                skipped = c.get("problems_skipped", 0)
                attempted = c.get("problems_attempted", 0)
                st.markdown(f"- `{name}`: skipped {skipped}/{attempted} problems")
            if len(cheated) > 3:
                st.caption(f"...and {len(cheated) - 3} more skipped contests")
            st.divider()
        elif is_flagged:
            st.warning(f"Flagged: {flag_type}")
            st.divider()

        # ── Verdict Banner ────────────────────────────────────────────────
        verdict = cf_result.get("verdict", "")
        is_flagged = cf_result.get("is_flagged", False)
        flag_type = cf_result.get("flag_type", "none")

        if "🚨" in verdict or is_flagged:
            if flag_type == "hard":
                st.error(f"## 🚨 HARDFLAG: Cheated in Contests\n\n{verdict}")
            elif flag_type == "soft":
                st.warning(f"## ⚠️ SOFT FLAG: Suspicious Pattern\n\n{verdict}")
            else:
                st.warning(f"## ⚠️ FLAGGED: {flag_type}\n\n{verdict}")
        elif "✅" in verdict:
            st.success(f"## ✅ {verdict}")
        elif "⚪" in verdict:
            st.info(f"## ⚪ {verdict}")
        else:
            st.info(f"## {verdict}")

        # ── Rating & Badge ───────────────────────────────────────────────
        st.markdown("### 🏅 Rating Profile")
        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
        with col_r1:
            rating = cf_result.get("rating", 0)
            max_rating = cf_result.get("max_rating", 0)
            tier = cf_result.get("rating_tier", "Unrated")
            emoji = cf_result.get("rating_emoji", "⚪")
            st.metric("Rating", f"{emoji} {max_rating}")
            st.caption(f"{tier}")
        with col_r2:
            st.metric("Current Rating", cf_result.get("rating", 0))
        with col_r3:
            problems = cf_result.get("problems_solved", 0)
            st.metric("Problems Solved", problems)
        with col_r4:
            contests = cf_result.get("contest_count", 0)
            st.metric("Contests", contests)
        with col_r5:
            ac_rate = cf_result.get("ac_rate", 0)
            st.metric("AC Rate", f"{ac_rate:.0%}")

        # Profile link
        st.markdown(f"[🔗 View on Codeforces]({cf_result.get('profile_url', '#')})")

        # ── Problem-Solving Score ────────────────────────────────────────
        st.markdown("### 📊 Problem-Solving Score")
        ps_score = cf_result.get("problem_solving_score", 0.0)
        render_score_bar(ps_score, "Problem-Solving Score")

        col_ps1, col_ps2 = st.columns(2)
        with col_ps1:
            tier_desc = cf_result.get("tier_description", "")
            if tier_desc:
                st.info(f"**Engineering Level:** {tier_desc}")
        with col_ps2:
            # Top topics
            topics = cf_result.get("top_topics", [])
            if topics:
                st.markdown(f"**Top Topics:** {', '.join([f'`{t}`' for t in topics[:5]])}")

        # ── Flag Details ────────────────────────────────────────────────
        if is_flagged:
            st.markdown("### 🚨 Flag Details")
            col_fl1, col_fl2 = st.columns(2)
            with col_fl1:
                st.metric("Flag Type", flag_type.upper())
                st.metric("Flag Score", f"{cf_result.get('flag_score', 0):.1%}")
            with col_fl2:
                evidence = cf_result.get("flag_evidence", [])
                if evidence:
                    for ev in evidence:
                        st.markdown(f"- {ev}")

            # Cheated contests
            cheated = cf_result.get("cheated_contests", [])
            if cheated:
                st.markdown("**🚨 Contests Where ALL Problems Were Skipped:**")
                for c in cheated[:5]:
                    cid = c.get("contest_id", "?")
                    name = c.get("contest_name", f"Contest {cid}")
                    attempted = c.get("problems_attempted", 0)
                    skipped = c.get("problems_skipped", 0)
                    url = c.get("contest_url", "#")
                    st.markdown(
                        f"- [{name}]({url}) — skipped {skipped}/{attempted} problems"
                    )

        # ── Difficulty Breakdown ────────────────────────────────────────
        st.markdown("### 📈 Difficulty Breakdown")
        difficulty = cf_result.get("difficulty_breakdown", {})
        if difficulty:
            # Render as horizontal bars
            fig = go.Figure()
            sorted_buckets = sorted(difficulty.items(), key=lambda x: x[0])
            labels = [b[0].split(" ")[0] for b in sorted_buckets]
            values = list(difficulty.values())

            fig.add_trace(go.Bar(
                y=labels,
                x=values,
                orientation='h',
                marker_color=px.colors.sequential.Blues[5],
                text=values,
                textposition='outside',
            ))
            fig.update_layout(
                height=max(200, len(labels) * 40),
                margin=dict(l=120, r=40, t=10, b=10),
                xaxis_title="Problems Solved",
                yaxis=dict(autorange="reversed"),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No difficulty data available (problems may not have ratings).")

        # ── Topics / Tags ───────────────────────────────────────────────
        topics_detail = cf_result.get("topics_detail", [])
        if topics_detail:
            st.markdown("### 🏷️ Topic Analysis")
            cols = st.columns(2)
            for idx, topic in enumerate(topics_detail[:8]):
                with cols[idx % 2]:
                    name = topic.get("name", "")
                    count = topic.get("count", 0)
                    avg_r = topic.get("avg_rating", 0)
                    max_r = topic.get("max_rating", 0)
                    st.markdown(
                        f"**{name}** — {count} problems, avg: {avg_r:.0f}, max: {max_r}"
                    )

        # ── Languages Used ──────────────────────────────────────────────
        languages = cf_result.get("languages", {})
        if languages:
            st.markdown("### 💻 Programming Languages")
            top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
            for lang, count in top_langs:
                st.markdown(f"- **{lang}:** {count} accepted submissions")

        # ── JD Relevance ───────────────────────────────────────────────
        jd_rel = cf_result.get("jd_relevance", {})
        if jd_rel:
            st.markdown("### 🎯 JD Skill Relevance")
            coverage = jd_rel.get("coverage", 0)
            st.metric("Coverage", f"{coverage:.0%}")

            matched = jd_rel.get("matched_skills", [])
            partial = jd_rel.get("partial_skills", [])
            if matched:
                st.markdown(f"**✅ Matched Job Skills ({len(matched)}):**")
                st.markdown(", ".join([f"`{s}`" for s in matched]))
            if partial:
                st.markdown(f"**🔶 Partial Match ({len(partial)}):**")
                st.markdown(", ".join([f"`{s}`" for s in partial[:5]]))
            if not matched and not partial:
                st.info("No direct matches between CF topics and JD skills. The candidate's CP topics don't overlap with job requirements.")

            # CF topics mapped to job skills
            job_skills_mapped = jd_rel.get("job_skills_mapped", [])
            if job_skills_mapped:
                st.markdown(f"**CF Topics → Job Skills:** {', '.join([f'`{s}`' for s in job_skills_mapped[:8]])}")


# ─── Tab 6: Virtual Interview ─────────────────────────────────────────────────

def tab_virtual_interview():
    """Virtual Interview - Adaptive Micro-Assessment Engine."""
    st.markdown('<p class="main-header">🎤 Virtual Interview Engine</p>', unsafe_allow_html=True)
    st.markdown("Adaptive micro-assessment for interviewing candidates with skill-based questions and real-time evaluation.")

    # Import and run the virtual interview app
    try:
        from virtual_interview import app as vi_app
        # Run the virtual interview's app logic inline
        run_virtual_interview()
    except ImportError as e:
        st.error(f"Failed to import Virtual Interview module: {e}")
        st.info("Make sure all dependencies are installed: `pip install -r requirements.txt`")
        st.markdown("""
        **Alternative:** Run the Virtual Interview separately:
        ```bash
        cd virtual_interview
        streamlit run app.py
        ```
        """)


def run_virtual_interview():
    """Run the virtual interview workflow inline."""
    import json
    import yaml

    # Initialize session state for virtual interview
    st.session_state.setdefault('vi_phase', 'start')
    st.session_state.setdefault('vi_questions', [])
    st.session_state.setdefault('vi_answers', {})
    st.session_state.setdefault('vi_scores', [])
    st.session_state.setdefault('vi_skill', None)
    st.session_state.setdefault('vi_rubric', None)
    st.session_state.setdefault('vi_difficulty', 'medium')

    # Start/Setup phase
    if st.session_state.vi_phase == 'start':
        st.markdown("### Configure Interview")
        
        skill_options = [
            "Python", "JavaScript", "SQL", "Docker", "Kubernetes",
            "Machine Learning", "System Design", "APIs", "Testing"
        ]
        skill = st.selectbox("Select Skill to Assess", skill_options, key="vi_skill_select")
        difficulty = st.radio("Difficulty Level", ["Easy", "Medium", "Hard"], horizontal=True, index=1, key="vi_diff")
        
        # Load rubric
        rubric_file = f"virtual_interview/rubrics/{skill.lower().replace(' ', '_')}.yaml"
        try:
            with open(rubric_file, 'r') as f:
                rubric = yaml.safe_load(f)
            st.session_state.vi_rubric = rubric
        except:
            rubric = {"criteria": [{"name": "Code Quality", "weight": 0.4}, {"name": "Correctness", "weight": 0.4}, {"name": "Efficiency", "weight": 0.2}]}
        
        if st.button("Start Interview", type="primary"):
            st.session_state.vi_skill = skill
            st.session_state.vi_difficulty = difficulty.lower()
            st.session_state.vi_phase = 'question'
            st.rerun()
    
    # Question phase
    elif st.session_state.vi_phase == 'question':
        skill = st.session_state.vi_skill
        difficulty = st.session_state.vi_difficulty
        
        st.markdown(f"### {skill} Interview - {difficulty.capitalize()} Level")
        
        # Sample questions based on skill
        questions_db = {
            "Python": {
                "easy": ["What is the difference between a list and a tuple?", "Explain list comprehensions"],
                "medium": ["Explain decorators and when to use them", "What is the Global Interpreter Lock (GIL)?"],
                "hard": ["Implement a context manager from scratch", "Explain metaclasses"]
            },
            "Docker": {
                "easy": ["What is a Docker container?", "Difference between image and container"],
                "medium": ["Explain Docker networking modes", "How do you debug a container?"],
                "hard": ["Design a multi-stage Dockerfile for a Python app", "Explain container orchestration"]
            }
        }
        
        questions = questions_db.get(skill, {}).get(difficulty, [f"Explain {skill} fundamentals"])
        q_idx = len(st.session_state.vi_answers)
        
        if q_idx < len(questions):
            q = questions[q_idx]
            st.markdown(f"**Question {q_idx + 1}:** {q}")
            
            answer = st.text_area("Your Answer", height=150, key=f"vi_answer_{q_idx}")
            
            if st.button("Submit Answer"):
                st.session_state.vi_answers[q_idx] = answer
                
                # Simple scoring based on answer length and keywords
                score = min(len(answer) / 500, 1.0) if answer else 0.0
                if len(answer) > 200:
                    score = 0.5 + min((len(answer) - 200) / 800, 0.5)
                st.session_state.vi_scores.append(score)
                
                if q_idx + 1 >= len(questions):
                    st.session_state.vi_phase = 'results'
                st.rerun()
        else:
            st.session_state.vi_phase = 'results'
            st.rerun()
    
    # Results phase
    elif st.session_state.vi_phase == 'results':
        st.markdown("### Interview Results")
        
        total_score = sum(st.session_state.vi_scores) / max(len(st.session_state.vi_scores), 1) if st.session_state.vi_scores else 0
        
        st.metric("Overall Score", f"{total_score * 100:.0f}%")
        
        if total_score >= 0.7:
            st.success("Strong performance! The candidate demonstrates solid understanding.")
        elif total_score >= 0.4:
            st.warning("Moderate performance. Some gaps in knowledge identified.")
        else:
            st.error("Needs improvement. Significant gaps in core concepts.")
        
        # Show breakdown
        for i, score in enumerate(st.session_state.vi_scores):
            st.markdown(f"- Question {i+1}: {'Pass' if score >= 0.5 else 'Needs Work'}")
        
        if st.button("Start New Interview"):
            for key in ['vi_phase', 'vi_questions', 'vi_answers', 'vi_scores', 'vi_skill', 'vi_rubric']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# ─── Main App ──────────────────────────────────────────────────────────────────

def main():
    # Header
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0;">
            <h1 style="font-size:2.2rem; margin-bottom:0.3rem;">🧠 Talent Intelligence</h1>
            <p style="color:#666; font-size:1rem;">Techkriti '26 × EightFold AI — Signal Extraction & Verification</p>
            <p style="color:#888; font-size:0.85rem;">Adaptive Scoring + Deep Behavioral Signal Extraction</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not INTEGRATOR_OK:
        st.error(f"Failed to import integration modules: {IMPORT_ERROR}")
        st.info("Make sure you're running from the EightFold directory: `streamlit run unified_app.py`")
        st.code("cd C:\\Darsh\\Techkriti\\Resume_Parser\\EightFold && streamlit run unified_app.py", language="bash")
        return

    tabs = st.tabs([
        "📋 JD Analysis",
        "👥 Candidates",
        "📊 Scoring Results",
        "🔍 Explainability",
        "🏆 Codeforces",
        "🎤 Interview",
    ])

    with tabs[0]:
        tab_jd_analysis()
    with tabs[1]:
        tab_candidates()
    with tabs[2]:
        tab_scoring_results()
    with tabs[3]:
        tab_explainability()
    with tabs[4]:
        tab_codeforces()
    with tabs[5]:
        tab_virtual_interview()


if __name__ == "__main__":
    main()
