"""
TTS Service - LIVE STREAMING Audio
================================
Streams audio in real-time chunks.
"""

import asyncio
import io

async def generate_live_stream(text: str, voice: str = "en-US-AriaNeural", speed: float = 1.5):
    """
    Generate live streaming audio and yield chunks.
    """
    from edge_tts import Communicate
    
    rate = f"+{(speed-1)*100:.0f}%"
    communicate = Communicate(text, voice=voice, rate=rate)
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]

def text_to_speech_stream(text: str, voice: str = "en-US-AriaNeural", speed: float = 1.5) -> bytes:
    """
    Generate full audio bytes for streaming playback.
    """
    try:
        async def generate():
            chunks = []
            async for chunk in generate_live_stream(text, voice, speed):
                chunks.append(chunk)
            return b"".join(chunks)
        
        return asyncio.run(generate())
    
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

# List available voices
VOICES = [
    "en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural",
    "en-GB-SophieNeural", "en-GB-RyanNeural",
    "en-AU-NatashaNeural", "en-IN-NeerjaNeural"
]
