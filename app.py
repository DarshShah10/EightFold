"""
EightFold Talent Intelligence - Entry Point
==========================================
Techkriti '26 × EightFold AI — Impact Area 01: Signal Extraction & Verification

Run this file with Streamlit:
    cd C:\Darsh\Techkriti\Resume_Parser\EightFold
    streamlit run app.py

Or directly:
    streamlit run unified_app.py
"""

import subprocess
import sys
import os

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

if __name__ == "__main__":
    # Check for critical imports before starting Streamlit
    missing = []
    try:
        import streamlit
    except ImportError:
        missing.append("streamlit")

    if missing:
        print("ERROR: Missing required packages.")
        print(f"Install with: pip install -r FINAL_REQUIREMENTS.txt")
        print(f"Missing: {', '.join(missing)}")
        sys.exit(1)

    # Launch the unified app
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", "unified_app.py",
                               "--browser.gatherUsageStats", "false"]))
