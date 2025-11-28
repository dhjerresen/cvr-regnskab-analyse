# llm_summary.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

# Read API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# The ONE model used by the project
MODEL = "gemini-2.5-flash"

def run_ai_model(prompt: str) -> str:
    """
    Sends a prompt to Google's Gemini API using the single fixed model.
    Used globally for:
    - XBRL summary
    - XHTML extraction
    - XHTML summarization
    """
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)

        # Gemini returns a response object with .text
        return response.text.strip()

    except Exception as e:
        print(f"[Gemini ERROR] {e}")
        return ""
