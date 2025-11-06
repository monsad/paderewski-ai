# Paderewski AI — Uruchomienie

## Wymagania
- Python 3.11+
- `pip`

## Instalacja zależności
```bash
python -m pip install --upgrade pip
```
```bash
pip install fastapi uvicorn requests beautifulsoup4 scikit-learn numpy anthropic openai python-dotenv
```

## Konfiguracja środowiska
Zalecane: plik `.env` w katalogu projektu (ładowany automatycznie).
```plaintext
ANTHROPIC_API_KEY=TWÓJ_KLUCZ
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5-20250929

PADEREWSKI_BASE_URL=https://paderewskicompetition.pl/
PARTICIPANTS_URL=https://www.konkurspaderewskiego.pl/uczestnicy-xiii-konkursu-2025/
JURY_URL=https://paderewskicompetition.pl/jury/
YOUTUBE_API_KEY=
```

Alternatywnie ustaw w powłoce przed startem:
```bash
export ANTHROPIC_API_KEY="TWÓJ_KLUCZ"
```
```bash
export LLM_PROVIDER="anthropic"
```
```bash
export LLM_MODEL="claude-sonnet-4-5-20250929"
```

## Uruchomienie
```bash
uvicorn app:app --host 0.0.0.0 --port 8011
```

## Szybka weryfikacja
Diagnostyka LLM:
```bash
curl -s http://localhost:8011/debug_llm | jq
```

Prognoza zwycięzcy:
```bash
curl -s http://localhost:8011/predict_winner | jq
```

UI w przeglądarce:
- Otwórz: `http://localhost:8011/`

Uwagi:
- Jeśli nie ustawisz klucza i modelu LLM, aplikacja wykona prosty fallback bez modelu.
- Importy używają modułów: `config.py`, `utils/`, `services/`, `routes.py` oraz bootstrapu `app.py`.
