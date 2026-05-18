"""Test script to verify Groq API key works."""
import requests, json

KEY = "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"
headers = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

resp = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers=headers,
    json={
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hola, quien eres? Responde en 1 frase en espanol."}],
        "max_tokens": 100,
        "temperature": 0.7
    },
    timeout=30
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    msg = data["choices"][0]["message"]["content"]
    print(f"Respuesta: {msg}")
    print(f"Tokens: prompt={data['usage']['prompt_tokens']} completion={data['usage']['completion_tokens']}")
else:
    print(f"Error: {resp.text[:500]}")
