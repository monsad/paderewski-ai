from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from config import PADEREWSKI_BASE_URL, get_llm_diagnostics
from schemas import QueryRequest
from services.web import get_dynamic_participants, get_dynamic_jury, fetch_web_info, fetch_youtube_videos
from services.llm import llm_predict_winner
from services.rag import retrieve_relevant_docs, generate_response

router = APIRouter()

@router.get("/debug_llm")
async def debug_llm():
    return get_llm_diagnostics()

@router.get("/participants")
async def participants():
    people = get_dynamic_participants()
    return people or []

@router.get("/jury")
async def jury():
    people = get_dynamic_jury()
    return people or []

@router.get("/history")
async def history():
    text = fetch_web_info(PADEREWSKI_BASE_URL)
    return {"source": PADEREWSKI_BASE_URL, "excerpt": text}

@router.get("/predict_winner")
async def predict_winner():
    people = get_dynamic_participants()
    return llm_predict_winner(people)

@router.post("/ask")
async def ask(req: QueryRequest):
    q = (req.query or "").lower().strip()
    if not q:
        return {"response": "Brak pytania."}

    participants_keywords = ["uczestnicy", "uczestnik", "biorą udział", "bierze udział", "lista uczestników", "kto bierze udzial", "kto bierze udział"]
    jury_keywords = ["jury", "juror", "jurorzy", "lista jury"]
    history_keywords = ["historia", "przeszłe edycje", "archiwum", "historyczne"]
    winner_keywords = ["kto wygra", "zwycięzca", "winner", "kto będzie najlepszy", "kto bedzie najlepszy"]

    if any(k in q for k in participants_keywords):
        people = get_dynamic_participants()
        lines = [f"- {p.get('name','')}" + (f" ({p.get('country')})" if p.get('country') else "") for p in people]
        return {"response": "Uczestnicy:\n" + ("\n".join(lines) if lines else "Brak danych.")}

    if any(k in q for k in jury_keywords):
        people = get_dynamic_jury()
        def label(j):
            role = f" — {j.get('role')}" if j.get('role') else ""
            country = f" ({j.get('country')})" if j.get('country') else ""
            return f"- {j.get('name','')}{role}{country}"
        lines = [label(j) for j in people]
        return {"response": "Jury:\n" + ("\n".join(lines) if lines else "Brak danych.")}

    if any(k in q for k in history_keywords):
        excerpt = fetch_web_info(PADEREWSKI_BASE_URL)
        return {"response": f"Historia — skrót:\n{excerpt}\n\nŹródło: {PADEREWSKI_BASE_URL}"}

    if any(k in q for k in winner_keywords):
        people = get_dynamic_participants()
        pred = llm_predict_winner(people)
        if pred.get("prediction"):
            return {"response": f"Prognoza (LLM): {pred['prediction']}\nPewność: {(pred['confidence']*100):.1f}%\n{pred.get('rationale','')}"}
        return {"response": f"Brak predykcji — {pred.get('rationale','')}"}

    docs = retrieve_relevant_docs(req.query)
    response = generate_response(req.query, docs)

    if any(k in q for k in ["youtube", "wideo", "video", "film"]):
        vids = fetch_youtube_videos()
        response += "\nYouTube:\n" + "\n".join([f"{t}: {u}" for t, u in vids])

    return {"response": response}

@router.get("/", response_class=HTMLResponse)
async def index():
    return """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <title>Paderewski AI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, Arial, sans-serif; margin: 20px; color: #111; }
    h1 { margin-bottom: 8px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; }
    .list { margin-top: 8px; }
    .item { padding: 6px 0; border-bottom: 1px dashed #eee; }
    textarea { width: 100%; min-height: 80px; }
    button { padding: 8px 12px; border-radius: 6px; border: 1px solid #aaa; background: #fafafa; cursor: pointer; }
    button:hover { background: #f0f0f0; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>Paderewski AI</h1>
  <div class="grid">
    <div class="card">
      <h2>Zapytaj (RAG/LLM)</h2>
      <textarea id="query" placeholder="np. 'kto wygra', 'lista uczestników'"></textarea>
      <div style="margin-top:8px;"><button onclick="ask()">Wyślij</button></div>
      <h3>Odpowiedź</h3>
      <div id="answer" class="mono"></div>
    </div>
    <div class="card">
      <h2>Prognoza zwycięzcy</h2>
      <div style="margin-top:8px;"><button onclick="loadPrediction()">Pobierz prognozę</button></div>
      <div id="prediction" class="mono"></div>
    </div>
    <div class="card">
      <h2>Uczestnicy</h2>
      <div id="participants" class="list"></div>
    </div>
    <div class="card">
      <h2>Jury</h2>
      <div id="jury" class="list"></div>
    </div>
    <div class="card" style="grid-column: 1 / -1;">
      <h2>Historia konkursu (skrót)</h2>
      <div style="margin-top:8px;"><button onclick="loadHistory()">Załaduj</button></div>
      <div id="history" class="mono"></div>
    </div>
  </div>
<script>
async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.json();
}
async function ask() {
  const q = document.getElementById('query').value;
  try {
    const data = await fetchJSON('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q })
    });
    document.getElementById('answer').textContent = data.response || JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('answer').textContent = 'Błąd: ' + e.message;
  }
}
async function loadPrediction() {
  try {
    const data = await fetchJSON('/predict_winner');
    const predictionText = data.prediction ? ('Prognoza: ' + data.prediction + '\\n') : 'Brak predykcji\\n';
    const confidenceText = (typeof data.confidence === 'number')
      ? ('Pewność: ' + (data.confidence * 100).toFixed(1) + '%\\n\\n')
      : '';
    const rationaleText = data.rationale || '';
    document.getElementById('prediction').textContent = predictionText + confidenceText + rationaleText;
  } catch (e) {
    document.getElementById('prediction').textContent = 'Błąd: ' + e.message;
  }
}
async function loadParticipants() {
  try {
    const data = await fetchJSON('/participants');
    const container = document.getElementById('participants');
    container.innerHTML = (Array.isArray(data) ? data : []).map(p =>
      '<div class="item"><strong>' + (p.name || '') + '</strong>' +
      (p.country ? ' (' + p.country + ')' : '') +
      (p.bio ? '<br />' + p.bio : '') +
      '</div>'
    ).join('');
  } catch (e) {
    document.getElementById('participants').textContent = 'Błąd: ' + e.message;
  }
}
async function loadJury() {
  try {
    const data = await fetchJSON('/jury');
    const container = document.getElementById('jury');
    container.innerHTML = (Array.isArray(data) ? data : []).map(j =>
      '<div class="item"><strong>' + (j.name || '') + '</strong>' +
      (j.role ? ' — ' + j.role : '') +
      (j.country ? ' (' + j.country + ')' : '') +
      (j.bio ? '<br />' + j.bio : '') +
      '</div>'
    ).join('');
  } catch (e) {
    document.getElementById('jury').textContent = 'Błąd: ' + e.message;
  }
}
async function loadHistory() {
  try {
    const data = await fetchJSON('/history');
    document.getElementById('history').textContent = (data.excerpt || '') + '\\n\\nŹródło: ' + (data.source || '');
  } catch (e) {
    document.getElementById('history').textContent = 'Błąd: ' + e.message;
  }
}
loadParticipants();
loadJury();
</script>
</body></html>
"""