"""
chatbot_engine.py
─────────────────
Two-layer chatbot:
  1. Primary  → Claude API (claude-haiku)
  2. Fallback → Improved TF-IDF (top-3 merged, threshold 0.05, keyword boost)
"""

import os, re, json
from urllib import request as urlreq, error as urlerr
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CSV_PATH = os.path.join(os.path.dirname(__file__), "christ_university_ncr_qa_completed.csv")

_vectorizer   = None
_tfidf_matrix = None
_answers      = []
_questions    = []
_kb_text      = ""


def _clean(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _fix(s: str) -> str:
    return (str(s).replace("\x92","'").replace("\x96","–")
                  .replace("\xa0"," ").replace("\x95","•").strip())


def load_knowledge_base():
    global _vectorizer, _tfidf_matrix, _answers, _questions, _kb_text

    try:
        df = pd.read_csv(CSV_PATH, encoding="cp1252", on_bad_lines="skip")
    except Exception:
        df = pd.read_csv(CSV_PATH, encoding="utf-8", errors="replace", on_bad_lines="skip")

    df.columns = [c.strip() for c in df.columns]
    df = df[["Question", "Answer"]].dropna()
    df = df[df["Question"].str.strip() != "Question"]
    df = df[df["Answer"].str.strip() != ""]
    df = df.drop_duplicates(subset="Answer")   # remove duplicate answers

    _questions = df["Question"].tolist()
    _answers   = [_fix(a) for a in df["Answer"].tolist()]

    lines = []
    for q, a in zip(_questions[:250], _answers[:250]):
        lines.append(f"Q: {q}\nA: {a}")
    _kb_text = "\n\n".join(lines)

    clean_qs = [_clean(q) for q in _questions]
    _vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_df=0.95, min_df=1,
        sublinear_tf=True,
    )
    _tfidf_matrix = _vectorizer.fit_transform(clean_qs)
    print(f"✅  Chatbot loaded {len(_questions)} unique Q&A pairs.")


def _call_claude(user_message: str, is_candidate: bool = False) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    if is_candidate:
        system = f"""You are the official admissions assistant for Christ (Deemed to be University) NCR Campus.
Address: Mariam Nagar, Meerut Road, Ghaziabad - 201003, Uttar Pradesh.
Academic Year: 2026-27.
Help prospective students with admissions, courses, fees, eligibility, scholarships, and campus life.
Be warm, welcoming and give detailed, structured answers.

Knowledge base:
{_kb_text}

Rules:
- ALWAYS give a helpful answer from the knowledge base first. Never reply with ONLY "contact us".
- Use bullet points for lists of items.
- Keep answers between 3-8 sentences or bullet points.
- End with admissions contact only if the query needs very specific details."""
    else:
        system = f"""You are the Christ University NCR Campus Help Desk AI for 2026-27.
Help current students, teachers and staff with university queries.

Knowledge base:
{_kb_text}

Rules:
- Always give the best answer you can from the knowledge base.
- Use bullet points for lists.
- Keep answers 3-6 sentences.
- Suggest a support ticket only AFTER answering."""

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 500,
        "system": system,
        "messages": [{"role": "user", "content": user_message}]
    }).encode()

    req = urlreq.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )
    try:
        with urlreq.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read())["content"][0]["text"].strip()
    except Exception as e:
        print(f"⚠️  Claude API error: {e}")
        return None


def _tfidf_response(user_message: str, is_candidate: bool = False) -> str:
    if _vectorizer is None:
        return "Chatbot is loading. Please try again in a moment."

    clean_msg = _clean(user_message)
    query_vec = _vectorizer.transform([clean_msg])
    scores    = cosine_similarity(query_vec, _tfidf_matrix).flatten()

    top_indices = np.argsort(scores)[::-1][:3]
    top_scores  = scores[top_indices]

    THRESHOLD = 0.05   # very permissive — answer almost everything

    if top_scores[0] < THRESHOLD:
        # Last resort keyword scan
        keywords = [k for k in clean_msg.split() if len(k) > 3]
        for i, q in enumerate(_questions):
            if any(k in q.lower() for k in keywords):
                return _answers[i]

        if is_candidate:
            return (
                "Christ University NCR Campus offers UG and PG programmes in Commerce, Management, "
                "Law, Sciences, Social Sciences, and Arts & Humanities. Popular courses: BBA, BCA, "
                "BCom, BA LLB, BSc, MBA. For 2026-27 admissions visit ncr.christuniversity.in or "
                "contact us at Mariam Nagar, Meerut Road, Ghaziabad - 201003."
            )
        return "I couldn't find a specific answer. Please raise a support ticket and our staff will help you shortly."

    seen, parts = set(), []
    for idx, score in zip(top_indices, top_scores):
        if score < THRESHOLD:
            break
        ans = _answers[idx]
        key = ans[:60]
        if key not in seen:
            seen.add(key)
            parts.append(ans)

    if len(parts) == 1:
        return parts[0]

    merged = parts[0]
    if len(parts) > 1 and parts[1][:60] not in merged:
        if len(parts[1]) < 300:
            merged += "\n\n" + parts[1]
    return merged


def get_response(user_message: str, is_candidate: bool = False) -> str:
    if _vectorizer is None:
        load_knowledge_base()

    claude_reply = _call_claude(user_message, is_candidate=is_candidate)
    if claude_reply:
        return claude_reply

    return _tfidf_response(user_message, is_candidate=is_candidate)