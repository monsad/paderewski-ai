import os
from typing import Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from anthropic import Anthropic
except Exception:
    Anthropic = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Podstawowe ustawienia
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
PADEREWSKI_BASE_URL = os.getenv("PADEREWSKI_BASE_URL", "https://paderewskicompetition.pl/")
PARTICIPANTS_URL = os.getenv(
    "PARTICIPANTS_URL",
    "https://www.konkurspaderewskiego.pl/uczestnicy-xiii-konkursu-2025/"
)
JURY_URL = os.getenv("JURY_URL", "https://paderewskicompetition.pl/jury/")

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" lub "openai"
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if (ANTHROPIC_API_KEY and Anthropic) else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OPENAI_API_KEY and OpenAI) else None

def get_llm_diagnostics() -> Dict:
    return {
        "provider": LLM_PROVIDER,
        "model": LLM_MODEL,
        "anthropic_ready": bool(anthropic_client),
        "anthropic_key_present": bool(ANTHROPIC_API_KEY),
        "anthropic_sdk_installed": Anthropic is not None,
        "openai_ready": bool(openai_client),
        "openai_key_present": bool(OPENAI_API_KEY),
        "openai_sdk_installed": OpenAI is not None,
    }