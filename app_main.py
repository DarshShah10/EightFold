"""
EightFold Talent Intelligence - Main Entry Point
================================================
Techkriti '26 x EightFold AI

Simple 2-tab interface:
  1. Main - JD Analysis + Candidates + Scoring + Explainability (auto-flow)
  2. Interview - Adaptive Virtual Interview

Run with: streamlit run app_main.py
"""

import os
import streamlit as st

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Page config
st.set_page_config(
    page_title="EightFold Talent Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS - Modern dark theme
st.markdown("""
<style>
    /* Main theme */
    .stApp { background: #0e1117; }

    /* Headers */
    .main-title { font-size: 2.5rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem; text-align: center; }
    .sub-title { font-size: 1.1rem; color: #8b949e; margin-bottom: 2rem; text-align: center; }

    /* Cards */
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1.5rem; margin: 0.5rem 0; }
    .card-header { color: #58a6ff; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; }

    /* Metrics */
    .metric-label { color: #8b949e; font-size: 0.85rem; }
    .metric-value { font-size: 1.8rem; font-weight: 700; }

    /* Scores */
    .score-excellent { color: #3fb950; }
    .score-good { color: #58a6ff; }
    .score-moderate { color: #d29922; }
    .score-weak { color: #f85149; }

    /* Input styling */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: #161b22; padding: 8px; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 12px 24px; border-radius: 6px; color: #8b949e; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #238636 !important; }

    /* Buttons */
    .stButton > button { background: #238636; color: white; border: none; border-radius: 6px; }
    .stButton > button:hover { background: #2ea043; }

    /* Expander */
    .streamlit-expanderHeader { background: #161b22; border-radius: 8px; }

    /* Progress bar */
    .stProgress > div > div { background: #238636; }

    /* Spinner */
    .stSpinner > div { border-color: #238636 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🧠 EightFold Talent Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Techkriti \'26 × EightFold AI — Signal Extraction & Verification</p>', unsafe_allow_html=True)

# ─── Check imports ─────────────────────────────────────────────────────────────
try:
    from integrator import TalentIntelligenceIntegrator, analyze, analyze_batch
    from src import JDContextAnalyzer, AdaptiveScoringEngine
    INTEGRATOR_OK = True
except ImportError as e:
    INTEGRATOR_OK = False
    IMPORT_ERROR = str(e)

if not INTEGRATOR_OK:
    st.error(f"Failed to import modules: {IMPORT_ERROR}")
    st.info("Run: `pip install -r requirements.txt`")
    st.stop()

# ─── Main Tabs ────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs([
    "📊 Main",
    "🎤 Interview"
])

with tab1:
    from main_tab import render_main_tab
    render_main_tab()

with tab2:
    from interview_tab import render_interview_tab
    render_interview_tab()
