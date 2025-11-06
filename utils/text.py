import unicodedata
from typing import List, Dict

def normalize_text(s: str, ascii_fallback: bool = False) -> str:
    s = unicodedata.normalize("NFC", s or "")
    if not ascii_fallback:
        return s
    mapping = {
        "ą":"a","ć":"c","ę":"e","ł":"l","ń":"n","ó":"o","ś":"s","ź":"z","ż":"z",
        "Ą":"A","Ć":"C","Ę":"E","Ł":"L","Ń":"N","Ó":"O","Ś":"S","Ź":"Z","Ż":"Z",
    }
    return "".join(mapping.get(ch, ch) for ch in s)

def build_user_text(prompt: str, names: List[str], ascii_fallback: bool = False) -> str:
    body = prompt + "\n\nUczestnicy:\n" + "\n".join(names)
    return normalize_text(body, ascii_fallback)

def resolve_llm_model(provider: str, model_name: str) -> str:
    if provider == "anthropic":
        m = (model_name or "").strip()
        if not m:
            return "claude-sonnet-4-5-20250929"
        s = m.lower()
        s = s.replace("claude-4.5-sonnet-", "claude-sonnet-4-5-")
        s = s.replace("claude-4-5-sonnet-", "claude-sonnet-4-5-")
        s = s.replace("claude-4.5-sonnet", "claude-sonnet-4-5")
        s = s.replace("claude-4-5-sonnet", "claude-sonnet-4-5")
        s = s.replace("claude-3.5", "claude-3-5")
        aliases = {
            "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-5-latest": "claude-sonnet-4-5-20250929",
            "claude-3-7-sonnet-latest": "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-latest": "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20241022": "claude-sonnet-4-5-20250929",
            "claude-3-5-haiku-latest": "claude-3-5-haiku-20241022",
        }
        return aliases.get(s, s)
    if provider == "openai":
        return (model_name or "").strip() or "gpt-4o-mini"
    return (model_name or "").strip()

def safe_parse_llm_json(raw_text: str) -> Dict:
    import json, re
    if not raw_text:
        return {}
    s = raw_text.strip()
    s = re.sub(r'^\s*```(?:json)?\s*', '', s)
    s = re.sub(r'\s*```\s*$', '', s)
    try:
        return json.loads(s)
    except Exception:
        pass
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = s[start:end + 1]
        candidate = re.sub(r",\s*}", "}", candidate)
        try:
            return json.loads(candidate)
        except Exception:
            return {}
    return {}