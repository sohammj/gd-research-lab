# server.py
import os, json, re, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

from gemini import analyze_prompt_with_gemini
from google.generativeai import GenerativeModel

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
UA = os.environ.get("HTTP_USER_AGENT", "gd-research-lab/1.0 (+local)")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": datetime.utcnow().isoformat() + "Z"})


def _http_json(url, params=None, timeout=15):
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _call_gemini_json(prompt: str):
    gm = GenerativeModel(GEMINI_MODEL)
    resp = gm.generate_content(prompt)
    txt = getattr(resp, "text", None)
    if not txt and getattr(resp, "candidates", None):
        for c in resp.candidates:
            if getattr(c, "content", None) and getattr(c.content, "parts", None):
                maybe = "".join(getattr(p, "text", "") for p in c.content.parts)
                if maybe:
                    txt = maybe
                    break
    if not txt:
        return {}
    t = txt.strip()
    if t.startswith("```json"):
        t = t[7:]
    elif t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    try:
        return json.loads(t.strip())
    except Exception:
        return {}


# ---------- STEP 1: Critique ----------
@app.post("/api/critique")
def critique():
    idea = (request.get_json() or {}).get("idea", "").strip()
    if not idea:
        return jsonify({"error": "idea is required"}), 400

    analysis = analyze_prompt_with_gemini(idea)
    prompt = f"""
Return ONLY JSON (no prose) with this exact structure:
{{
  "meta": {{"title":"","description":"","domain":""}},
  "scores": {{"novelty":0,"feasibility":0,"impact":0,"overall":0}},
  "reasons": {{"noveltyReason":"","feasibilityReason":"","impactReason":""}},
  "gaps": [],
  "suggestions": [],
  "verdict": ""
}}
Research idea: "{idea}"
"""
    out = _call_gemini_json(prompt) or {}
    out.setdefault("meta", {})
    out["meta"].setdefault("title", idea[:120])
    out["meta"].setdefault("description", "Automated critique & scoring from Gemini.")
    out["meta"].setdefault("domain", ", ".join(analysis.get("main_topics", []))[:120])
    return jsonify(out)


# ---------- STEP 2: Literature ----------
@app.post("/api/literature")
def literature():
    idea = (request.get_json() or {}).get("idea", "").strip()
    if not idea:
        return jsonify({"error": "idea is required"}), 400

    analysis = analyze_prompt_with_gemini(idea)
    query = " ".join(
        analysis.get("academic_terms")
        or analysis.get("search_terms")
        or [idea]
    )

    # OpenAlex (papers)
    key_papers = []
    try:
        j = _http_json(
            "https://api.openalex.org/works",
            {"search": query, "per_page": 10, "sort": "relevance_score:desc"},
        )
        for w in j.get("results", []):
            key_papers.append(
                {
                    "title": w.get("display_name"),
                    "venue": (w.get("host_venue") or {}).get("display_name") or "",
                    "year": w.get("publication_year") or "",
                    "link": (w.get("primary_location") or {}).get("landing_page_url")
                    or w.get("id"),
                }
            )
    except Exception as e:
        print("OpenAlex error:", e)

    # arXiv (Atom feed -> quick parse for title/link)
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "start": 0, "max_results": 10},
            headers={"User-Agent": UA},
            timeout=15,
        )
        if r.ok:
            entries = re.findall(r"<entry>(.*?)</entry>", r.text, flags=re.S)
            for e in entries:
                t = re.search(r"<title>(.*?)</title>", e, flags=re.S)
                l = re.search(
                    r'<link rel="alternate" type="text/html" href="(.*?)"', e
                )
                if t:
                    key_papers.append(
                        {
                            "title": re.sub(r"\s+", " ", t.group(1)).strip(),
                            "venue": "arXiv",
                            "year": "",
                            "link": l.group(1) if l else "",
                        }
                    )
    except Exception as e:
        print("arXiv error:", e)

    # Ask Gemini to organize the head (questions/gaps/etc.) based on idea + papers
    organize_prompt = f"""
Return ONLY JSON with:
{{
  "meta": {{"title":"","description":"","domain":""}},
  "research_questions": [], "niches": [], "methodologies": [],
  "trends": [], "major_gaps": [], "emerging_trends": [], "opportunities": []
}}
Idea: "{idea}"
Papers: {json.dumps(key_papers, ensure_ascii=False)}
"""
    head = _call_gemini_json(organize_prompt) or {}
    head.setdefault("meta", {})
    head["meta"].setdefault("title", f"Literature & Resources for: {idea}")
    head["meta"].setdefault("description", "Auto-curated snapshot.")
    head["meta"].setdefault("domain", ", ".join(analysis.get("main_topics", []) or ["general"]))

    return jsonify(
        {
            **head,
            "key_papers": key_papers,
            "datasets": [],  # plug a dataset API here if you have one
            "tools": ["PyTorch", "scikit-learn", "HuggingFace", "Weights & Biases"],
            "venues": ["NeurIPS", "ICLR", "ICML", "KDD", "Nature"],
        }
    )


# ---------- STEP 3: Community Trends ----------
@app.post("/api/community")
def community():
    idea = (request.get_json() or {}).get("idea", "").strip()
    if not idea:
        return jsonify({"error": "idea is required"}), 400

    analysis = analyze_prompt_with_gemini(idea)
    q = " ".join(analysis.get("reddit_queries") or analysis.get("search_terms") or [idea])

    # Reddit (no-auth JSON)
    reddit = []
    try:
        r = requests.get(
            "https://www.reddit.com/search.json",
            params={"q": q, "sort": "relevance", "t": "year", "limit": 10},
            headers={"User-Agent": UA},
            timeout=15,
        )
        if r.ok:
            data = r.json()
            for ch in data.get("data", {}).get("children", []):
                d = ch.get("data", {})
                if d.get("title") and d.get("permalink"):
                    reddit.append(
                        {"title": d["title"], "link": f"https://www.reddit.com{d['permalink']}"}
                    )
    except Exception as e:
        print("Reddit error:", e)

    # Hacker News (Algolia)
    hn = []
    try:
        j = _http_json(
            "https://hn.algolia.com/api/v1/search",
            {"query": q, "tags": "story", "hitsPerPage": 10},
        )
        for h in j.get("hits", []):
            title = h.get("title")
            url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            if title and url:
                hn.append({"title": title, "link": url})
    except Exception as e:
        print("HN error:", e)

    # Trend summary from titles via Gemini
    trend_prompt = f"""
Return ONLY JSON {{"trends":[]}} summarizing recurring themes from these thread titles.
Reddit: {json.dumps([t['title'] for t in reddit], ensure_ascii=False)}
HN: {json.dumps([t['title'] for t in hn], ensure_ascii=False)}
"""
    trends = _call_gemini_json(trend_prompt).get("trends", []) or []

    return jsonify({"trends": trends, "threads": {"reddit": reddit, "hn": hn}})


# ---------- STEP 4: Directions & Resources ----------
@app.post("/api/directions")
def directions():
    idea = (request.get_json() or {}).get("idea", "").strip()
    if not idea:
        return jsonify({"error": "idea is required"}), 400

    prompt = f"""
Return ONLY JSON with:
{{
  "summary": "",
  "directions": [],
  "resources": {{
    "tools": [],
    "checklists": [],
    "datasets": [{{"name":"","link":""}}],
    "papers": [{{"title":"","link":""}}]
  }}
}}
Idea: "{idea}"
"""
    return jsonify(_call_gemini_json(prompt) or {})


# ---------- STEP 5: Draft Outline ----------
@app.post("/api/draft")
def draft():
    idea = (request.get_json() or {}).get("idea", "").strip()
    if not idea:
        return jsonify({"error": "idea is required"}), 400

    prompt = f"""
Return ONLY JSON:
{{
  "title": "",
  "outline": [
    {{"section":"Abstract","bullets":[]}},
    {{"section":"Introduction","bullets":[]}},
    {{"section":"Related Work","bullets":[]}},
    {{"section":"Methods","bullets":[]}},
    {{"section":"Results","bullets":[]}},
    {{"section":"Discussion","bullets":[]}},
    {{"section":"Conclusion","bullets":[]}}
  ]
}}
Idea: "{idea}"
"""
    return jsonify(_call_gemini_json(prompt) or {})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)