from typing import Dict, List
from config import LLM_PROVIDER, LLM_MODEL, anthropic_client, openai_client
from utils.text import build_user_text, normalize_text, resolve_llm_model, safe_parse_llm_json

def llm_predict_winner(participants: List[Dict]) -> Dict:
    names = [p.get("name", "") for p in participants if p.get("name")]
    if not names:
        return {"prediction": None, "confidence": 0.0, "rationale": "Brak listy uczestników (nie udało się pobrać)."}

    prompt = (
        "Jesteś analitykiem konkursu pianistycznego Paderewski 2025. "
        "Na podstawie listy uczestników i typowego programu (etudy, sonaty, Paderewski, recital z Herdzinem i Mozartem, finałowy koncert), "
        "zaproponuj 3 kandydatów do zwycięstwa. "
        "Zwróć JSON: {top_candidates: [{name, probability, rationale}], note}. "
        "Prawdopodobieństwa w sumie ≤ 1. Używaj wyłącznie nazw z listy."
    )

    model_id = resolve_llm_model(LLM_PROVIDER, LLM_MODEL)

    if LLM_PROVIDER == "anthropic" and anthropic_client:
        try:
            user_text = build_user_text(prompt, names, ascii_fallback=False)
            resp = anthropic_client.messages.create(
                model=model_id,
                max_tokens=1024,
                temperature=0.4,
                system=normalize_text("Jesteś precyzyjnym analitykiem konkursowym, który zwraca ściśle sformatowany JSON."),
                messages=[{"role": "user", "content": [{"type": "text", "text": user_text}]}],
            )
            content_text = ""
            for block in (resp.content or []):
                if getattr(block, "type", "") == "text":
                    content_text += getattr(block, "text", "")
            data = safe_parse_llm_json(content_text)
            top = data.get("top_candidates", [])
            if top:
                best = max(top, key=lambda x: float(x.get("probability", 0.0)))
                return {
                    "prediction": best.get("name"),
                    "confidence": float(best.get("probability", 0.0)),
                    "rationale": (best.get("rationale") or "") + (" " + (data.get("note") or "")),
                    "top_candidates": top,
                }
            # Retry z ASCII jeśli brak JSON
            if not top:
                user_text = build_user_text(prompt, names, ascii_fallback=True)
                resp = anthropic_client.messages.create(
                    model=model_id,
                    max_tokens=1024,
                    temperature=0.4,
                    system=normalize_text("You are a precise competition analyst that outputs strict JSON.", ascii_fallback=True),
                    messages=[{"role": "user", "content": [{"type": "text", "text": user_text}]}],
                )
                content_text = ""
                for block in (resp.content or []):
                    if getattr(block, "type", "") == "text":
                        content_text += getattr(block, "text", "")
                data = safe_parse_llm_json(content_text)
                top = data.get("top_candidates", [])
                if top:
                    best = max(top, key=lambda x: float(x.get("probability", 0.0)))
                    return {
                        "prediction": best.get("name"),
                        "confidence": float(best.get("probability", 0.0)),
                        "rationale": (best.get("rationale") or "") + (" " + (data.get("note") or "")),
                        "top_candidates": top,
                    }
            return {"prediction": None, "confidence": 0.0, "rationale": data.get("note", "Nieprawidłowy format odpowiedzi LLM (brak poprawnego JSON).")}
        except Exception as e:
            return {"prediction": None, "confidence": 0.0, "rationale": f"Błąd LLM (Anthropic): {e}"}

    if LLM_PROVIDER == "openai" and openai_client:
        try:
            user_text = build_user_text(prompt, names, ascii_fallback=False)
            completion = openai_client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": normalize_text("Jesteś precyzyjnym analitykiem konkursowym, który zwraca ściśle sformatowany JSON.")},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.4,
            )
            data = safe_parse_llm_json(completion.choices[0].message.content)
            top = data.get("top_candidates", [])
            if top:
                best = max(top, key=lambda x: float(x.get("probability", 0.0)))
                return {
                    "prediction": best.get("name"),
                    "confidence": float(best.get("probability", 0.0)),
                    "rationale": (best.get("rationale") or "") + (" " + (data.get("note") or "")),
                    "top_candidates": top,
                }
            return {"prediction": None, "confidence": 0.0, "rationale": data.get("note", "Nieprawidłowy format odpowiedzi LLM (brak poprawnego JSON).")}
        except Exception as e:
            return {"prediction": None, "confidence": 0.0, "rationale": f"Błąd LLM (OpenAI): {e}"}

    import random
    candidate = random.choice(participants) if participants else {}
    return {
        "prediction": candidate.get("name"),
        "confidence": 0.15 if candidate else 0.0,
        "rationale": "Fallback bez LLM (losowy wybór z listy uczestników)." if candidate else "Brak uczestników do predykcji."
    }