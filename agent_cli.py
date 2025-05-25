"""
agent_cli.py

Interactive CLI for Sports Psychologist AI Agent using prompt_toolkit.
Supports chat, profile management, and TTS via FastAPI endpoints.
"""

import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
import sys
import os
try:
    from pydub import AudioSegment
    import simpleaudio as sa
except ImportError:
    AudioSegment = None
    sa = None  # Will warn user if not installed

API_URL = "http://localhost:8000"  # Change if running FastAPI elsewhere

style = Style.from_dict({
    '': '#00ff00',
    'prompt': '#00afff bold',
    'error': '#ff0000 bold',
})

modes = ['chat', 'profile-get', 'profile-post', 'profile-put', 'tts', 'exit']
mode_completer = WordCompleter(modes, ignore_case=True)

# Voice mapping for dynamic selection
VOICE_MAP = {
    ("male", "australian"): "IKne3meq5aSn9XLyUdCD",  # Charlie
    ("female", "american"): "EXAVITQu4vr4xnSDxMaL",  # Sarah
    ("male", "british"): "JBFqnCBsd6RMkjVDRZzb",     # George
    ("female", "british"): "Xb7hH8MSUJpSbSDYk0k2",   # Alice
    ("male", "american"): "cjVigY5qzO86Huf0OWal",    # Eric
    ("female", "swedish"): "XB0fDUnXU5powFXDhCwa",   # Charlotte
    # Add more as needed
}
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah (female, american)

def extract_voice_characteristics(message):
    message = message.lower()
    gender = None
    accent = None
    if "female" in message:
        gender = "female"
    elif "male" in message:
        gender = "male"
    if "australian" in message:
        accent = "australian"
    elif "british" in message:
        accent = "british"
    elif "american" in message:
        accent = "american"
    elif "swedish" in message:
        accent = "swedish"
    return gender, accent

def get_voice_id(gender, accent):
    return VOICE_MAP.get((gender, accent), DEFAULT_VOICE_ID)

def get_user_id():
    """Prompt for user_id."""
    session = PromptSession()
    user_id = session.prompt('[prompt]Enter user_id: ', style=style)
    return user_id.strip()


def chat_mode(user_id):
    """Chat with the agent and auto-play TTS for each response, with dynamic voice selection."""
    session = PromptSession()
    print("[prompt]Type your message (or /exit to return to mode select):")
    current_gender = "female"
    current_accent = "american"
    voice_id = get_voice_id(current_gender, current_accent)
    while True:
        msg = session.prompt("You: ", style=style)
        if msg.strip().lower() == "/exit":
            break
        # Detect voice change request
        gender, accent = extract_voice_characteristics(msg)
        changed = False
        if gender:
            current_gender = gender
            changed = True
        if accent:
            current_accent = accent
            changed = True
        if changed:
            voice_id = get_voice_id(current_gender, current_accent)
            print(f"[prompt]Voice changed to {current_gender} {current_accent}")
        resp = requests.post(f"{API_URL}/chat", json={"user_id": user_id, "message": msg})
        if resp.status_code == 200:
            agent_reply = resp.json().get("response", "")
            print(f"Agent: {agent_reply}")
            # Auto TTS with dynamic voice
            tts_resp = requests.post(f"{API_URL}/tts", json={"text": agent_reply, "user_id": user_id, "voice_id": voice_id})
            if tts_resp.status_code == 200:
                filename = f"tts_{user_id}.mp3"
                with open(filename, "wb") as f:
                    f.write(tts_resp.content)
                print(f"[prompt]Audio saved to {filename}")
                if AudioSegment and sa:
                    try:
                        wav_filename = filename.replace('.mp3', '.wav')
                        sound = AudioSegment.from_mp3(filename)
                        sound.export(wav_filename, format='wav')
                        wave_obj = sa.WaveObject.from_wave_file(wav_filename)
                        play_obj = wave_obj.play()
                        play_obj.wait_done()
                    except Exception as e:
                        print(f"[error]Could not play audio: {e}")
                else:
                    print("[error]Install 'pydub' and 'simpleaudio' to auto-play audio: pip install pydub simpleaudio")
            else:
                print(f"[error]TTS error: {tts_resp.status_code} {tts_resp.text}")
        else:
            print(f"[error]Chat error: {resp.status_code} {resp.text}")


def profile_get_mode(user_id):
    """Fetch and display user profile."""
    resp = requests.get(f"{API_URL}/profile", params={"user_id": user_id})
    if resp.status_code == 200:
        print("[prompt]Profile:")
        for k, v in resp.json().items():
            print(f"  {k}: {v}")
    else:
        print(f"[error]Error: {resp.status_code} {resp.text}", style=style)


def profile_post_mode(user_id):
    """Create or update user profile."""
    session = PromptSession()
    sport = session.prompt('Sport: ', style=style)
    goals = session.prompt('Goals: ', style=style)
    level = session.prompt('Level: ', style=style)
    notes = session.prompt('Notes: ', style=style)
    profile = {
        "id": user_id,
        "sport": sport,
        "goals": goals,
        "level": level,
        "notes": notes
    }
    resp = requests.post(f"{API_URL}/profile", json=profile)
    if resp.status_code == 200:
        print("[prompt]Profile updated.")
    else:
        print(f"[error]Error: {resp.status_code} {resp.text}", style=style)


def profile_put_mode(user_id):
    """Update user profile (PUT)."""
    session = PromptSession()
    sport = session.prompt('Sport: ', style=style)
    goals = session.prompt('Goals: ', style=style)
    level = session.prompt('Level: ', style=style)
    notes = session.prompt('Notes: ', style=style)
    profile = {
        "id": user_id,
        "sport": sport,
        "goals": goals,
        "level": level,
        "notes": notes
    }
    resp = requests.put(f"{API_URL}/profile", json=profile)
    if resp.status_code == 200:
        print("[prompt]Profile updated.")
    else:
        print(f"[error]Error: {resp.status_code} {resp.text}", style=style)


def tts_mode(user_id):
    """Send text to TTS endpoint and save audio to file."""
    session = PromptSession()
    text = session.prompt('Text to synthesize: ', style=style)
    req = {"text": text, "user_id": user_id}
    resp = requests.post(f"{API_URL}/tts", json=req)
    if resp.status_code == 200:
        filename = f"tts_{user_id}.mp3"
        with open(filename, "wb") as f:
            f.write(resp.content)
        print(f"[prompt]Audio saved to {filename}")
    else:
        print(f"[error]Error: {resp.status_code} {resp.text}", style=style)


def main():
    print("\n[prompt]Sports Psychologist AI Agent CLI\nType a mode (chat, profile-get, profile-post, profile-put, tts, exit):\n")
    session = PromptSession()
    user_id = get_user_id()
    while True:
        mode = session.prompt('Mode: ', completer=mode_completer, style=style)
        mode = mode.strip().lower()
        if mode == 'exit':
            print("[prompt]Goodbye!")
            sys.exit(0)
        elif mode == 'chat':
            chat_mode(user_id)
        elif mode == 'profile-get':
            profile_get_mode(user_id)
        elif mode == 'profile-post':
            profile_post_mode(user_id)
        elif mode == 'profile-put':
            profile_put_mode(user_id)
        elif mode == 'tts':
            tts_mode(user_id)
        else:
            print("[error]Unknown mode. Try again.", style=style)

if __name__ == "__main__":
    main() 