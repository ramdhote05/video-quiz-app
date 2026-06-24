"""
Step 3 of the pipeline: turn the raw transcript into a concise, structured
summary (TL;DR + key bullet points + key topics).

Two backends are supported, chosen automatically:

1. GROQ (cloud, free tier) - used when a GROQ_API_KEY is configured.
   Groq hosts open models (Mixtral / Llama family) and returns very fast,
   high quality structured summaries. Get a free key at console.groq.com
   and put it in your .env file.

2. LOCAL (offline, zero cost) - used automatically when no API key is set.
   Runs a small Hugging Face summarization model (distilbart-cnn) on your
   own machine. Lower quality than a 7B+ LLM, but needs no internet after
   the first model download and no account/API key at all.
"""
import json
import re
import textwrap

_local_pipeline_cache = {}


# --------------------------------------------------------------------------- #
# Backend 1: Groq cloud (Mixtral / Llama)
# --------------------------------------------------------------------------- #
def _summarize_with_groq(transcript: str, api_key: str, model: str) -> dict:
    from groq import Groq

    client = Groq(api_key=api_key)

    prompt = textwrap.dedent(f"""
        You are an expert teaching assistant. Read the lecture transcript below
        and produce a JSON object with exactly these keys:

        - "tldr": one or two sentence overview of the whole video.
        - "key_topics": a list of 3-6 short topic names covered in the video.
        - "bullets": a list of 6-12 concise bullet points capturing the most
          important facts, definitions, and explanations a student should
          remember for an exam. Each bullet should stand on its own.

        Respond with ONLY the JSON object, no other text, no markdown fences.

        TRANSCRIPT:
        \"\"\"{transcript[:15000]}\"\"\"
    """).strip()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    return _parse_json_block(raw)


# --------------------------------------------------------------------------- #
# Backend 2: local / offline Hugging Face model
# --------------------------------------------------------------------------- #
def _get_local_pipeline(model_name: str):
    if model_name not in _local_pipeline_cache:
        from transformers import pipeline
        _local_pipeline_cache[model_name] = pipeline("summarization", model=model_name)
    return _local_pipeline_cache[model_name]


def _chunk_text(text: str, max_words: int = 600):
    words = text.split()
    for i in range(0, len(words), max_words):
        yield " ".join(words[i:i + max_words])


def _summarize_with_local_model(transcript: str, model_name: str) -> dict:
    summarizer = _get_local_pipeline(model_name)

    chunk_summaries = []
    for chunk in _chunk_text(transcript):
        if not chunk.strip():
            continue
        result = summarizer(chunk, max_length=120, min_length=30, do_sample=False)
        chunk_summaries.append(result[0]["summary_text"].strip())

    combined = " ".join(chunk_summaries)

    # Turn the combined summary into bullet-style sentences.
    sentences = re.split(r"(?<=[.!?])\s+", combined)
    bullets = [s.strip() for s in sentences if len(s.strip()) > 8]

    tldr = bullets[0] if bullets else "Summary unavailable."
    return {
        "tldr": tldr,
        "key_topics": [],
        "bullets": bullets[:12] if bullets else ["No summary could be generated."],
    }


def _summarize_with_extractive_fallback(transcript: str) -> dict:
    """Dependency-free summary used when cloud and Hugging Face backends fail."""
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", transcript.replace("\n", " "))
        if len(s.strip()) > 20
    ]
    if not sentences:
        short_text = transcript.strip()
        return {
            "tldr": short_text[:240] if short_text else "Summary unavailable.",
            "key_topics": [],
            "bullets": [short_text[:300]] if short_text else ["No summary could be generated."],
        }

    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", transcript.lower())
    stopwords = {
        "about", "after", "also", "because", "been", "being", "between", "could",
        "from", "have", "here", "into", "more", "most", "only", "other", "should",
        "some", "such", "than", "that", "their", "then", "there", "these", "they",
        "this", "those", "through", "very", "were", "what", "when", "where", "which",
        "while", "with", "would", "your",
    }
    frequencies = {}
    for word in words:
        if word not in stopwords:
            frequencies[word] = frequencies.get(word, 0) + 1

    def score(sentence: str) -> int:
        return sum(frequencies.get(w.lower(), 0) for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", sentence))

    ranked = sorted(enumerate(sentences), key=lambda item: score(item[1]), reverse=True)
    selected_indexes = sorted(i for i, _ in ranked[:8])
    bullets = [sentences[i] for i in selected_indexes]
    topic_words = sorted(frequencies, key=frequencies.get, reverse=True)[:6]

    return {
        "tldr": " ".join(bullets[:2]) if bullets else sentences[0],
        "key_topics": [word.title() for word in topic_words],
        "bullets": bullets or [sentences[0]],
    }


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _parse_json_block(raw: str) -> dict:
    """LLMs sometimes wrap JSON in markdown fences or add stray text -- strip that out."""
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def summarize(transcript: str, groq_api_key: str = "", groq_model: str = "mixtral-8x7b-32768",
              local_model_name: str = "sshleifer/distilbart-cnn-12-6") -> dict:
    """
    Returns a dict: {"tldr": str, "key_topics": [str], "bullets": [str]}
    Automatically uses Groq if an API key is present, otherwise falls back
    to the local offline summarizer.
    """
    if not transcript or not transcript.strip():
        return {"tldr": "", "key_topics": [], "bullets": []}

    if groq_api_key:
        try:
            return _summarize_with_groq(transcript, groq_api_key, groq_model)
        except Exception:
            # If the cloud call fails for any reason (bad key, rate limit, no
            # internet), gracefully degrade to the local model instead of
            # crashing the whole pipeline.
            pass

    try:
        return _summarize_with_local_model(transcript, local_model_name)
    except Exception:
        return _summarize_with_extractive_fallback(transcript)
