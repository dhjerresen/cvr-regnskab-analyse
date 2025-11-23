# llm_summary.py
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"


def run_ai_model(prompt: str) -> str:
    """
    Sends a prompt to a local Ollama model (phi3:mini) and returns output text.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Ollama error: {response.text}")

    data = response.json()
    return data.get("response", "")
