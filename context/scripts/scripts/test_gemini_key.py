"""Test script to verify Gemini API key works."""
import requests

KEY = "AIzaSyDhyQt4ysp-PhkmLqEUhd3c9Ln3b8e_siE"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={KEY}"

payload = {
    "contents": [{"role": "user", "parts": [{"text": "Hola, presentate en 1 frase en espanol. Quien eres?"}]}],
    "generationConfig": {"maxOutputTokens": 100, "temperature": 0.7}
}

try:
    resp = requests.post(URL, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        print(f"Respuesta: {text.strip()}")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
