"""
Main Tab - Unified JD Analysis + Candidates + Scoring + Explainability
====================================================================
Streamlined flow: JD + GitHub → Analyze → Score → Explain
"""

import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from integrator import analyze_batch
from src import JDContextAnalyzer, extract_skills_from_jd, extract_skills_fallback

# ─── Helper Functions ───────────────────────────────────────────────────────────

def get_score_color(score: float) -> str:
    if score >= 0.75: return "#3fb950"
    elif score >= 0.60: return "#58a6ff"
    elif score >= 0.45: return "#d29922"
    return "#f85149"


def get_recommendation_emoji(recommendation: str) -> str:
    return {"STRONG HIRE": "🟢", "CONSIDER": "🟡", "MAYBE": "🟠", "PASS": "🔴"}.get(recommendation, "⚪")


def render_signal_bars(signals: dict):
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
    colors_list = ["#58a6ff", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

    fig = go.Figure()
    for i, (key, val) in enumerate(signals.items()):
        if key in signal_names and isinstance(val, (int, float)):
            fig.add_trace(go.Bar(
                y=[signal_names[key]],
                x=[val],
                orientation='h',
                marker_color=get_score_color(val),
                text=[f"{val:.0%}"],
                textposition='inside',
                insidetextanchor='start',
                textfont=dict(color='white', size=12),
                hovertemplate=f"<b>{signal_names[key]}</b>: {val:.1%}<extra></extra>",
            ))

    fig.update_layout(
        height=max(200, len([k for k in signals if k in signal_names]) * 50),
        margin=dict(l=140, r=20, t=10, b=10),
        xaxis=dict(range=[0, 1], tickformat=".0%", title=""),
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_main_tab():
    """Render the main tab with streamlined flow."""

    # ─── Session State ─────────────────────────────────────────────────────────
    st.session_state.setdefault('main_jd', '')
    st.session_state.setdefault('main_handles', '')
    st.session_state.setdefault('main_results', None)
    st.session_state.setdefault('main_step', 0)  # 0=input, 1=results

    # ─── Input Section ──────────────────────────────────────────────────────────
    if st.session_state.main_step == 0:
        st.markdown("### 📝 Enter Job Description & Candidates")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)

            # Job Description
            jd_text = st.text_area(
                "Job Description",
                height=150,
                placeholder="Paste the job description here...\n\nExample: 'We are looking for a Senior ML Engineer with Python, TensorFlow, and AWS experience...'",
                key="main_jd_input"
            )

            # GitHub Handles
            handles_text = st.text_area(
                "GitHub Handles (one per line)",
                height=100,
                placeholder="Enter GitHub handles...\ne.g.:\ngvanrossum\ntwisted",
                key="main_handles_input"
            )

            st.markdown('</div>', unsafe_allow_html=True)

            # Options
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                github_token = st.text_input("GitHub Token (optional)", type="password", placeholder="ghp_...")
            with col2:
                use_llm = st.checkbox("🧠 LLM Extraction", value=True)
            with col3:
                force_refresh = st.checkbox("🔄 Force Refresh")

            # Analyze Button
            if st.button("🚀 Analyze Candidates", type="primary", use_container_width=True):
                if len(jd_text.strip()) < 50:
                    st.warning("Please enter a longer job description (at least 50 characters)")
                    return
                if not handles_text.strip():
                    st.warning("Please enter at least one GitHub handle")
                    return

                with st.spinner("Analyzing candidates..."):
                    handles = [h.strip() for h in handles_text.strip().split("\n") if h.strip()]
                    token = github_token or os.environ.get("GITHUB_TOKEN")

                    try:
                        results = analyze_batch(handles, jd_text, github_token=token, force_refresh=force_refresh)
                        st.session_state.main_results = results
                        st.session_state.main_jd = jd_text
                        st.session_state.main_handles = handles_text
                        st.session_state.main_step = 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

    # ─── Results Section ────────────────────────────────────────────────────────
    else:
        # Back button
        if st.button("← New Analysis"):
            st.session_state.main_step = 0
            st.session_state.main_results = None
            st.rerun()

        st.markdown("---")
        st.markdown("## 📊 Analysis Results")

        results = st.session_state.main_results

        if not results:
            st.warning("No results to display")
            return

        # ─── Summary Cards ──────────────────────────────────────────────────────
        st.markdown("### 🏆 Candidate Rankings")

        for i, result in enumerate(results):
            ranking = result.get("ranking", i + 1)
            handle = result.get("candidate", {}).get("github_handle", "unknown")
            scoring = result.get("scoring", {})
            unified = result.get("unified_recommendation", {})
            recommendation = unified.get("recommendation", scoring.get("hiring_recommendation", "UNKNOWN"))
            score = scoring.get("match_score", 0)
            color = get_score_color(score)
            badge = get_recommendation_emoji(recommendation)

            with st.container():
                st.markdown(f'<div class="card">', unsafe_allow_html=True)

                # Header
                col_header = st.columns([3, 1, 1])
                with col_header[0]:
                    st.markdown(f"### {badge} #{ranking} — **{handle}**")
                with col_header[1]:
                    st.markdown(f'<p class="metric-label">Match Score</p><p class="metric-value" style="color:{color}">{score:.0%}</p>', unsafe_allow_html=True)
                with col_header[2]:
                    st.markdown(f'<p class="metric-label">Recommendation</p><p class="metric-value">{recommendation}</p>', unsafe_allow_html=True)

                # Quick metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    gap = scoring.get("gap_analysis", {})
                    matched = len(gap.get("matched_skills", []))
                    st.metric("✅ Matched", matched)
                with col_m2:
                    missing = len(gap.get("missing_skills", []))
                    st.metric("❌ Missing", missing)
                with col_m3:
                    industry = scoring.get("jd_context", {}).get("detected_industry", "—").replace("_", " ").title()
                    st.metric("🏭 Industry", industry[:15])
                with col_m4:
                    time_prod = gap.get("time_to_productivity", "—")
                    st.metric("⏱️ Time to Productivity", time_prod)

                # ─── OVERALL MATCH (BIG) ────────────────────────────────────────────
                st.markdown(f"## 🏅 Overall Match: <span style='color:{color}; font-size:2rem; font-weight:700;'>{score:.1%}</span>", unsafe_allow_html=True)

                # ─── REASONING CHAIN ──────────────────────────────────────────────
                reasoning = scoring.get("reasoning", "")
                if reasoning:
                    st.markdown("### 🧩 Reasoning Chain")
                    st.info(f"💡 {reasoning}")

                # ─── SKILL EVIDENCE CHAINS ─────────────────────────────────────────
                st.markdown("### 🔗 Skill Evidence Chains (Source Tracking)")
                explainability = result.get("explainability", {})
                reasoning_chains = explainability.get("reasoning_chains", [])
                si = result.get("skill_intelligence", {})

                if reasoning_chains:
                    for chain in reasoning_chains:
                        skill = chain.get("skill", "")
                        chain_type = chain.get("type", "unknown")
                        conf = chain.get("confidence", 0)
                        evidence_summary = chain.get("evidence_summary", "")
                        reasoning_text = chain.get("reasoning", "")
                        github_links = chain.get("github_links", [])
                        commits = chain.get("commits", [])

                        icon = "✅" if chain_type in ("language", "matched") else "🔶" if chain_type == "adjacent" else "❌"

                        with st.expander(f"{icon} **{skill}** — {evidence_summary} (confidence: {conf:.0%})"):
                            if reasoning_text:
                                st.markdown(f"**Why we believe this:** {reasoning_text}")

                            if github_links:
                                st.markdown("**📦 Repositories providing evidence:**")
                                for link in github_links:
                                    url = link.get("url", "")
                                    label = link.get("label", "")
                                    desc = link.get("desc", "")
                                    stars = link.get("stars", 0)
                                    if url and label:
                                        st.markdown(
                                            f"- [{label}]({url}) {'⭐' + str(stars) if stars else ''} "
                                            f"{f'— {desc[:80]}' if desc else ''}"
                                        )

                            if commits:
                                st.markdown("**💻 Commits showing this skill:**")
                                for commit in commits[:3]:
                                    url = commit.get("url", "")
                                    sha = commit.get("sha", "")
                                    msg = commit.get("message", "")
                                    repo = commit.get("repo", "")
                                    if url:
                                        st.markdown(f"- [`{sha}`]({url}) in *{repo}* — {msg[:80]}")
                                    elif sha:
                                        st.markdown(f"- `{sha}` in *{repo}* — {msg[:80]}")

                            st.markdown(f"**Confidence:** {conf:.0%}")
                elif si.get("project_evidence"):
                    # Fallback: show project evidence
                    for proj in si.get("project_evidence", []):
                        repo = proj.get("full_name", proj.get("name", ""))
                        stars = proj.get("stars", 0)
                        skills = proj.get("skills_demonstrated", [])
                        why = proj.get("why_it_matters", "")
                        desc = proj.get("description", "")
                        gh_url = f"https://github.com/{repo}" if repo else "#"
                        st.markdown(f"✅ **[{repo}]({gh_url})** ⭐{stars}")
                        if skills:
                            st.markdown(f"   Skills: `{', '.join(skills)}`")
                        if why:
                            st.markdown(f"   📌 {why}")
                        if desc:
                            st.markdown(f"   _{desc[:100]}_")
                else:
                    st.info("No evidence chains available. Try scoring with a cached GitHub handle.")

                # ─── SIGNAL BREAKDOWN ─────────────────────────────────────────────
                st.markdown("### 📊 Signal Breakdown")
                signals = scoring.get("signal_breakdown", {})
                if signals:
                    render_signal_bars(signals)
                else:
                    st.info("No signal data available")

                # ─── GAP ANALYSIS ──────────────────────────────────────────────────
                gap = scoring.get("gap_analysis", {})
                matched_g = gap.get("matched_skills", [])
                missing_g = gap.get("missing_skills", [])
                adjacent_g = gap.get("adjacent_skills", [])

                with st.expander("### 🔍 Gap Analysis"):
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        if matched_g:
                            st.markdown("**✅ Matched Skills**")
                            for m in matched_g[:8]:
                                skill_name = m.get('skill', m)
                                st.markdown(f"- `{skill_name}`")
                    with col_g2:
                        if missing_g:
                            st.markdown("**❌ Missing Skills**")
                            for m in missing_g[:6]:
                                lt = m.get("learning_time", "—")
                                st.markdown(f"- `{m.get('skill', m)}` — {lt}")

                    if adjacent_g:
                        st.markdown("**🔶 Adjacent Skills**")
                        for a in adjacent_g[:4]:
                            st.markdown(f"- `{a.get('required', '')}` ← has `{a.get('candidate_has', '')}`")

                    gap_sum = gap.get("gap_summary", "")
                    if gap_sum:
                        st.info(f"📝 {gap_sum}")

                # ─── JD CONTEXT ───────────────────────────────────────────────────
                st.markdown("### 🎯 JD Context & Weight Rationale")
                jd_ctx = scoring.get("jd_context", {})
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    st.metric("🏭 Industry", jd_ctx.get("detected_industry", "—").replace("_", " ").title())
                with col_e2:
                    st.metric("📊 Seniority", jd_ctx.get("detected_seniority", "—").replace("_", " ").title())
                with col_e3:
                    st.metric("💼 Role Type", jd_ctx.get("detected_role_type", "—").replace("_", " ").title())
                st.markdown(f"**Explanation:** {jd_ctx.get('weight_explanation', '')}")

                # Adaptive weights
                weights = scoring.get("adaptive_weights", {})
                if weights:
                    with st.expander("⚖️ Adaptive Weights Applied"):
                        for w_key, w_val in weights.items():
                            label = w_key.replace("_", " ").title()
                            color_bar = "#3fb950" if w_val >= 0.25 else "#d29922" if w_val >= 0.15 else "#8b949e"
                            st.markdown(
                                f"<div style='display:flex;align-items:center;margin:4px 0;'>"
                                f"<div style='width:{w_val*100:.0f}%;background:{color_bar};opacity:0.8;height:10px;border-radius:4px;'></div>"
                                f"<span style='margin-left:8px;font-weight:600;'>{label}: {w_val:.0%}</span></div>",
                                unsafe_allow_html=True
                            )

                # ─── COMMIT INTELLIGENCE CITATIONS ──────────────────────────────────
                ci = result.get("commit_intelligence", {})
                if ci.get("score", 0) > 0:
                    st.markdown("### 🏆 Commit Intelligence Citations")
                    citations = ci.get("citations", [])
                    if citations:
                        for j, cit in enumerate(citations[:5]):
                            cit_text = cit.get("title", cit.get("text", str(cit)))
                            cit_type = cit.get("category", "")
                            emoji = "⭐" if "star" in str(cit_type).lower() else "🔧" if "fix" in str(cit_type).lower() else "📝"
                            st.markdown(f"{emoji} *{cit_text}*")
                    else:
                        st.info("No commit citations available")

                # ─── CROSS-VALIDATION ──────────────────────────────────────────────
                cv = result.get("cross_validation", {})
                if cv and cv.get("validation_result"):
                    st.markdown("### 🔏 Resume vs GitHub Verification")
                    vr = cv["validation_result"]
                    st.markdown(f"**Authenticity:** {vr.get('authenticity_rating', 'Unknown')}")
                    st.markdown(f"**Verified:** {vr.get('verified_skills', 0)}/{vr.get('total_skills_claimed', 0)} skills")
                else:
                    st.caption("💡 Provide a PDF resume to enable Resume vs GitHub verification")

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")

        # ─── Comparison Chart ────────────────────────────────────────────────────
        if len(results) > 1:
            st.markdown("### 📈 Score Comparison")

            fig = go.Figure()
            for i, result in enumerate(results):
                handle = result.get("candidate", {}).get("github_handle", f"Candidate {i+1}")
                score = result.get("scoring", {}).get("match_score", 0)

                fig.add_trace(go.Bar(
                    name=handle,
                    x=["Match Score"],
                    y=[score],
                    text=[f"{score:.0%}"],
                    textposition='outside',
                    marker_color=get_score_color(score),
                ))

            fig.update_layout(
                barmode='group',
                yaxis_tickformat=".0%",
                height=250,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.1),
                margin=dict(l=40, r=20, t=20, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        # ─── Download Report ─────────────────────────────────────────────────────
        st.markdown("### 📥 Export")
        import json
        report = {
            "jd": st.session_state.main_jd,
            "candidates": [
                {
                    "handle": r.get("candidate", {}).get("github_handle"),
                    "score": r.get("scoring", {}).get("match_score", 0),
                    "recommendation": r.get("unified_recommendation", {}).get("recommendation", ""),
                }
                for r in results
            ]
        }
        st.download_button("📥 Download Report", json.dumps(report, indent=2), "talent_report.json", mime="application/json")
