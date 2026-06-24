# LectureRecap Project Summary

## 1. Project Overview

LectureRecap is an AI-powered video summarization and quiz generation web application.
The main goal of the project is to help students revise educational videos faster.
Instead of manually watching a full lecture again, the user uploads a video and the
system automatically creates:

- A full transcript of the spoken content.
- A short summary of the lecture.
- Key topics and important bullet points.
- A multiple-choice quiz based on the content.
- An interactive result page where the user can answer the quiz and see the score.

In simple words, this project converts a lecture video into study material.

## 2. Problem Statement

Students often need to revise long lecture recordings, training videos, or classroom
sessions. Watching the whole video again takes time, and manually preparing notes or
quiz questions is repetitive.

This project solves that problem by automating the revision workflow:

1. Upload a lecture video.
2. Extract the audio.
3. Convert the speech into text.
4. Summarize the transcript.
5. Generate quiz questions.
6. Display everything in a clean web interface.

## 3. Main Features

- Video upload through a browser interface.
- Supported video formats: MP4, MOV, MKV, AVI, WEBM, and M4V.
- Audio extraction from uploaded videos using FFmpeg.
- Speech-to-text transcription using Groq Whisper API when a Groq API key is available.
- Optional local transcription fallback using `faster-whisper` if installed.
- AI summary generation using Groq when configured.
- Local fallback summarization when cloud summarization is unavailable.
- Dependency-free extractive summary fallback if `transformers` is not installed.
- Rule-based quiz generation when Groq quiz generation is unavailable.
- Background processing so the browser does not freeze during long video processing.
- Live processing page that polls job status.
- Result page with Summary, Transcript, and Quiz tabs.
- Quiz grading endpoint that returns score and explanations.
- Smoke test file to verify route and fallback behavior.

## 4. Tech Stack

### Backend

- Python
- Flask
- Werkzeug
- python-dotenv

### AI and Processing

- Groq API for cloud transcription, summarization, and quiz generation.
- Groq Whisper model for speech-to-text when `GROQ_API_KEY` is set.
- FFmpeg for extracting audio from uploaded videos.
- Optional `faster-whisper` local transcription fallback.
- Optional Hugging Face `transformers` summarization fallback.
- Built-in Python extractive summarizer as a final fallback.
- Rule-based local quiz generator for offline/no-API operation.

### Frontend

- HTML templates using Jinja2.
- Vanilla JavaScript.
- CSS.
- No frontend framework is used.

### Storage

- Uploaded videos are temporarily stored in the `uploads/` folder.
- Extracted audio and final result JSON files are stored in the `outputs/` folder.
- Job status is stored in memory using a Python dictionary.
- No database is currently used.

## 5. Important Project Files

### `app.py`

This is the main Flask application file. It defines all routes, handles uploads,
starts background processing, tracks job status, and renders the pages.

Important routes:

- `/` - Upload page.
- `/upload` - Accepts video upload.
- `/processing/<job_id>` - Shows processing progress.
- `/api/status/<job_id>` - Returns current job status as JSON.
- `/result/<job_id>` - Shows transcript, summary, and quiz.
- `/api/grade-quiz/<job_id>` - Grades quiz answers.

### `config.py`

Stores application configuration. It reads values from `.env` and defines:

- Upload folder.
- Output folder.
- Allowed video file extensions.
- Maximum upload size.
- Groq API key.
- Groq model name.
- Whisper settings.
- Number of quiz questions.

### `run_server.py`

A helper runner added for stable local preview on Windows. It runs Flask without
the debug reloader and writes preview logs to `outputs/preview-server.log`.

### `pipeline/audio_extractor.py`

Uses FFmpeg to extract audio from the uploaded video. The output audio format is:

- WAV
- 16 kHz
- Mono channel
- PCM 16-bit

This format is suitable for Whisper-style speech-to-text models.

### `pipeline/transcriber.py`

Converts the extracted audio into text.

It works in two modes:

- If `GROQ_API_KEY` is available, it uses Groq cloud transcription.
- If no API key is available, it tries to use local `faster-whisper`.

The output includes:

- Full transcript text.
- Detected language.
- Timestamped transcript segments.

### `pipeline/summarizer.py`

Creates a structured summary from the transcript.

It attempts summary generation in this order:

1. Groq cloud LLM summary if an API key is configured.
2. Hugging Face `transformers` local summarization model if installed.
3. Dependency-free extractive fallback if cloud/local model summarization fails.

The summary output contains:

- `tldr`
- `key_topics`
- `bullets`

### `pipeline/quiz_generator.py`

Creates multiple-choice quiz questions.

It works in two modes:

- Groq mode: asks a cloud LLM to generate high-quality MCQs.
- Local mode: creates fill-in-the-blank questions from keywords in the transcript
  and summary bullets.

Each quiz question contains:

- Question text.
- Four options.
- Correct option index.
- Explanation.

### `templates/`

Contains the Jinja2 HTML templates:

- `base.html` - Shared layout.
- `index.html` - Upload page.
- `processing.html` - Progress checklist page.
- `result.html` - Summary, transcript, and quiz page.

### `static/css/style.css`

Contains the full visual design of the app. The current theme is a chalkboard
classroom style with dark green background, chalk-like headings, and gold accents.

### `test_smoke.py`

A smoke test script that checks:

- Summarizer helper functions.
- Dependency-free fallback summary.
- Local quiz generation.
- Flask routes.
- Template rendering.
- Quiz grading endpoint.

Run it with:

```bash
python test_smoke.py
```

## 6. Complete Workflow

### Step 1: User Uploads a Video

The user opens the home page and selects or drags a video file into the upload box.
The frontend sends the file to the `/upload` route using JavaScript `fetch`.

### Step 2: Flask Validates the Upload

The backend checks:

- A file was selected.
- The file extension is allowed.
- The upload size is within the configured limit.

Then it creates a unique `job_id`, saves the file in `uploads/`, and starts a
background thread.

### Step 3: Background Pipeline Starts

The pipeline runs in a background thread so the upload request can return quickly.
The browser is redirected to `/processing/<job_id>`.

The processing page repeatedly calls `/api/status/<job_id>` to show progress.

### Step 4: Audio Extraction

FFmpeg extracts the audio track from the uploaded video and saves it as a WAV file
inside `outputs/`.

If the video has no audio track, the pipeline reports an error.

### Step 5: Transcription

The app converts the audio into text.

If Groq is configured, it uses Groq's Whisper transcription endpoint.
If not, it tries local `faster-whisper`.

The transcript includes both full text and timestamped segments.

### Step 6: Summarization

The transcript is passed into the summarizer.

The app first tries Groq for a high-quality structured summary. If Groq fails or is
not configured, it tries local summarization. If local dependencies are missing, it
uses the built-in extractive fallback.

### Step 7: Quiz Generation

The transcript and summary bullets are passed into the quiz generator.

If Groq is available, it generates natural multiple-choice questions.
If not, the local fallback creates fill-in-the-blank questions using important
keywords from the transcript.

### Step 8: Result JSON Is Saved

The final output is saved in `outputs/<job_id>.json`.

The JSON contains:

- Job id.
- Original filename.
- Transcript data.
- Summary data.
- Quiz data.
- Creation timestamp.

### Step 9: User Sees Result Page

When processing is complete, the browser redirects to `/result/<job_id>`.

The result page has three main sections:

- Summary
- Transcript
- Quiz

The user can answer quiz questions and submit them for grading.

### Step 10: Cleanup

After processing finishes, the raw uploaded video and intermediate audio file are
removed to save disk space.

## 7. Configuration

Configuration is controlled by environment variables, usually stored in `.env`.

Important variables:

```env
SECRET_KEY=dev-secret-change-me
MAX_UPLOAD_MB=500
GROQ_API_KEY=
GROQ_MODEL=mixtral-8x7b-32768
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
LOCAL_SUMMARY_MODEL=sshleifer/distilbart-cnn-12-6
NUM_QUIZ_QUESTIONS=5
```

If `GROQ_API_KEY` is empty, the app uses fallback logic.

## 8. How to Run the Project

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure FFmpeg is installed and available in PATH.

Run normally:

```bash
python app.py
```

Or run the stable local preview runner:

```bash
python run_server.py
```

Then open:

```text
http://127.0.0.1:5000/
```

## 9. Current Dependency Note

The current `requirements.txt` keeps heavy local AI packages commented out to avoid
Windows and Python 3.14 installation issues.

Commented packages include:

- `faster-whisper`
- `transformers`
- `torch`
- `sentencepiece`

Because of this:

- Cloud mode with Groq is the easiest full workflow.
- Local summarization still works through the built-in extractive fallback.
- Local transcription needs `faster-whisper` installed, unless Groq transcription is used.

## 10. Error Handling

The app handles several failure cases:

- Missing upload file.
- Unsupported video format.
- Video with no audio stream.
- FFmpeg extraction failure.
- Unknown job id.
- Summarization fallback when Groq or `transformers` fails.
- Expired processing page recovery with a link back to upload.

## 11. Limitations

- Job status is stored in memory, so active jobs are lost if the server restarts.
- No database is currently used.
- Local transcription requires extra packages that are not installed by default.
- Long videos can take a lot of time to process.
- Local quiz fallback produces simpler fill-in-the-blank questions.
- The Flask development server is suitable for demos, not production deployment.

## 12. Possible Future Improvements

- Store jobs and results in SQLite or another database.
- Add user accounts and history of processed videos.
- Add YouTube URL input.
- Add quiz difficulty selection.
- Let users choose number of quiz questions.
- Export summary and quiz as PDF or DOCX.
- Add support for multiple languages.
- Add Celery and Redis for scalable background processing.
- Add better local transcription setup for offline demos.
- Add result sharing or download links.

## 13. One-Line Explanation

LectureRecap is a Flask-based AI study assistant that turns uploaded lecture videos
into transcripts, summaries, and interactive quizzes using FFmpeg, Groq, fallback
AI logic, and a simple browser interface.
