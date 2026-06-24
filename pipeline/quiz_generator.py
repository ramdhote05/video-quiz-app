"""
Step 4 of the pipeline: turn the summary/transcript into a multiple-choice
quiz so learners can self-test what they just watched.

Same dual-backend pattern as summarizer.py:
- GROQ (cloud, free tier): asks an LLM to write well-formed MCQs with
  plausible distractors and short explanations. Much higher quality.
- LOCAL (offline): a simple cloze-deletion generator that blanks out a key
  term in a summary sentence and builds distractors from other terms found
  in the transcript. No extra models, no internet, works anywhere.
"""
import json
import random
import re
import textwrap

from .summarizer import _parse_json_block  # reuse the same robust JSON cleanup

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "to", "of", "in", "on", "at", "for", "with", "as", "by",
    "that", "this", "these", "those", "it", "its", "from", "into", "such",
    "which", "who", "whom", "what", "when", "where", "why", "how", "than",
    "then", "so", "if", "not", "no", "we", "you", "they", "he", "she", "i",
    "his", "her", "their", "our", "your", "my", "can", "will", "would",
    "could", "should", "about", "also", "there", "here", "very", "more",
    "most", "some", "any", "each", "all", "one", "two", "three",
}


# --------------------------------------------------------------------------- #
# Backend 1: Groq cloud (Mixtral / Llama)
# --------------------------------------------------------------------------- #
def _generate_with_groq(transcript: str, summary_bullets: list, api_key: str,
                         model: str, num_questions: int) -> list:
    from groq import Groq

    client = Groq(api_key=api_key)
    bullets_text = "\n".join(f"- {b}" for b in summary_bullets)

    prompt = textwrap.dedent(f"""
        You are writing a self-revision quiz for a student who just watched an
        educational video. Using the summary and transcript below, write
        exactly {num_questions} multiple-choice questions.

        Return ONLY a JSON array (no markdown fences, no extra text). Each
        element must be an object with these exact keys:
        - "question": string
        - "options": array of exactly 4 short strings
        - "correct_index": integer 0-3, index into "options" of the right answer
        - "explanation": one sentence explaining why that answer is correct

        Make questions test understanding, not just word-matching. Vary the
        position of the correct answer across questions.

        SUMMARY:
        {bullets_text}

        TRANSCRIPT (for extra detail):
        \"\"\"{transcript[:8000]}\"\"\"
    """).strip()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    raw = response.choices[0].message.content.strip()
    parsed = _parse_json_array(raw)
    return _validate_questions(parsed)


def _parse_json_array(raw: str) -> list:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


def _validate_questions(questions: list) -> list:
    """Keep only well-formed questions so a malformed LLM response can't break the UI."""
    valid = []
    for q in questions:
        if (
            isinstance(q, dict)
            and isinstance(q.get("question"), str)
            and isinstance(q.get("options"), list)
            and len(q["options"]) == 4
            and isinstance(q.get("correct_index"), int)
            and 0 <= q["correct_index"] <= 3
        ):
            q.setdefault("explanation", "")
            valid.append(q)
    return valid


# --------------------------------------------------------------------------- #
# Backend 2: local / offline rule-based cloze generator
# --------------------------------------------------------------------------- #
def _candidate_keywords(text: str) -> list:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text)
    return [w for w in words if w.lower() not in _STOPWORDS]


def _generate_locally(transcript: str, summary_bullets: list, num_questions: int) -> list:
    pool = _candidate_keywords(transcript)
    if len(pool) < 4 or not summary_bullets:
        return []

    questions = []
    used_sentences = set()
    random.shuffle(summary_bullets)

    for sentence in summary_bullets:
        if len(questions) >= num_questions:
            break
        if sentence in used_sentences:
            continue
        words_in_sentence = [w for w in _candidate_keywords(sentence)]
        if not words_in_sentence:
            continue

        # Pick the longest keyword in this sentence as the "answer" to blank out.
        answer = max(words_in_sentence, key=len)
        blanked = re.sub(rf"\b{re.escape(answer)}\b", "_____", sentence, count=1, flags=re.IGNORECASE)
        if "_____" not in blanked:
            continue

        # Build 3 distractors: other keywords of similar-ish length, not equal to the answer.
        distractor_pool = [w for w in pool if w.lower() != answer.lower()]
        random.shuffle(distractor_pool)
        distractors = []
        for w in distractor_pool:
            if w.lower() not in [d.lower() for d in distractors] and w.lower() != answer.lower():
                distractors.append(w)
            if len(distractors) == 3:
                break
        if len(distractors) < 3:
            continue

        options = distractors + [answer]
        random.shuffle(options)
        correct_index = options.index(answer)

        questions.append({
            "question": f"Fill in the blank: \"{blanked}\"",
            "options": options,
            "correct_index": correct_index,
            "explanation": f"The original sentence states: \"{sentence}\"",
        })
        used_sentences.add(sentence)

    return questions


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def generate_quiz(transcript: str, summary_bullets: list, groq_api_key: str = "",
                   groq_model: str = "mixtral-8x7b-32768", num_questions: int = 5) -> list:
    """
    Returns a list of question dicts:
        {"question": str, "options": [str x4], "correct_index": int, "explanation": str}
    """
    if groq_api_key:
        try:
            questions = _generate_with_groq(transcript, summary_bullets, groq_api_key,
                                             groq_model, num_questions)
            if questions:
                return questions
        except Exception:
            pass  # fall through to local generator

    return _generate_locally(transcript, summary_bullets, num_questions)
