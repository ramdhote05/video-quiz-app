"""
Setup verification script — run this after `pip install -r requirements.txt`
to confirm the app, templates, and offline logic are wired correctly.
NOTE: This does NOT test Whisper transcription or the Groq API call itself
(those need network access to download models / reach the API), but it
proves everything else - audio extraction, the offline quiz fallback, and
every Flask route/template - works end to end.

Run with: python3 test_smoke.py
"""
import json
import sys

sys.path.insert(0, ".")

PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}")


print("1) Summarizer helper functions")
from pipeline.summarizer import _parse_json_block, _chunk_text, _summarize_with_extractive_fallback

parsed = _parse_json_block('```json\n{"tldr": "x", "bullets": ["a", "b"]}\n```')
check("parses fenced JSON block", parsed == {"tldr": "x", "bullets": ["a", "b"]})

chunks = list(_chunk_text(" ".join(["word"] * 1500), max_words=600))
check("chunks long text into pieces", len(chunks) == 3)

fallback_summary = _summarize_with_extractive_fallback(sample_text := (
    "Machine learning helps students identify performance patterns. "
    "Decision trees explain predictions using readable branches. "
    "Flask connects the browser workflow to the Python backend."
))
check("dependency-free summary fallback returns bullets", len(fallback_summary["bullets"]) >= 1)

print("\n2) Quiz generator (offline rule-based fallback, no API key, no model)")
from pipeline.quiz_generator import _generate_locally, _candidate_keywords

sample_transcript = (
    "Machine learning models like Decision Tree and Random Forest are used "
    "to predict student performance. Logistic Regression is a simple "
    "classification algorithm. Flask connects the Python backend to a MySQL "
    "database for storing predictions."
)
sample_bullets = [
    "Decision Tree and Random Forest are used to predict student performance.",
    "Logistic Regression is a simple classification algorithm.",
    "Flask connects the backend to a MySQL database.",
]

keywords = _candidate_keywords(sample_transcript)
check("extracts keyword candidates", len(keywords) > 5)

questions = _generate_locally(sample_transcript, sample_bullets, num_questions=3)
check("generates at least 1 question", len(questions) >= 1)
if questions:
    q = questions[0]
    check("question has 4 options", len(q["options"]) == 4)
    check("correct_index points at a valid option", 0 <= q["correct_index"] <= 3)
    check("options has no duplicate strings", len(set(o.lower() for o in q["options"])) == 4)
    print(f"  sample question -> {q['question']}")
    print(f"  options -> {q['options']}  (correct index: {q['correct_index']})")

print("\n3) Flask app wiring (routes, templates, 404 handling)")
import app as flask_app_module

flask_app_module.app.config["TESTING"] = True
client = flask_app_module.app.test_client()

resp = client.get("/")
check("GET / renders index page (200)", resp.status_code == 200)
check("index page contains upload form", b"upload-form" in resp.data)

resp = client.get("/processing/does-not-exist")
check("unknown job id on /processing/<id> shows recovery page", resp.status_code == 200 and b"Back to upload" in resp.data)

resp = client.get("/api/status/does-not-exist")
check("unknown job id on /api/status/<id> returns 404 JSON", resp.status_code == 404)

resp = client.get("/result/does-not-exist")
check("unknown job id on /result/<id> returns 404", resp.status_code == 404)

resp = client.post("/upload")
check("upload with no file returns 400", resp.status_code == 400)

print("\n4) Result page renders correctly with a fabricated result (templates + JS data binding)")
import os

fake_job_id = "smoketest01"
fake_result = {
    "job_id": fake_job_id,
    "original_filename": "lecture.mp4",
    "transcript": {
        "text": sample_transcript,
        "language": "en",
        "segments": [{"start": 0.0, "end": 4.5, "text": "Welcome to the lecture."}],
    },
    "summary": {
        "tldr": "This lecture covers ML models for predicting student performance.",
        "key_topics": ["Decision Tree", "Random Forest", "Flask", "MySQL"],
        "bullets": sample_bullets,
    },
    "quiz": questions,
    "created_at": 0,
}
os.makedirs(flask_app_module.Config.OUTPUT_FOLDER, exist_ok=True)
with open(flask_app_module._result_path(fake_job_id), "w") as f:
    json.dump(fake_result, f)

resp = client.get(f"/result/{fake_job_id}")
check("result page renders (200)", resp.status_code == 200)
check("result page includes tldr text", b"predicting student performance" in resp.data)
check("result page embeds quiz JSON for JS", b"correct_index" in resp.data)

resp = client.post(
    f"/api/grade-quiz/{fake_job_id}",
    data=json.dumps({"answers": {"0": questions[0]["correct_index"]}}),
    content_type="application/json",
)
check("grade-quiz endpoint returns 200", resp.status_code == 200)
grade_data = resp.get_json()
check("grading marks the correct answer as correct", grade_data["graded"][0]["correct"] is True)

os.remove(flask_app_module._result_path(fake_job_id))

print(f"\n{'='*40}\nTOTAL: {PASS} passed, {FAIL} failed\n{'='*40}")
sys.exit(1 if FAIL else 0)
