# gemini.py
import os, json
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

DEFAULT_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")


def _extract_json(text: str):
    """Pull JSON out of plain text or fenced blocks."""
    if not text:
        return {}
    t = text.strip()
    if t.startswith("```json"):
        t = t[7:]
        if t.endswith("```"):
            t = t[:-3]
    elif t.startswith("```"):
        t = t[3:]
        if t.endswith("```"):
            t = t[:-3]
    try:
        return json.loads(t.strip())
    except Exception:
        return {}


def analyze_prompt_with_gemini(prompt: str, model_name: str = DEFAULT_MODEL_NAME):
    """
    Ask Gemini to extract search scaffolding for downstream APIs.
    Always returns a dict with all expected keys (sensible fallbacks).
    """
    try:
        gm = genai.GenerativeModel(model_name)
        ask = f"""
Analyze this user prompt and return ONLY valid JSON with keys:
main_topics, search_terms, related_concepts, academic_terms,
github_queries, reddit_queries, kaggle_queries, medium_queries, quora_queries.

User prompt: "{prompt}"
"""
        resp = gm.generate_content(ask)

        text = getattr(resp, "text", None)
        if not text and getattr(resp, "candidates", None):
            for c in resp.candidates:
                if getattr(c, "content", None) and getattr(c.content, "parts", None):
                    text = "".join(getattr(p, "text", "") for p in c.content.parts)
                    if text:
                        break

        data = _extract_json(text or "")

        # sensible fallbacks
        data.setdefault("main_topics", prompt.split()[:3])
        data.setdefault("search_terms", [prompt])
        for k in [
            "related_concepts",
            "academic_terms",
            "github_queries",
            "reddit_queries",
            "kaggle_queries",
            "medium_queries",
            "quora_queries",
        ]:
            data.setdefault(k, [])

        return data

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return {
            "main_topics": prompt.split()[:3],
            "search_terms": [prompt],
            "related_concepts": [],
            "academic_terms": [prompt],
            "github_queries": [prompt],
            "reddit_queries": [prompt],
            "kaggle_queries": [prompt],
            "medium_queries": [prompt],
            "quora_queries": [prompt],
        }