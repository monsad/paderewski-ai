from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup
import re

from config import PADEREWSKI_BASE_URL, PARTICIPANTS_URL, JURY_URL, YOUTUBE_API_KEY

def fetch_html(url: str, timeout: int = 12) -> Optional[str]:
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        return None
    return None

def fetch_web_info(url: str) -> str:
    html = fetch_html(url) or ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)[:1500]

def fetch_youtube_videos(query: str = "Paderewski Piano Competition 2025", max_results: int = 5) -> List[tuple]:
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "order": "date",
        "type": "video",
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(base_url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return [(it["snippet"]["title"], f"https://www.youtube.com/watch?v={it['id']['videoId']}") for it in data.get("items", [])]
        return [("Error", resp.text)]
    except Exception as e:
        return [("Error", str(e))]

def extract_names(text: str) -> List[str]:
    pattern = r"\b([A-ZŁŚĆŹŻ][a-ząćęłńóśźż]+(?:\s[A-Z][a-ząćęłńóśźż]+){0,3})\b"
    candidates = re.findall(pattern, text)
    blacklist = {"Schedule", "Jury", "Prizes", "Repertoire", "International", "Ignacy", "Paderewski", "Konkurs", "Międzynarodowy"}
    cleaned = []
    for c in candidates:
        if c in blacklist:
            continue
        parts = c.split()
        if len(parts) >= 2:
            cleaned.append(c)
    seen = set()
    ordered = []
    for c in cleaned:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered

def parse_names_from_html(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".entry-content") or soup.select_one("article") or soup
    text_chunks = []
    for sel in ["ul", "ol", "li", "p", "h2", "h3", "a", "span", "strong", ".wp-block-list li"]:
        for el in container.select(sel):
            t = el.get_text(" ", strip=True)
            if t:
                text_chunks.append(t)
    big = "\n".join(text_chunks)
    return extract_names(big)

def build_people_dicts(names: List[str], with_role: bool = False) -> List[Dict]:
    people = []
    for n in names:
        entry = {"name": n, "country": "", "bio": ""}
        if with_role:
            entry["role"] = None
        people.append(entry)
    return people

def parse_participants_konkurspaderewskiego(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".entry-content") or soup.select_one("article") or soup
    text_chunks = []
    for sel in ["ul", "ol", "li", "p", "h2", "h3", ".wp-block-list li", "strong", "a"]:
        for el in container.select(sel):
            t = el.get_text(" ", strip=True)
            if t:
                text_chunks.append(t)
    names = extract_names("\n".join(text_chunks))
    return build_people_dicts(names)

def parse_jury_paderewskicompetition(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".entry-content") or soup.select_one("article") or soup
    text_chunks = []
    for sel in ["ul", "ol", "li", "p", "h2", "h3", "a", "strong", ".wp-block-list li"]:
        for el in container.select(sel):
            t = el.get_text(" ", strip=True)
            if t:
                text_chunks.append(t)
    names = extract_names("\n".join(text_chunks))
    people = build_people_dicts(names, with_role=True)
    for p in people:
        p["role"] = None
    return people

def get_dynamic_participants() -> List[Dict]:
    html = fetch_html(PARTICIPANTS_URL)
    if html:
        people = parse_participants_konkurspaderewskiego(html)
        if people:
            return people
    candidates = []
    bases = [PADEREWSKI_BASE_URL.rstrip("/"), "https://www.konkurspaderewskiego.pl"]
    paths = ["/uczestnicy/", "/participants/", "/contestants/", "/list-of-participants/", "/"]
    for base in bases:
        for path in paths:
            candidates.append(f"{base.rstrip('/')}{path}")
    for url in candidates:
        h = fetch_html(url)
        if not h:
            continue
        names = parse_names_from_html(h)
        if names:
            return build_people_dicts(names)
    return []

def get_dynamic_jury() -> List[Dict]:
    html = fetch_html(JURY_URL)
    if html:
        people = parse_jury_paderewskicompetition(html)
        if people:
            return people
    candidates = []
    bases = [PADEREWSKI_BASE_URL.rstrip("/"), "https://www.konkurspaderewskiego.pl"]
    paths = ["/jury-xiii-konkursu-2025/", "/jury/", "/jurors/", "/komisja/", "/"]
    for base in bases:
        for path in paths:
            candidates.append(f"{base.rstrip('/')}{path}")
    for url in candidates:
        h = fetch_html(url)
        if not h:
            continue
        names = parse_names_from_html(h)
        if names:
            return build_people_dicts(names, with_role=True)
    return []