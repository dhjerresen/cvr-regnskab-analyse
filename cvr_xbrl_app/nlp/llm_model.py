# nlp/llm_model.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env ONLY if running locally
# (Hugging Face does NOT need .env, it injects secrets automatically)
load_dotenv()

# Try both local and HF env vars
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "❌ GEMINI_API_KEY not found. "
        "Set it in a local .env file or in HuggingFace Spaces → Settings → Secrets."
    )

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Single model used across project
MODEL = "gemini-2.5-flash"

def run_ai_model(prompt: str) -> str:
    """
    Runs the single shared Gemini model for:
    - XBRL summary
    - XHTML extraction
    - XHTML summarization
    """
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"[Gemini ERROR] {e}")
        return ""
