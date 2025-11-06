from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

documents = [
    "The 13th International Ignacy Jan Paderewski Piano Competition is held in Bydgoszcz, Poland, from November 9 to 23, 2025.",
    "Schedule: November 9 - Inaugural Concert; November 10-13 - Stage I; November 14-16 - Stage II; November 18-19 - Semi-Final; November 21-22 - Final; November 23 - Awards.",
    "Prizes: 1st €40,000; 2nd €25,000; 3rd €15,000; 4th €10,000; 5th €5,000.",
    "Repertoire: Preliminary (Etudes, sonata), Stage I (style diversity), Stage II (Paderewski + free), Semi-Final (Herdzin piece + Mozart concerto), Final (major concerto).",
]
_vectorizer = TfidfVectorizer()
_doc_vectors = _vectorizer.fit_transform(documents)

def retrieve_relevant_docs(query: str, top_k: int = 3) -> List[str]:
    qv = _vectorizer.transform([query])
    sims = cosine_similarity(qv, _doc_vectors).flatten()
    top_idx = np.argsort(sims)[-top_k:][::-1]
    return [documents[i] for i in top_idx]

def generate_response(query: str, relevant_docs: List[str]) -> str:
    cleaned = [d for d in relevant_docs if "predictions:" not in d.lower() and "prognoza:" not in d.lower()]
    context = "\n".join(cleaned) if cleaned else "Brak dopasowanego kontekstu."
    return f"Informacje z kontekstu RAG:\n{context}"