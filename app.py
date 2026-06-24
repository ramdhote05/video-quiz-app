"""
AI Video Summarization & Quiz Generation System
Flask web app tying together the pipeline: Upload -> Audio Extraction ->
Whisper Transcription -> LLM Summarization -> Quiz Generation -> Display.
"""
import json
import os
import threading
import time
import uuid

from flask import Flask, jsonify, render_template, request, redirect, url_for, abort
from werkzeug.utils import secure_filename

from config import Config
from pipeline.audio_extractor import extract_audio
from pipeline.transcriber import transcribe
from pipeline.summarizer import summarize
from pipeline.quiz_generator import generate_quiz

app = Flask(__name__)
app.config.from_object(Config)
Config.ensure_folders()

# In-memory job status tracker: {job_id: {"status": str, "message": str, "filename": str}}
# Good enough for a single-process Flask dev server / small classroom deployment.
JOBS = {}
JOBS_LOCK = threading.Lock()

PIPELINE_STAGES = [
    ("uploaded", "Video uploaded"),
    ("extracting_audio", "Extracting audio track"),
    ("transcribing", "Transcribing speech with Whisper"),
    ("summarizing", "Summarizing key points"),
    ("generating_quiz", "Generating quiz questions"),
    ("done", "Ready to review"),
]


def _set_status(job_id, status, message=""):
    with JOBS_LOCK:
        JOBS.setdefault(job_id, {})
        JOBS[job_id]["status"] = status
        JOBS[job_id]["message"] = message


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in Config.ALLOWED_EXTENSIONS


def _result_path(job_id):
    return os.path.join(Config.OUTPUT_FOLDER, f"{job_id}.json")


def run_pipeline(job_id: str, video_path: str, original_filename: str):
    """Runs in a background thread so the upload request returns immediately."""
    try:
        _set_status(job_id, "extracting_audio")
        audio_path = extract_audio(video_path, Config.OUTPUT_FOLDER)

        _set_status(job_id, "transcribing")
        transcript_data = transcribe(
            audio_path,
            model_size=Config.WHISPER_MODEL_SIZE,
            device=Config.WHISPER_DEVICE,
            compute_type=Config.WHISPER_COMPUTE_TYPE,
        )

        _set_status(job_id, "summarizing")
        summary = summarize(
            transcript_data["text"],
            groq_api_key=Config.GROQ_API_KEY,
            groq_model=Config.GROQ_MODEL,
            local_model_name=Config.LOCAL_SUMMARY_MODEL,
        )

        _set_status(job_id, "generating_quiz")
        quiz = generate_quiz(
            transcript_data["text"],
            summary.get("bullets", []),
            groq_api_key=Config.GROQ_API_KEY,
            groq_model=Config.GROQ_MODEL,
            num_questions=Config.NUM_QUIZ_QUESTIONS,
        )

        result = {
            "job_id": job_id,
            "original_filename": original_filename,
            "transcript": transcript_data,
            "summary": summary,
            "quiz": quiz,
            "created_at": time.time(),
        }
        with open(_result_path(job_id), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        _set_status(job_id, "done")

    except Exception as e:
        _set_status(job_id, "error", str(e))

    finally:
        # Clean up the raw uploaded video + intermediate audio to save disk space.
        for path in (video_path, locals().get("audio_path")):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("video")
    if not file or file.filename == "":
        return jsonify({"error": "No video file selected."}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    job_id = uuid.uuid4().hex[:12]
    filename = secure_filename(file.filename)
    video_path = os.path.join(Config.UPLOAD_FOLDER, f"{job_id}_{filename}")
    file.save(video_path)

    _set_status(job_id, "uploaded")
    if os.environ.get("VERCEL") == "1":
        # Run synchronously on Vercel to ensure completion before serverless functions suspend
        run_pipeline(job_id, video_path, filename)
    else:
        # Run in a background thread for standard deployments (e.g., local run)
        thread = threading.Thread(target=run_pipeline, args=(job_id, video_path, filename), daemon=True)
        thread.start()

    return jsonify({"job_id": job_id, "redirect": url_for("processing", job_id=job_id)})


@app.route("/processing/<job_id>")
def processing(job_id):
    if job_id not in JOBS:
        if os.path.exists(_result_path(job_id)):
            return redirect(url_for("result", job_id=job_id))
        return render_template("processing.html", job_id=job_id, stages=PIPELINE_STAGES, missing_job=True)
    return render_template("processing.html", job_id=job_id, stages=PIPELINE_STAGES, missing_job=False)


@app.route("/api/status/<job_id>")
def api_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job id."}), 404
    return jsonify(job)


@app.route("/result/<job_id>")
def result(job_id):
    path = _result_path(job_id)
    if not os.path.exists(path):
        abort(404)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return render_template("result.html", data=data)


@app.route("/api/grade-quiz/<job_id>", methods=["POST"])
def grade_quiz(job_id):
    path = _result_path(job_id)
    if not os.path.exists(path):
        return jsonify({"error": "Unknown job id."}), 404
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    answers = request.json.get("answers", {})  # {"0": 2, "1": 0, ...}
    quiz = data["quiz"]
    graded = []
    correct_count = 0
    for i, q in enumerate(quiz):
        selected = answers.get(str(i))
        is_correct = selected == q["correct_index"]
        if is_correct:
            correct_count += 1
        graded.append({
            "correct": is_correct,
            "correct_index": q["correct_index"],
            "explanation": q.get("explanation", ""),
        })

    return jsonify({
        "score": correct_count,
        "total": len(quiz),
        "graded": graded,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
