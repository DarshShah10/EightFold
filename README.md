# EightFold Talent Intelligence Platform

## 🧠 Overview

EightFold Talent Intelligence combines:
- **Resume Parsing & Skill Extraction** — Analyze resumes and extract candidate skills
- **GitHub Signal Extraction** — Deep behavioral analysis from GitHub profiles
- **Adaptive Candidate Scoring** — Match candidates to job descriptions with context-aware weights
- **Virtual Interview Engine** — Adaptive micro-assessment for interviewing candidates
- **Explainability** — Evidence chains and reasoning traces for transparent decisions

## 🎯 Features

| Tab | Description |
|-----|-------------|
| 📋 JD Analysis | Context detection + skill extraction from job descriptions |
| 👥 Candidates | Deep profile generation from GitHub handles |
| 📊 Scoring Results | Adaptive scoring with gap analysis |
| 🔍 Explainability | Evidence chains + reasoning traces |
| 🎤 Virtual Interview | Adaptive micro-assessment engine |

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
# Clone/download the project
cd EightFold

# Install all dependencies
pip install -r requirements.txt

# Or use the setup script
python setup_env.py --full
```

### 2. Get GitHub Token (Recommended)

The harvester works WITHOUT a token (rate limited to 60 requests/hour), but for the hackathon you'll want a token (5000 requests/hour).

**Get a token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: `talent-intelligence`
4. Scopes: `repo`, `read:user`, `read:org`
5. Generate and COPY the token

**Set the token:**

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

**Windows (CMD):**
```cmd
set GITHUB_TOKEN=ghp_your_token_here
```

**Linux/Mac:**
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Permanent (add to your shell config):**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 📖 How to Run

### Quick Test (with default user gvanrossum)
```bash
python run_harvester.py
```

### Test with a specific GitHub handle
```bash
python run_harvester.py gvanrossum
```

### Run with custom output directory
```bash
python run_harvester.py gvanrossum my_data
```

### Test Environment Setup
```bash
# Check setup
python setup_env.py

# Test GitHub connection
python setup_env.py --test

# Full setup (install + test)
python setup_env.py --full
```

---

## 📁 Project Structure

```
EightFold/
├── modules/                  # Core modules for candidate analysis
│   ├── harvester.py         # Data collector for GitHub profiles
│   ├── candidate_profile.py # Candidate profile generation
│   └── ...
├── src/                     # Source modules for skill analysis
│   ├── pdf_resume_parser.py # Resume parsing
│   ├── scoring_engine.py    # Adaptive scoring
│   └── ...
├── virtual_interview/        # Virtual Interview Engine
│   ├── app.py               # Streamlit UI for interviews
│   ├── main.py              # CLI entry point
│   ├── config.py             # Configuration
│   ├── core/                # Core interview logic
│   │   ├── question_generator.py
│   │   ├── evaluator.py
│   │   ├── feedback_generator.py
│   │   └── ...
│   ├── components/          # UI components
│   ├── rubrics/             # Assessment rubrics
│   └── services/            # TTS, voice input services
├── unified_app.py           # Main unified Streamlit app (5 tabs)
├── app.py                   # Entry point
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🔧 Using the Harvester in Your Code

```python
from modules.harvester import harvest

# Harvest data for a GitHub user
result = harvest("github_handle")

# Access the data
print(result["user"])           # User metadata
print(result["repos"])          # Repository list
print(result["commits"])        # Commit history with deep metrics
print(result["pull_requests"])  # PR behavior
print(result["aggregates"])     # Computed metrics
```

---

## 📊 What Data is Collected

| Category | Data Points |
|----------|-------------|
| **User** | name, bio, location, followers, following, public repos |
| **Repos** | all repos with stars, forks, size, topics, structure signals |
| **Languages** | bytes per language (volume-weighted, not just presence) |
| **Commits** | 30 per repo = ~300 total with patches, churn, complexity |
| **PRs** | 15 per repo = ~150 total with merge time, review engagement |
| **Reviews** | code review behavior from top 5 repos |
| **Issues** | participation patterns, resolution time |
| **Comments** | communication quality, technical depth |
| **Events** | 200 contribution events for activity patterns |
| **Starred** | interests and exploration patterns |
| **Gists** | snippet sharing behavior |
| **Orgs** | team collaboration patterns |
| **Dependencies** | requirements.txt, package.json, Cargo.toml, etc. |
| **Branches** | branching strategy signals |
| **Releases** | release engineering discipline |

---

## ⚡ Rate Limits

| Auth Method | Requests/Hour | Notes |
|-------------|---------------|-------|
| No token | 60 | Works but limited |
| With token | 5000 | Full speed, recommended |
| Authenticated + GraphQL | 5000 | (Future enhancement) |

---

## 🐛 Troubleshooting

**Error: "Could not find user"**
- Check the GitHub handle is correct
- Make sure the user exists and has public repos

**Error: "Rate limit exceeded"**
- Set your GITHUB_TOKEN (see above)
- Wait for the rate limit to reset (usually 1 hour)

**Error: "Module not found"**
- Run `pip install -r requirements.txt`
- Make sure you're in the project root directory

**Empty data results**
- User might have no public repositories
- User might have all forks (forks are excluded)

---

## 🎯 Next Steps (After Harvester Works)

1. ✅ Harvester is done
2. ⬜ Module 4: Dependency Fingerprinting
3. ⬜ Module 5: Learning Velocity Calculator
4. ⬜ Main orchestrator (candidate_profile.json)
5. ⬜ Integration with P2 (JD matching)
6. ⬜ Integration with P3 (explanation layer)
