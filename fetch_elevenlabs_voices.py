import os
import requests

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("Set ELEVENLABS_API_KEY in your environment or .env file.")

url = "https://api.elevenlabs.io/v1/voices"
headers = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    voices = response.json().get("voices", [])
    for v in voices:
        print(f"Name: {v['name']}")
        print(f"Voice ID: {v['voice_id']}")
        print(f"Labels: {v.get('labels', {})}")
        print(f"Category: {v.get('category', '')}")
        print("-" * 40)
else:
    print(f"Failed to fetch voices: {response.status_code} {response.text}") 