"""Code Editor Component - Simple but reliable code editor"""
import streamlit as st

def render_code_editor(key: str, language: str, height: int = 400, initial: str = ""):
    """Render a code editor with syntax highlighting styling"""
    
    # Session state key
    session_key = f"code_{key}"
    
    # Initialize if not exists
    if session_key not in st.session_state:
        st.session_state[session_key] = initial or "# Write your code here\n"
    
    # Language display
    st.markdown(f"📝 <span style='color:#4fc3f7; font-weight:bold;'>{language.upper()}</span> Code Editor", unsafe_allow_html=True)
    
    # Code input - this is what gets submitted
    code = st.text_area(
        "Enter your code",
        value=st.session_state[session_key],
        height=height,
        key=f"input_{key}",
        placeholder=f"# Write your {language} code here\n",
        label_visibility="collapsed"
    )
    
    # Update session state when user types
    st.session_state[session_key] = code
    
    return code
