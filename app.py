"""
EightFold Talent Intelligence - Entry Point
==========================================
Techkriti '26 × EightFold AI

Simple 2-tab interface:
  1. Main - JD Analysis + Candidates + Scoring (auto-flow)
  2. Interview - Adaptive Virtual Interview

Run with:
    streamlit run app.py

Or directly:
    streamlit run app_main.py
"""

import subprocess
import sys
import os

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

if __name__ == "__main__":
    # Check for streamlit
    try:
        import streamlit
    except ImportError:
        print("ERROR: streamlit not installed.")
        print("Install with: pip install streamlit")
        sys.exit(1)

    # Launch the main app
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", "app_main.py",
                               "--browser.gatherUsageStats", "false"]))
