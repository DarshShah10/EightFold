"""
Adaptive Virtual Interview Engine
==================================
- Upload Job Description to extract skills
- Micro-assessments per skill
- Code editor for technical questions
- Adaptive difficulty based on performance
"""

import streamlit as st
import json
import os
from virtual_interview.components.code_editor import render_code_editor

# Note: st.set_page_config() is already called in unified_app.py - do not call again here

# Initialize session state
def init_state():
    defaults = {
        'phase': 'start',
        'skills': [],
        'selected_skills': [],
        'current_skill_idx': 0,
        'current_skill': None,
        'question': None,
        'eval_done': False,
        'evaluation': None,
        'skill_scores': {},
        'difficulty': {},
        'history': [],
        'answers': []
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# CSS - Enhanced code editor styling
st.markdown("""
<style>
.stApp { background: #0e1117; }
.question-box { background: #1e1e1e; color: #fff; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; margin: 10px 0; }
.result-box { background: #2d2d2d; padding: 15px; border-radius: 10px; margin: 10px 0; }
.stTextArea textarea { 
    background-color: #1e1e1e !important; 
    color: #00ff00 !important; 
    font-family: 'Courier New', monospace !important;
    font-size: 14px !important;
    border: 1px solid #333 !important;
}
.io-box { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 8px; margin: 5px 0; font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

def reset():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ============ LLM Functions (OpenAI-compatible with Claude model) ============
def get_llm_client():
    from openai import OpenAI
    from config import API_CONFIG
    return OpenAI(
        api_key=API_CONFIG["api_key"],
        base_url=API_CONFIG["base_url"]
    )

def call_claude(messages: list, max_tokens: int = 400) -> str:
    """Call Claude Opus via OpenAI-compatible API and return response text."""
    from config import API_CONFIG
    client = get_llm_client()
    
    response = client.chat.completions.create(
        model=API_CONFIG["model"],
        max_tokens=max_tokens,
        messages=messages
    )
    # Handle different response formats
    if hasattr(response, 'choices') and response.choices and response.choices[0].message.content:
        return response.choices[0].message.content
    elif hasattr(response, 'content') and response.content:
        # Extract text from content array
        for item in response.content:
            if item.get('type') == 'text':
                return item.get('text', '')
    return str(response)

def extract_skills(jd_text: str) -> tuple:
    """Extract skills and job role from job description."""
    try:
        from config import API_CONFIG
        
        messages = [
            {"role": "user", "content": f"""Analyze this job description and extract:
1. The JOB ROLE/DOMAIN (e.g., "ML Engineer", "Backend Developer", "Data Scientist", "DevOps Engineer", "Web Developer")
2. Key TECHNICAL SKILLS needed

Categories for skills:
- "coding": Programming languages (Python, C++, Java, JavaScript, Go, Rust, etc.)
- "tool": Tools/frameworks (Docker, Kubernetes, AWS, React, TensorFlow, etc.)
- "conceptual": Concepts (Agile, CI/CD, Machine Learning, System Design, etc.)

Return JSON like:
{{"role": "ML Engineer", "skills": [{{"name": "Python", "type": "coding"}}, {{"name": "TensorFlow", "type": "tool"}}, {{"name": "Deep Learning", "type": "conceptual"}}]}}
Extract 6-12 most important skills. Return ONLY JSON.

Job Description:
{jd_text}"""}
        ]
        
        text = call_claude(messages, max_tokens=600)
        
        # Clean markdown
        text = text.strip().replace("```json", "").replace("```", "").strip()
        
        # Try to parse JSON
        result = json.loads(text)
        
        # Validate response
        if isinstance(result, dict) and "skills" in result and "role" in result:
            st.session_state.job_role = result.get("role", "")
            return result["skills"]
        else:
            role, skills = fallback_extract_skills(jd_text)
            st.session_state.job_role = role
            return skills
            
    except json.JSONDecodeError as e:
        st.warning("Parsing issue, using pattern matching...")
        role, skills = fallback_extract_skills(jd_text)
        st.session_state.job_role = role
        return skills
    except Exception as e:
        st.warning(f"API error: {e}, using pattern matching...")
        role, skills = fallback_extract_skills(jd_text)
        st.session_state.job_role = role
        return skills

def fallback_extract_skills(text: str) -> tuple:
    """Fallback skill extraction using keyword patterns."""
    skills = []
    job_role = "Software Engineer"  # Default
    
    # Detect job role
    role_patterns = {
        "ml": "ML Engineer", "machine learning": "ML Engineer", "deep learning": "ML Engineer",
        "data scientist": "Data Scientist", "data engineer": "Data Engineer",
        "backend": "Backend Developer", "frontend": "Frontend Developer", "full stack": "Full Stack Developer",
        "devops": "DevOps Engineer", "sre": "SRE", "cloud": "Cloud Engineer",
        "mobile": "Mobile Developer", "ios": "iOS Developer", "android": "Android Developer",
        "security": "Security Engineer", "cyber": "Security Engineer"
    }
    
    text_lower = text.lower()
    for pattern, role in role_patterns.items():
        if pattern in text_lower:
            job_role = role
            break
    
    # Programming languages
    languages = ["Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "TypeScript", "Scala", "R", "MATLAB"]
    
    # Tools/Frameworks
    tools = ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring", "TensorFlow", "PyTorch", "Kubernetes", "Jenkins", "Git", "GitHub", "GitLab", "Terraform", "Ansible", "Prometheus", "Grafana"]
    
    # Concepts
    concepts = ["Machine Learning", "AI", "DevOps", "Agile", "Scrum", "CI/CD", "Microservices", "REST API", "GraphQL", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "Redis", "Kafka", "System Design", "Cloud Computing", "Security", "Testing", "Debugging"]
    
    for lang in languages:
        if lang.lower() in text_lower:
            skills.append({"name": lang, "type": "coding"})
    
    for tool in tools:
        if tool.lower() in text_lower:
            skills.append({"name": tool, "type": "tool"})
    
    for concept in concepts:
        if concept.lower() in text_lower:
            skills.append({"name": concept, "type": "conceptual"})
    
    # Remove duplicates
    seen = set()
    unique = []
    for s in skills:
        if s["name"] not in seen:
            seen.add(s["name"])
            unique.append(s)
    
    # If still empty, add defaults
    if not unique:
        unique = [
            {"name": "Programming", "type": "coding"},
            {"name": "Problem Solving", "type": "conceptual"}
        ]
    
    return job_role, unique[:10]  # Return role and max 10 skills

def generate_question(skill_name: str, skill_type: str, diff: int, prev_question: str = None, prev_answer: str = None) -> dict:
    """Generate question based on skill type, job role, and difficulty."""
    try:
        diff_labels = {1: "beginner", 2: "easy", 3: "medium", 4: "hard", 5: "expert"}
        difficulty = diff_labels.get(diff, "medium")
        job_role = st.session_state.get('job_role', 'Software Engineer')
        
        if prev_question and prev_answer:
            # Generate follow-up question based on previous answer
            prompt = f"""Ask a NEW follow-up question that builds on the previous answer.

Previous Question: {prev_question}
Previous Answer: {prev_answer}

Ask about: specific details, edge cases, trade-offs, or real-world applications.

Return JSON: {{"question": "new follow-up question", "follow_up_type": "deeper", "hints": ["hint"]}}"""
        elif skill_type == "coding":
            # Domain-specific coding problems based on job role
            # ML/DATA related coding examples
            ml_examples = {
                1: "Write a function to calculate softmax for a list of numbers",
                2: "Write a function to implement sigmoid activation. Input: 0.5 -> Output: 0.622",
                3: "Implement a function to compute dot product of two vectors (lists)",
                4: "Implement attention mechanism: given query, keys, values arrays, return weighted sum",
                5: "Implement a simple neural network forward pass with ReLU activation and softmax"
            }
            
            # Backend/DevOps related coding examples  
            backend_examples = {
                1: "Write a function to reverse a string",
                2: "Write a function to check if a number is prime",
                3: "Write a function to implement LRU cache using OrderedDict",
                4: "Implement a rate limiter using sliding window algorithm",
                5: "Design and implement a thread-safe producer-consumer pattern"
            }
            
            # Web/Frontend related coding examples
            web_examples = {
                1: "Write a function to validate an email address format",
                2: "Write a function to debounce rapid button clicks (ignore clicks within 300ms)",
                3: "Implement a function to deep clone a nested JSON object",
                4: "Implement a simple memoization decorator for any function",
                5: "Implement a virtual DOM diff algorithm for efficient updates"
            }
            
            # Generic DSA examples (fallback)
            generic_examples = {
                1: "Write a function that takes a list of numbers and returns their sum",
                2: "Write a function to check if a string is a palindrome",
                3: "Write a function to find two numbers in a list that add up to target",
                4: "Implement a function to find longest palindromic substring",
                5: "Implement a LRU cache with O(1) get and put operations"
            }
            
            # Select examples based on job role
            role_lower = job_role.lower()
            if any(x in role_lower for x in ['ml', 'machine learning', 'data', 'ai', 'deep learning', 'nlp']):
                examples = ml_examples
            elif any(x in role_lower for x in ['backend', 'devops', 'sre', 'cloud', 'sre']):
                examples = backend_examples
            elif any(x in role_lower for x in ['frontend', 'web', 'full stack', 'react', 'vue']):
                examples = web_examples
            else:
                examples = generic_examples
            
            prompt = f"""Generate a {difficulty} level coding problem for a {job_role} position using {skill_name}.

IMPORTANT: 
- Must be a CONCRETE problem with clear input/output
- Related to {job_role} work, NOT generic DSA
- Give specific examples

{examples.get(diff, examples[3])}

For difficulty {diff}, generate ONE specific problem similar to the example above.

Return JSON with:
{{"question": "EXACTLY what code to write - be specific", "input": "example input", "output": "expected output", "example": "input -> output", "constraints": "any constraints", "hints": ["hint1"]}}"""
        else:
            prompt = f"""Generate a {difficulty} interview question about {skill_name} for a {job_role} position.
NOT about experience - test actual knowledge with a scenario or problem.

Return JSON: {{"question": "[scenario-based question about {skill_name}]", "hints": ["hint"]}}"""
        
        messages = [{"role": "user", "content": prompt}]
        text = call_claude(messages, max_tokens=600)
        
        # Clean and parse JSON
        text = text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        
        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = text[start:end]
            result = json.loads(json_str)
            # Ensure question field exists
            if "question" in result:
                return result
            else:
                raise ValueError("No question field")
        else:
            raise ValueError("No JSON found")
    except Exception as e:
        # Return a coding task as fallback
        job_role = st.session_state.get('job_role', 'Software Engineer')
        return {
            "question": f"For a {job_role} role, write {skill_name} code to solve this: implement a basic data transformation function",
            "input": "[1, 2, 3]",
            "output": "[2, 4, 6]",
            "example": "[1, 2, 3] -> [2, 4, 6]",
            "hints": ["Think about what transformations a " + job_role + " would do"]
        }

def execute_code(code: str, language: str) -> dict:
    """Execute code and return output/errors"""
    import subprocess
    import sys
    
    if language.lower() == "python":
        try:
            # Execute Python code safely
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": None, "error": "Timeout: Code took too long to execute"}
        except Exception as e:
            return {"success": False, "output": None, "error": str(e)}
    else:
        return {"success": False, "output": None, "error": f"Execution for {language} not supported yet"}

def evaluate_answer(skill: str, question: str, answer: str, is_code: bool) -> dict:
    """Evaluate answer and return ACTUAL scores based on Claude's evaluation."""
    import re
    
    try:
        if is_code:
            eval_prompt = f"""Evaluate this code for the question:
Question: {question}

Code Submitted:
{answer}

IMPORTANT: 
- Judge if the code CORRECTLY solves the problem
- Give LOWER scores for wrong answers, HIGHER for correct ones
- If answer is wrong or incomplete, say so clearly

Return JSON with ONLY these fields:
{{"score": number from 0-100, "correct": true/false, "feedback": "brief explanation of what was right/wrong"}}"""

            messages = [{"role": "user", "content": eval_prompt}]
            response = call_claude(messages, max_tokens=500)
            
            response_lower = response.lower()
            
            # Try to extract score from response
            score = None
            correct = None
            
            # Look for score patterns
            score_patterns = [
                r'"score"\s*:\s*(\d+)',
                r'score[:\s]+(\d+)',
                r'(\d+)\s*/\s*100',
                r'(\d+)\s*percent',
            ]
            
            for pattern in score_patterns:
                match = re.search(pattern, response_lower)
                if match:
                    score = int(match.group(1))
                    break
            
            # Look for correct/incorrect indicators
            if 'correct: true' in response_lower or '"correct": true' in response_lower:
                correct = True
            elif 'correct: false' in response_lower or '"correct": false' in response_lower:
                correct = False
            elif any(x in response_lower for x in ['wrong', 'incorrect', 'not correct', 'doesn\'t solve', 'failed']):
                correct = False
            elif any(x in response_lower for x in ['correct', 'good', 'works', 'solved', 'right']):
                correct = True
            
            # Default to score if found, otherwise analyze keywords
            if score is not None:
                correctness = score / 100.0
            else:
                # Analyze response for positive/negative indicators
                positive_words = ["correct", "good", "great", "excellent", "works", "solved", "right", "accurate"]
                negative_words = ["wrong", "incorrect", "inaccurate", "not correct", "failed", "doesn't work", "error", "bug"]
                
                pos_count = sum(1 for word in positive_words if word in response_lower)
                neg_count = sum(1 for word in negative_words if word in response_lower)
                
                if neg_count > pos_count:
                    correctness = 0.3
                elif pos_count > neg_count:
                    correctness = 0.7
                else:
                    correctness = 0.5  # Neutral if unclear
            
            clarity = correctness  # Clarity follows correctness
            
            return {
                "correctness": correctness,
                "clarity": clarity,
                "correct": correct if correct is not None else (correctness >= 0.6),
                "depth": "high" if correctness > 0.75 else "medium" if correctness > 0.5 else "low",
                "feedback": response,
                "strengths": ["Shows understanding"] if correctness >= 0.5 else [],
                "gaps": ["Answer needs improvement"] if correctness < 0.7 else []
            }
        else:
            eval_prompt = f"""Evaluate this answer for the question:
Question: {question}

Answer: {answer}

IMPORTANT:
- Judge if the answer is CORRECT and COMPLETE
- Give LOWER scores for wrong/incomplete answers
- Be honest about what was correct vs incorrect

Return JSON with ONLY these fields:
{{"score": number from 0-100, "correct": true/false, "feedback": "brief explanation"}}"""

            messages = [{"role": "user", "content": eval_prompt}]
            response = call_claude(messages, max_tokens=500)
            
            response_lower = response.lower()
            
            # Try to extract score
            score = None
            correct = None
            
            for pattern in [r'"score"\s*:\s*(\d+)', r'score[:\s]+(\d+)', r'(\d+)/100']:
                match = re.search(pattern, response_lower)
                if match:
                    score = int(match.group(1))
                    break
            
            # Check correct field
            if 'correct: true' in response_lower or '"correct": true' in response_lower:
                correct = True
            elif 'correct: false' in response_lower or '"correct": false' in response_lower:
                correct = False
            
            if score is not None:
                correctness = score / 100.0
            else:
                # Keyword analysis
                positive_words = ["correct", "good", "great", "excellent", "accurate", "complete"]
                negative_words = ["wrong", "incorrect", "inaccurate", "incomplete", "missing", "lacking"]
                
                pos_count = sum(1 for word in positive_words if word in response_lower)
                neg_count = sum(1 for word in negative_words if word in response_lower)
                
                if neg_count > pos_count:
                    correctness = 0.3
                elif pos_count > neg_count:
                    correctness = 0.7
                else:
                    correctness = 0.5
            
            clarity = correctness
            
            return {
                "correctness": correctness,
                "clarity": clarity,
                "correct": correct if correct is not None else (correctness >= 0.6),
                "depth": "high" if correctness > 0.75 else "medium" if correctness > 0.5 else "low",
                "feedback": response,
                "strengths": ["Good answer"] if correctness >= 0.5 else [],
                "gaps": ["Needs more detail"] if correctness < 0.7 else []
            }
    except Exception as e:
        return {
            "correctness": 0.5, 
            "clarity": 0.5, 
            "correct": False,
            "depth": "medium", 
            "feedback": "Evaluation completed.",
            "strengths": [],
            "gaps": ["Could not fully evaluate"]
        }

# ============ MAIN APP ============
st.markdown("## 🤖 Adaptive Micro-Assessment Engine")

with st.sidebar:
    st.header("Settings")
    if st.button("🔄 Reset"):
        reset()

# ===== PHASE 1: JD Upload =====
if st.session_state.phase == 'start':
    st.markdown("### 📄 Step 1: Upload Job Description")
    
    jd_input = st.text_area("Paste Job Description:", height=200, placeholder="Paste job description here...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Extract Skills", type="primary", disabled=not jd_input):
            with st.spinner("Analyzing JD..."):
                skills = extract_skills(jd_input)
                st.session_state.skills = skills
                st.session_state.phase = 'skills'
                st.rerun()
    
    with col2:
        st.markdown("**Or enter manually:**")
    
    manual = st.text_input("Skills (comma-separated):", placeholder="Python, Docker, AWS")
    if st.button("Use Manual Skills") and manual:
        skills = [{"name": s.strip(), "type": "conceptual"} for s in manual.split(",") if s.strip()]
        st.session_state.skills = skills
        st.session_state.phase = 'skills'
        st.rerun()

# ===== PHASE 2: Select Skills =====
elif st.session_state.phase == 'skills':
    st.markdown("### ✅ Extracted Skills")
    
    # Show detected job role
    job_role = st.session_state.get('job_role', 'Software Engineer')
    st.markdown(f"**🎯 Position:** {job_role}")
    
    if not st.session_state.skills:
        st.warning("No skills extracted. Enter manually.")
        if st.button("← Go Back"):
            st.session_state.phase = 'start'
            st.rerun()
    
    # Display skills by category
    coding = [s for s in st.session_state.skills if s.get('type') == 'coding']
    tools = [s for s in st.session_state.skills if s.get('type') == 'tool']
    concepts = [s for s in st.session_state.skills if s.get('type') == 'conceptual']
    
    selected = []
    
    if coding:
        st.markdown("**💻 Coding Languages:**")
        for s in coding:
            if st.checkbox(f"  {s['name']}", value=True):
                selected.append(s)
    
    if tools:
        st.markdown("**🔧 Tools & Frameworks:**")
        for s in tools:
            if st.checkbox(f"  {s['name']}", value=True):
                selected.append(s)
    
    if concepts:
        st.markdown("**📚 Concepts:**")
        for s in concepts:
            if st.checkbox(f"  {s['name']}", value=True):
                selected.append(s)
    
    if selected:
        st.session_state.selected_skills = selected
        
        # Initialize tracking
        for s in selected:
            name = s['name']
            if name not in st.session_state.skill_scores:
                st.session_state.skill_scores[name] = {'correct': 0, 'total': 0}
            if name not in st.session_state.difficulty:
                st.session_state.difficulty[name] = 3  # Start at medium
        
        if st.button(f"🎯 Start Assessment ({len(selected)} skills)", type="primary"):
            st.session_state.current_skill_idx = 0
            st.session_state.current_skill = selected[0]
            st.session_state.phase = 'assess'
            st.rerun()
    else:
        st.warning("Select at least one skill.")

# ===== PHASE 3: Assessment =====
elif st.session_state.phase == 'assess':
    skill = st.session_state.current_skill
    skill_name = skill['name']
    skill_type = skill.get('type', 'conceptual')
    
    diff = st.session_state.difficulty.get(skill_name, 3)
    diff_stars = "⭐" * diff
    
    # Progress
    total_skills = len(st.session_state.selected_skills)
    current_idx = st.session_state.current_skill_idx
    
    st.markdown(f"### 🎯 {skill_name}")
    st.markdown(f"**Type:** {skill_type} | **Difficulty:** {diff_stars}")
    st.progress((current_idx + 1) / total_skills, text=f"Skill {current_idx + 1}/{total_skills}")
    
    # Generate question (with follow-up context if available)
    if not st.session_state.question:
        with st.spinner("Generating question..."):
            prev_q = st.session_state.get('prev_question')
            prev_a = st.session_state.get('prev_answer')
            st.session_state.question = generate_question(skill_name, skill_type, diff, prev_q, prev_a)
    
    q_data = st.session_state.question
    st.markdown(f'<div class="question-box"><b>❓ Question:</b><br>{q_data.get("question", "No question generated")}</div>', unsafe_allow_html=True)
    
    # Determine if question requires code execution
    # Only for programming languages AND explicit coding requests
    question_text = q_data.get("question", "").lower()
    
    # Programming languages that should get code editor
    coding_languages = ["python", "java", "javascript", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin", "typescript"]
    is_programming_language = skill_name.lower() in coding_languages
    
    # Only trigger code editor if it's a programming language AND question asks for code
    code_keywords = [
        "write code", "write a", "write python", "write javascript",
        "implement a", "implement the",
        "solve this", "solve the problem",
        "create a function", "create a program",
        "build a", "build an"
    ]
    asks_for_code = any(keyword in question_text for keyword in code_keywords)
    
    # Code editor only if both conditions met
    is_code_question = is_programming_language and asks_for_code
    
    if is_code_question:
        # Auto-detect language from skill name
        lang_map = {
            "python": "Python", "c++": "C++", "java": "Java", 
            "javascript": "JavaScript", "go": "Go", "rust": "Rust",
            "typescript": "TypeScript", "c#": "C#", "ruby": "Ruby",
            "php": "PHP", "swift": "Swift", "kotlin": "Kotlin"
        }
        detected_lang = lang_map.get(skill_name.lower(), skill_name)
        
        st.markdown(f'<div class="question-box"><b>💻 Language:</b> {detected_lang}</div>', unsafe_allow_html=True)
        
        # Show input/output if available
        if q_data.get("input"):
            st.markdown(f"**📥 Input:** `{q_data.get('input')}`")
        if q_data.get("output"):
            st.markdown(f"**📤 Output:** `{q_data.get('output')}`")
        if q_data.get("example"):
            st.markdown(f"**📋 Example:** `{q_data.get('example')}`")
        
        # Monaco Editor (like VS Code) - syntax highlighting only
        answer = render_code_editor("main_code", detected_lang, height=380)
    else:
        answer = st.text_area("Your Answer:", height=150)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        submit_btn = st.button("📤 Submit", type="primary", disabled=not answer)
    with col2:
        hint_btn = st.button("💡 Get Hint")
    with col3:
        if is_code_question:
            test_btn = st.button("🧪 Test Output", disabled=not answer)
    
    # Show hint
    if hint_btn and q_data.get("hints"):
        hints = q_data["hints"]
        st.info(f"💡 **Hint:** {hints[0] if len(hints) > 0 else 'Think about the core concept.'}")
    
    # Process submission
    if submit_btn and answer:
        with st.spinner("Evaluating..."):
            ev = evaluate_answer(skill_name, q_data.get("question", ""), answer, is_code_question)
            st.session_state.evaluation = ev
            st.session_state.eval_done = True
            st.session_state.answers.append({'skill': skill_name, 'answer': answer, 'eval': ev})
            
            # Update scores
            st.session_state.skill_scores[skill_name]['total'] += 1
            if ev.get('correctness', 0) >= 0.6:
                st.session_state.skill_scores[skill_name]['correct'] += 1
            
            # Update difficulty
            if ev.get('correctness', 0) >= 0.8:
                st.session_state.difficulty[skill_name] = min(5, diff + 1)
            elif ev.get('correctness', 0) < 0.4:
                st.session_state.difficulty[skill_name] = max(1, diff - 1)
            
            st.rerun()
    
    # Show evaluation
    if st.session_state.eval_done:
        ev = st.session_state.evaluation
        depth = ev.get('depth', 'medium')
        
        st.markdown("---")
        st.markdown("### 📊 Evaluation")
        
        cols = st.columns(3)
        cols[0].metric("✅ Correctness", f"{ev.get('correctness', 0):.0%}")
        if is_code_question:
            cols[1].metric("📝 Clarity", f"{ev.get('clarity', 0):.0%}")
            cols[2].metric("🔍 Depth", f"{'🟢' if depth=='high' else '🟡' if depth=='medium' else '🔴'} {depth.upper()}")
        else:
            cols[1].metric("📝 Clarity", f"{ev.get('clarity', 0):.0%}")
            cols[2].metric("🔍 Depth", f"{'🟢' if depth=='high' else '🟡' if depth=='medium' else '🔴'} {depth.upper()}")
        
        # Extract and display clean feedback (remove JSON formatting)
        feedback_text = ev.get('feedback', '')
        # Try to extract just the feedback text from JSON
        try:
            if '{' in feedback_text and '}' in feedback_text:
                feedback_json = json.loads(feedback_text)
                feedback_text = feedback_json.get('feedback', feedback_text)
        except:
            pass  # Keep original if not JSON
        st.markdown(f"**Feedback:** {feedback_text}")
        
        if ev.get('strengths'):
            st.success("✅ " + ", ".join(ev['strengths'][:2]))
        if ev.get('gaps'):
            st.error("❌ " + ", ".join(ev['gaps'][:2]))
        
        # Next action
        st.markdown("---")
        
        # Follow-up question options
        st.markdown("---")
        st.markdown("### 🔄 Next Steps")
        
        scores = st.session_state.skill_scores[skill_name]
        accuracy = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
        
        # Follow-up question button
        if scores['total'] <= 2:
            st.info("💬 Ask a follow-up question to dig deeper!")
            if st.button("🔄 Follow-up Question", type="primary"):
                # Store current Q&A for context
                st.session_state.prev_question = q_data.get("question", "")
                st.session_state.prev_answer = st.session_state.answers[-1]['answer'] if st.session_state.answers else ""
                st.session_state.question = None
                st.session_state.eval_done = False
                st.rerun()
        
        # Difficulty adjustment buttons
        if depth == 'high' and scores['total'] < 3 and accuracy >= 0.7:
            st.info("💡 Excellent! Let me try harder...")
            if st.button("🔨 Harder Question"):
                st.session_state.question = None
                st.session_state.eval_done = False
                st.rerun()
        elif depth == 'low' and scores['total'] < 2:
            st.info("📚 Let me try easier...")
            if st.button("🔰 Easier Question"):
                st.session_state.question = None
                st.session_state.eval_done = False
                st.rerun()
        
        # Move to next skill
        next_idx = st.session_state.current_skill_idx + 1
        if st.button("➡️ Next Skill", type="secondary"):
            if next_idx >= len(st.session_state.selected_skills):
                st.session_state.phase = 'results'
            else:
                st.session_state.current_skill_idx = next_idx
                st.session_state.current_skill = st.session_state.selected_skills[next_idx]
            st.session_state.question = None
            st.session_state.prev_question = None
            st.session_state.prev_answer = None
            st.session_state.eval_done = False
            st.rerun()

# ===== PHASE 4: Results =====
elif st.session_state.phase == 'results':
    st.markdown("## 🎉 Assessment Complete!")
    
    # Calculate scores
    total_correct = sum(s['correct'] for s in st.session_state.skill_scores.values())
    total_q = sum(s['total'] for s in st.session_state.skill_scores.values())
    overall = (total_correct / total_q * 100) if total_q > 0 else 0
    
    # Separate by type
    coding_scores = []
    other_scores = []
    
    for skill in st.session_state.selected_skills:
        name = skill['name']
        scores = st.session_state.skill_scores.get(name, {'correct': 0, 'total': 1})
        acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
        if skill.get('type') == 'coding':
            coding_scores.append(acc)
        else:
            other_scores.append(acc)
    
    tech_score = (sum(coding_scores) / len(coding_scores) * 100) if coding_scores else None
    know_score = (sum(other_scores) / len(other_scores) * 100) if other_scores else overall
    comm_score = min(100, overall + 10)
    
    # Display scores
    st.markdown("### 📊 Final Score Breakdown")
    
    cols = st.columns(4)
    cols[0].metric("🎯 Overall", f"{overall:.0f}%")
    cols[1].metric("💻 Technical", f"{tech_score:.0f}%" if tech_score else "N/A")
    cols[2].metric("📚 Knowledge", f"{know_score:.0f}%")
    cols[3].metric("🗣️ Communication", f"{comm_score:.0f}%")
    
    # Per-skill breakdown
    st.markdown("---")
    st.markdown("### 🔍 Per-Skill Breakdown")
    
    for skill in st.session_state.selected_skills:
        name = skill['name']
        scores = st.session_state.skill_scores.get(name, {'correct': 0, 'total': 1})
        acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
        diff = st.session_state.difficulty.get(name, 3)
        
        if acc >= 0.8 and diff >= 4:
            level = "✅ Expert"
            color = "success"
        elif acc >= 0.6:
            level = "⚠️ Proficient"
            color = "warning"
        elif acc >= 0.4:
            level = "🔴 Developing"
            color = "info"
        else:
            level = "❌ Needs Training"
            color = "error"
        
        msg = f"**{name}**: {level} ({acc:.0%}, ⭐{diff})"
        if color == "success":
            st.success(msg)
        elif color == "warning":
            st.warning(msg)
        else:
            st.error(msg)
    
    # Communication assessment
    st.markdown("---")
    st.markdown("### 🗣️ Communication Assessment")
    
    if overall >= 70:
        st.success("✅ **Strong Communicator** - Explains concepts clearly")
        comm_note = "Can effectively communicate technical concepts."
    elif overall >= 50:
        st.warning("⚠️ **Adequate Communicator** - Basic explanations")
        comm_note = "Can explain basic concepts, room for improvement."
    else:
        st.error("❌ **Needs Training** - Lacks clarity")
        comm_note = "Should practice explaining concepts more clearly."
    
    st.markdown(f"_{comm_note}_")
    
    # Final recommendation with explanation
    st.markdown("---")
    st.markdown("### 🏆 Final Assessment")
    
    # Build explanation
    explanation_parts = []
    
    if overall >= 75:
        st.success("## ✅ HIGHLY RECOMMENDED")
        explanation_parts.append(f"**Overall Score: {overall:.0f}%** - Strong performance across most areas")
    elif overall >= 55:
        st.warning("## ⚠️ CONDITIONALLY RECOMMENDED")
        explanation_parts.append(f"**Overall Score: {overall:.0f}%** - Average performance, some areas need improvement")
    else:
        st.error("## ❌ NEEDS MORE TRAINING")
        explanation_parts.append(f"**Overall Score: {overall:.0f}%** - Significant gaps in knowledge or skills")
    
    # Explain score calculation
    st.markdown("---")
    st.markdown("#### 📊 How Your Score Was Calculated")
    
    total_attempts = sum(s['total'] for s in st.session_state.skill_scores.values())
    total_correct = sum(s['correct'] for s in st.session_state.skill_scores.values())
    
    st.markdown(f"""
    - **Questions Answered:** {total_attempts}
    - **Correct Answers:** {total_correct}
    - **Accuracy:** {(total_correct/total_attempts*100) if total_attempts > 0 else 0:.0f}%
    
    **Scoring Criteria:**
    - ✅ **Expert** (80%+ accuracy at high difficulty) = Strong hire
    - ⚠️ **Proficient** (60%+ accuracy) = Good candidate
    - 🔴 **Developing** (40-60%) = Needs training
    - ❌ **Needs Training** (<40%) = Not ready
    """)
    
    # Detailed breakdown
    st.markdown("---")
    st.markdown("#### 🔍 Detailed Breakdown by Skill")
    
    for skill in st.session_state.selected_skills:
        name = skill['name']
        scores = st.session_state.skill_scores.get(name, {'correct': 0, 'total': 1})
        correct = scores['correct']
        total = scores['total']
        acc = correct / total if total > 0 else 0
        diff = st.session_state.difficulty.get(name, 3)
        
        if acc >= 0.8 and diff >= 4:
            level = "Expert"
            icon = "🟢"
            st.markdown(f"{icon} **{name}**: {level} - {correct}/{total} correct at ⭐{diff} difficulty")
        elif acc >= 0.6:
            level = "Proficient"
            icon = "🟡"
            st.markdown(f"{icon} **{name}**: {level} - {correct}/{total} correct at ⭐{diff} difficulty")
        elif acc >= 0.4:
            level = "Developing"
            icon = "🟠"
            st.markdown(f"{icon} **{name}**: {level} - {correct}/{total} correct at ⭐{diff} difficulty")
        else:
            level = "Needs Training"
            icon = "🔴"
            st.markdown(f"{icon} **{name}**: {level} - {correct}/{total} correct at ⭐{diff} difficulty")
    
    # Strengths & Areas with explanations
    st.markdown("---")
    st.markdown("#### ✅ What You Did Well")
    
    strengths_found = False
    for skill in st.session_state.selected_skills:
        name = skill['name']
        scores = st.session_state.skill_scores.get(name, {'correct': 0, 'total': 1})
        acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
        if acc >= 0.7:
            st.markdown(f"- **{name}**: Strong understanding demonstrated ({acc:.0%} accuracy)")
            strengths_found = True
    
    if not strengths_found:
        st.markdown("- Keep practicing to improve your scores!")
    
    st.markdown("")
    st.markdown("#### 📚 Areas to Improve")
    
    gaps_found = False
    for skill in st.session_state.selected_skills:
        name = skill['name']
        scores = st.session_state.skill_scores.get(name, {'correct': 0, 'total': 1})
        acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
        if acc < 0.6:
            gap = 100 - (acc * 100)
            st.markdown(f"- **{name}**: {gap:.0f}% gap in knowledge - Consider more practice")
            gaps_found = True
    
    if not gaps_found:
        st.markdown("- No major gaps identified!")
    
    # Download
    report = {
        "overall_score": round(overall, 1),
        "technical_score": round(tech_score, 1) if tech_score else None,
        "knowledge_score": round(know_score, 1),
        "communication_score": round(comm_score, 1),
        "recommendation": "Highly Recommended" if overall >= 75 else "Conditionally Recommended" if overall >= 55 else "Not Recommended",
        "skills": st.session_state.skill_scores,
        "difficulties": st.session_state.difficulty
    }
    
    st.download_button("📥 Download Report", json.dumps(report, indent=2), "assessment_report.json")
    
    if st.button("🔄 New Assessment"):
        reset()
