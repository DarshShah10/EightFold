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
    from integrator import TalentIntelligenceIntegrator, analyze, analyze_batch
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


# ─── Tab 5: Virtual Interview ─────────────────────────────────────────────────

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

    # Initialize session state for virtual interview
    st.session_state.setdefault('vi_phase', 'start')
    st.session_state.setdefault('vi_skills', [])
    st.session_state.setdefault('vi_selected_skills', [])
    st.session_state.setdefault('vi_current_skill_idx', 0)
    st.session_state.setdefault('vi_current_skill', None)
    st.session_state.setdefault('vi_question', None)
    st.session_state.setdefault('vi_eval_done', False)
    st.session_state.setdefault('vi_evaluation', None)
    st.session_state.setdefault('vi_skill_scores', {})
    st.session_state.setdefault('vi_difficulty', {})
    st.session_state.setdefault('vi_history', [])
    st.session_state.setdefault('vi_answers', [])
    st.session_state.setdefault('vi_job_role', 'Software Engineer')

    # CSS
    st.markdown("""
    <style>
    .vi-question-box { background: #1e1e1e; color: #fff; padding: 20px; border-radius: 10px; border-left: 5px solid #9c27b0; margin: 10px 0; }
    .vi-result-box { background: #2d2d2d; padding: 15px; border-radius: 10px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

    def reset_vi():
        for key in list(st.session_state.keys()):
            if key.startswith('vi_'):
                del st.session_state[key]
        st.rerun()

    def get_vi_llm_client():
        from openai import OpenAI
        from virtual_interview.config import API_CONFIG
        return OpenAI(api_key=API_CONFIG["api_key"], base_url=API_CONFIG["base_url"])

    def call_vi_llm(messages: list, max_tokens: int = 400) -> str:
        from virtual_interview.config import API_CONFIG
        client = get_vi_llm_client()
        response = client.chat.completions.create(
            model=API_CONFIG["model"],
            max_tokens=max_tokens,
            messages=messages
        )
        if hasattr(response, 'choices') and response.choices:
            return response.choices[0].message.content or str(response)
        return str(response)

    def extract_vi_skills(jd_text: str):
        """Extract skills from job description using the app's existing extraction logic."""
        try:
            # Use the same extraction logic as the rest of the app
            from src import extract_skills_from_jd, extract_skills_fallback

            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key and "your-api-key" not in api_key:
                skills_result = extract_skills_from_jd(jd_text)
            else:
                skills_result = extract_skills_fallback(jd_text)

            # Convert to VI format: list of {"name": ..., "type": ...}
            skills = []

            # Add must_have skills as "conceptual" type
            for skill_name in skills_result.get("must_have", []):
                skills.append({"name": skill_name, "type": "conceptual"})

            # Add nice_to_have skills
            for skill_name in skills_result.get("nice_to_have", []):
                skills.append({"name": skill_name, "type": "conceptual"})

            # Detect job role from seniority signals or defaults
            seniority = skills_result.get("seniority_signals", [])
            if seniority:
                st.session_state.vi_job_role = seniority[0] if seniority else "Software Engineer"
            else:
                st.session_state.vi_job_role = "Software Engineer"

            return skills if skills else [{"name": "Programming", "type": "coding"}]

        except Exception as e:
            # Fallback to basic keyword extraction
            skills = []
            tech_keywords = ["python", "java", "javascript", "docker", "kubernetes", "aws", "react", "node", "sql", "machine learning", "tensorflow", "pytorch", "git", "ci/cd", "agile"]
            for kw in tech_keywords:
                if kw.lower() in jd_text.lower():
                    t = "coding" if kw in ["python", "java", "javascript"] else "tool"
                    skills.append({"name": kw.title(), "type": t})
            st.session_state.vi_job_role = "Software Engineer"
            return skills[:10] or [{"name": "Programming", "type": "coding"}]

    def generate_vi_question(skill_name: str, skill_type: str, diff: int):
        """Generate interview question."""
        try:
            diff_labels = {1: "beginner", 2: "easy", 3: "medium", 4: "hard", 5: "expert"}
            difficulty = diff_labels.get(diff, "medium")
            job_role = st.session_state.vi_job_role

            if skill_type == "coding":
                prompt = f"""Generate a {difficulty} level coding problem for a {job_role} position using {skill_name}.
Return JSON: {{"question": "specific problem", "input": "example input", "output": "expected output", "hints": ["hint"]}}"""
            else:
                prompt = f"""Generate a {difficulty} interview question about {skill_name} for a {job_role} position.
Return JSON: {{"question": "[scenario-based question]", "hints": ["hint"]}}"""

            text = call_vi_llm([{"role": "user", "content": prompt}], max_tokens=500)
            text = text.strip()
            if '{' in text:
                start = text.find('{')
                end = text.rfind('}') + 1
                if end > start:
                    return json.loads(text[start:end])
        except:
            pass
        return {"question": f"Explain {skill_name} and its importance in {st.session_state.vi_job_role} role", "hints": ["Focus on practical applications"]}

    def evaluate_vi_answer(skill: str, question: str, answer: str) -> dict:
        """Evaluate interview answer."""
        import re
        try:
            prompt = f"""Evaluate this answer for the question:
Question: {question}
Answer: {answer}

Return JSON with score (0-100), correct (true/false), and feedback:
{{"score": number, "correct": true/false, "feedback": "explanation"}}"""

            response = call_vi_llm([{"role": "user", "content": prompt}], max_tokens=400)
            response_lower = response.lower()

            # Extract score
            score = 50
            for pattern in [r'"score"\s*:\s*(\d+)', r'score[:\s]+(\d+)', r'(\d+)\s*/\s*100']:
                match = re.search(pattern, response_lower)
                if match:
                    score = int(match.group(1))
                    break

            correct = 'correct: true' in response_lower or '"correct": true' in response_lower
            correctness = score / 100.0

            return {
                "correctness": correctness,
                "clarity": correctness,
                "correct": correct,
                "depth": "high" if correctness > 0.75 else "medium" if correctness > 0.5 else "low",
                "feedback": response,
                "strengths": ["Good answer"] if correctness >= 0.5 else [],
                "gaps": ["Needs more detail"] if correctness < 0.7 else []
            }
        except Exception as e:
            return {"correctness": 0.5, "clarity": 0.5, "correct": False, "depth": "medium", "feedback": str(e), "strengths": [], "gaps": []}

    # ===== VI PHASE 1: JD Upload =====
    if st.session_state.vi_phase == 'start':
        st.markdown("### 📄 Step 1: Upload Job Description (or enter skills manually)")
        jd_input = st.text_area("Job Description", height=150, placeholder="Paste job description...", key="vi_jd_input")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Extract Skills", type="primary", disabled=not jd_input):
                with st.spinner("Analyzing..."):
                    skills = extract_vi_skills(jd_input)
                    st.session_state.vi_skills = skills
                    st.session_state.vi_phase = 'skills'
                    st.rerun()
        with col2:
            st.markdown("**Or enter manually:**")
            manual = st.text_input("Skills (comma-separated)", placeholder="Python, Docker, AWS", key="vi_manual")
            if st.button("Use Manual Skills") and manual:
                skills = [{"name": s.strip(), "type": "conceptual"} for s in manual.split(",") if s.strip()]
                st.session_state.vi_skills = skills
                st.session_state.vi_phase = 'skills'
                st.rerun()

    # ===== VI PHASE 2: Select Skills =====
    elif st.session_state.vi_phase == 'skills':
        st.markdown("### ✅ Extracted Skills")
        st.markdown(f"**🎯 Position:** {st.session_state.vi_job_role}")

        if not st.session_state.vi_skills:
            st.warning("No skills extracted.")
            if st.button("← Go Back"):
                st.session_state.vi_phase = 'start'
                st.rerun()

        selected = []
        for s in st.session_state.vi_skills:
            if st.checkbox(f"{s['name']} ({s.get('type', 'conceptual')})", value=True):
                selected.append(s)
                if s['name'] not in st.session_state.vi_skill_scores:
                    st.session_state.vi_skill_scores[s['name']] = {'correct': 0, 'total': 0}
                if s['name'] not in st.session_state.vi_difficulty:
                    st.session_state.vi_difficulty[s['name']] = 3

        if selected and st.button(f"🎯 Start Interview ({len(selected)} skills)", type="primary"):
            st.session_state.vi_selected_skills = selected
            st.session_state.vi_current_skill_idx = 0
            st.session_state.vi_current_skill = selected[0]
            st.session_state.vi_phase = 'interview'
            st.rerun()
        elif not selected:
            st.warning("Select at least one skill.")

    # ===== VI PHASE 3: Interview =====
    elif st.session_state.vi_phase == 'interview':
        skill = st.session_state.vi_current_skill
        skill_name = skill['name']
        skill_type = skill.get('type', 'conceptual')
        diff = st.session_state.vi_difficulty.get(skill_name, 3)
        diff_stars = "⭐" * diff

        total_skills = len(st.session_state.vi_selected_skills)
        current_idx = st.session_state.vi_current_skill_idx

        st.markdown(f"### 🎯 {skill_name}")
        st.markdown(f"**Type:** {skill_type} | **Difficulty:** {diff_stars}")
        st.progress((current_idx + 1) / total_skills, text=f"Skill {current_idx + 1}/{total_skills}")

        if not st.session_state.vi_question:
            with st.spinner("Generating question..."):
                st.session_state.vi_question = generate_vi_question(skill_name, skill_type, diff)

        q_data = st.session_state.vi_question
        st.markdown(f'<div class="vi-question-box"><b>❓ Question:</b><br>{q_data.get("question", "Loading...")}</div>', unsafe_allow_html=True)

        if q_data.get("input"):
            st.markdown(f"**📥 Input:** `{q_data.get('input')}`")
        if q_data.get("output"):
            st.markdown(f"**📤 Output:** `{q_data.get('output')}`")

        answer = st.text_area("Your Answer:", height=120, key=f"vi_answer_{skill_name}")

        col1, col2, col3 = st.columns(3)
        with col1:
            submit = st.button("📤 Submit", type="primary", disabled=not answer)
        with col2:
            hint = st.button("💡 Get Hint")
        with col3:
            pass

        if hint and q_data.get("hints"):
            st.info(f"💡 **Hint:** {q_data['hints'][0] if q_data['hints'] else 'Think about the core concept.'}")

        if submit and answer:
            with st.spinner("Evaluating..."):
                ev = evaluate_vi_answer(skill_name, q_data.get("question", ""), answer)
                st.session_state.vi_evaluation = ev
                st.session_state.vi_eval_done = True
                st.session_state.vi_answers.append({'skill': skill_name, 'answer': answer, 'eval': ev})

                st.session_state.vi_skill_scores[skill_name]['total'] += 1
                if ev.get('correctness', 0) >= 0.6:
                    st.session_state.vi_skill_scores[skill_name]['correct'] += 1

                if ev.get('correctness', 0) >= 0.8:
                    st.session_state.vi_difficulty[skill_name] = min(5, diff + 1)
                elif ev.get('correctness', 0) < 0.4:
                    st.session_state.vi_difficulty[skill_name] = max(1, diff - 1)

                st.rerun()

        if st.session_state.vi_eval_done:
            ev = st.session_state.vi_evaluation
            depth = ev.get('depth', 'medium')

            st.markdown("---")
            st.markdown("### 📊 Evaluation")
            cols = st.columns(3)
            cols[0].metric("✅ Correctness", f"{ev.get('correctness', 0):.0%}")
            cols[1].metric("📝 Clarity", f"{ev.get('clarity', 0):.0%}")
            cols[2].metric("🔍 Depth", f"{'🟢' if depth=='high' else '🟡' if depth=='medium' else '🔴'} {depth.upper()}")

            feedback_text = ev.get('feedback', '')
            try:
                if '{' in feedback_text:
                    fb_json = json.loads(feedback_text)
                    feedback_text = fb_json.get('feedback', feedback_text)
            except:
                pass
            st.markdown(f"**Feedback:** {feedback_text}")

            if ev.get('strengths'):
                st.success("✅ " + ", ".join(ev['strengths'][:2]))
            if ev.get('gaps'):
                st.error("❌ " + ", ".join(ev['gaps'][:2]))

            st.markdown("---")
            next_idx = st.session_state.vi_current_skill_idx + 1
            if st.button("➡️ Next Skill", type="secondary"):
                if next_idx >= len(st.session_state.vi_selected_skills):
                    st.session_state.vi_phase = 'results'
                else:
                    st.session_state.vi_current_skill_idx = next_idx
                    st.session_state.vi_current_skill = st.session_state.vi_selected_skills[next_idx]
                st.session_state.vi_question = None
                st.session_state.vi_eval_done = False
                st.rerun()

    # ===== VI PHASE 4: Results =====
    elif st.session_state.vi_phase == 'results':
        st.markdown("## 🎉 Interview Complete!")
        total_correct = sum(s['correct'] for s in st.session_state.vi_skill_scores.values())
        total_q = sum(s['total'] for s in st.session_state.vi_skill_scores.values())
        overall = (total_correct / total_q * 100) if total_q > 0 else 0

        st.markdown("### 📊 Final Score Breakdown")
        cols = st.columns(4)
        cols[0].metric("🎯 Overall", f"{overall:.0f}%")
        cols[1].metric("📝 Questions", total_q)
        cols[2].metric("✅ Correct", total_correct)
        cols[3].metric("❌ Incorrect", total_q - total_correct)

        st.markdown("### 🔍 Per-Skill Breakdown")
        for skill in st.session_state.vi_selected_skills:
            name = skill['name']
            scores = st.session_state.vi_skill_scores.get(name, {'correct': 0, 'total': 1})
            acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
            diff = st.session_state.vi_difficulty.get(name, 3)

            if acc >= 0.8 and diff >= 4:
                level, color = "✅ Expert", "success"
            elif acc >= 0.6:
                level, color = "⚠️ Proficient", "warning"
            elif acc >= 0.4:
                level, color = "🔴 Developing", "info"
            else:
                level, color = "❌ Needs Training", "error"

            msg = f"**{name}**: {level} ({acc:.0%}, ⭐{diff})"
            if color == "success":
                st.success(msg)
            elif color == "warning":
                st.warning(msg)
            else:
                st.error(msg)

        # Final recommendation
        st.markdown("### 🏆 Final Assessment")
        if overall >= 75:
            st.success("## ✅ STRONG CANDIDATE")
        elif overall >= 55:
            st.warning("## ⚠️ CONDITIONALLY RECOMMENDED")
        else:
            st.error("## ❌ NEEDS MORE TRAINING")

        # Download report
        report = {
            "overall_score": round(overall, 1),
            "recommendation": "Highly Recommended" if overall >= 75 else "Conditionally Recommended" if overall >= 55 else "Not Recommended",
            "skills": st.session_state.vi_skill_scores,
            "difficulties": st.session_state.vi_difficulty,
            "answers": st.session_state.vi_answers
        }
        st.download_button("📥 Download Interview Report", json.dumps(report, indent=2), "interview_report.json")

        if st.button("🔄 New Interview"):
            reset_vi()


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
        "🎤 Virtual Interview",
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
        tab_virtual_interview()


if __name__ == "__main__":
    main()
