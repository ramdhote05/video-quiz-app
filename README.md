# LectureRecap — AI Video Summarization & Quiz Generation System

An end-to-end Flask app that takes an uploaded educational video and turns it
into a transcript, a short revision-ready summary, and an auto-generated
multiple-choice quiz.

```
Video Upload → Audio Extraction → Whisper Transcription → LLM Summarization → Quiz Generation → Flask Web Display
```

## How it works

| Stage | What happens | Library |
|---|---|---|
| 1. Upload | User drops an MP4/MOV/MKV/AVI/WEBM file in the browser | Flask + Werkzeug |
| 2. Audio extraction | The video's audio track is pulled out as 16kHz mono WAV | MoviePy |
| 3. Transcription | Speech-to-text on the WAV file | faster-whisper (Whisper) |
| 4. Summarization | Transcript → TL;DR + key topics + bullet points | Groq cloud LLM, or local model if no key |
| 5. Quiz generation | Summary/transcript → 5 MCQs with explanations | Groq cloud LLM, or rule-based fallback |
| 6. Display | Tabbed UI: Summary / Transcript / interactive Quiz with scoring | Flask templates + vanilla JS |

Processing runs in a background thread per upload so the page can poll
`/api/status/<job_id>` and show a live progress checklist instead of making
the user stare at a frozen page.

### Two LLM modes — no paid account required

The summarizer and quiz generator both check `GROQ_API_KEY` at runtime:

- **Set it** → calls [Groq](https://console.groq.com) (free tier), which
  hosts fast open models like Mixtral/Llama. Best quality, recommended.
- **Leave it blank** → automatically falls back to a fully local pipeline:
  a small Hugging Face summarization model (`distilbart-cnn`) plus a
  rule-based cloze-deletion quiz generator. Zero cost, zero API key, works
  offline after the first model download — lower quality, but the whole
  system still runs end to end.

This means the project satisfies "use Mixtral or similar free LLMs / any
free cloud service" while still being demoable on a laptop with no internet
and no signups, which is worth mentioning if asked about it in a viva.

## Project structure

```
video-quiz-app/
├── app.py                  # Flask routes, job orchestration
├── config.py                # All settings, read from .env
├── requirements.txt
├── .env.example             # Copy to .env and fill in
├── test_smoke.py             # Verifies the install without needing model downloads
├── pipeline/
│   ├── audio_extractor.py   # Step 1
│   ├── transcriber.py        # Step 2 (Whisper)
│   ├── summarizer.py         # Step 3 (Groq / local fallback)
│   └── quiz_generator.py     # Step 4 (Groq / local fallback)
├── templates/
│   ├── base.html, index.html, processing.html, result.html
├── static/css/style.css      # "Chalkboard classroom" theme
├── uploads/                   # Raw videos land here briefly, then get deleted
└── outputs/                    # Extracted audio + final result JSON per job
```

## Setup

1. **Install ffmpeg** (required by MoviePy and Whisper to read video/audio):
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - Windows: `winget install ffmpeg` (or download from ffmpeg.org and add to PATH)
   - Mac: `brew install ffmpeg`

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   If you only plan to use the Groq cloud backend, you can skip installing
   `transformers` and `torch` from requirements.txt to save a lot of disk
   space and install time — they're only used by the offline fallback.

3. **Configure your `.env`:**
   ```bash
   cp .env.example .env
   ```
   To use Groq (recommended): create a free account at
   https://console.groq.com, generate an API key, and paste it into
   `GROQ_API_KEY` in `.env`. Check Groq's model list in their console, since
   available free models change over time — update `GROQ_MODEL` to match.

   To run fully offline instead: just leave `GROQ_API_KEY` blank.

4. **Verify the install (optional but recommended):**
   ```bash
   python3 test_smoke.py
   ```
   This checks the Flask routes, templates, and offline quiz logic without
   needing to download any model weights.

5. **Run the app:**
   ```bash
   python3 app.py
   ```
   Open http://localhost:5000 in your browser and upload a short video to
   try it end to end.

## Deployment

This project is configured for serverless deployment on Vercel using `app.py` and `vercel.json`.

For cloud deployment, set `GROQ_API_KEY` in Vercel's environment settings so transcription and LLM work run through Groq instead of local model downloads. See `DEPLOYMENT.md` for step-by-step instructions.

## Notes for your project report / viva

- **Why Whisper:** open-source, runs locally, no per-minute transcription
  fees, and handles accented/noisy classroom audio reasonably well.
- **Why a dual LLM backend:** demonstrates the system works both as a
  "free cloud service" integration (the brief's requirement) and as a fully
  offline fallback — useful if your demo machine has no internet on the day.
- **Why background threads instead of a task queue (Celery/Redis):** keeps
  the stack simple for a single-user/classroom-scale deployment. The
  in-memory `JOBS` dict is called out in the code as the part you'd swap for
  Celery + Redis if this needed to scale to many concurrent users.
- **Known limitations to mention proactively:** the offline quiz fallback
  produces simpler fill-in-the-blank questions rather than fully natural
  MCQs (Groq mode is noticeably better); very long videos (1hr+) take
  several minutes to transcribe on CPU; only English-language quiz/summary
  prompts are currently used even though Whisper itself is multilingual.

## Possible extensions

- Persist jobs in SQLite instead of an in-memory dict, so progress survives a server restart.
- Let the user pick quiz difficulty or number of questions before upload.
- Add a "study mode" that re-quizzes only the questions answered incorrectly.
- Support YouTube URLs as input (download via yt-dlp) instead of only local file uploads.
