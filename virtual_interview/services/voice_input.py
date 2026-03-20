"""
Voice Input Service - Auto Transcribe
====================================
"""

import tempfile
import os

def transcribe_audio(audio_data) -> str:
    """Convert audio to text."""
    try:
        import speech_recognition as sr
        
        # Get bytes from UploadedFile
        audio_bytes = audio_data.getvalue() if hasattr(audio_data, 'getvalue') else audio_data
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        # Transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        
        os.unlink(temp_path)
        return text
    except Exception as e:
        print(f"Transcribe error: {e}")
        return ""

def voice_input_with_submit(key: str = "voice"):
    """Voice input with auto-transcribe and submit."""
    import streamlit as st
    
    st.markdown("**🎤 Voice Recording:**")
    
    audio_data = st.audio_input("Record your answer", key=f"rec_{key}")
    
    if audio_data:
        with st.spinner("🎤 Transcribing..."):
            text = transcribe_audio(audio_data)
            if text:
                st.session_state[f"voice_text_{key}"] = text
                st.success(f"✅ Heard: {text}")
                return text
            else:
                st.warning("⚠️ Could not transcribe. Please type your answer below.")
    
    return None
