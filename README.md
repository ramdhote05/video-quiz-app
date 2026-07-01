# 🎬 LectureRecap — AI Video Summarization & Quiz Generation System

<div align="center">

![LectureRecap](https://img.shields.io/badge/LectureRecap-AI%20Powered-6366f1?style=for-the-badge&logo=openai&logoColor=white)
[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://video-quiz-app-chi.vercel.app)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/ramdhote05/video-quiz-app)
[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

**An end-to-end Flask app that takes an uploaded educational video and turns it into a transcript, a short revision-ready summary, and an auto-generated multiple-choice quiz.**

[🌐 View Live App](https://video-quiz-app-chi.vercel.app) • [📂 GitHub Repo](https://github.com/ramdhote05/video-quiz-app) • [⚙️ How It Works](#how-it-works)

</div>

---

## 🌐 Live Demo

> **🚀 The app is deployed and live on Vercel!**

| Platform | Link |
|----------|------|
| 🌐 **Live App (Vercel)** | [https://video-quiz-app-chi.vercel.app](https://video-quiz-app-chi.vercel.app) |
| 📁 **Vercel Project Dashboard** | [https://vercel.com/techkrutids-9345s-projects/video-quiz-app](https://vercel.com/techkrutids-9345s-projects/video-quiz-app) |
| 💻 **GitHub Repository** | [https://github.com/ramdhote05/video-quiz-app](https://github.com/ramdhote05/video-quiz-app) |

---

## 🔄 Pipeline Overview

```
Video Upload → Audio Extraction → Whisper Transcription → LLM Summarization → Quiz Generation → Flask Web Display
```

---

## ⚙️ How It Works

| Stage | What happens | Library |
|---|---|---|
| 1. **Upload** | User drops an MP4/MOV/MKV/AVI/WEBM file in the browser | Flask + Werkzeug |
| 2. **Audio extraction** | The video's audio track is pulled out as 16kHz mono WAV | MoviePy |
| 3. **Transcription** | Speech-to-text on the WAV file | faster-whisper (Whisper) |
| 4. **Summarization** | Transcript → TL;DR + key topics + bullet points | Groq cloud LLM, or local model if no key |
| 5. **Quiz generation** | Summary/transcript → 5 MCQs with explanations | Groq cloud LLM, or rule-based fallback |
| 6. **Display** | Tabbed UI: Summary / Transcript / interactive Quiz with scoring | Flask templates + vanilla JS |

Processing runs in a **background thread** per upload so the page can poll `/api/status/<job_id>` and show a live progress checklist instead of making the user stare at a frozen page.

---

## 🤖 Two LLM Modes — No Paid Account Required

The summarizer and quiz generator both check `GROQ_API_KEY` at runtime:

- ✅ **Set it** → calls [Groq](https://console.groq.com) (free tier), which hosts fast open models like Mixtral/Llama. Best quality, **recommended**.
- 🔌 **Leave it blank** → automatically falls back to a fully local pipeline: a small Hugging Face summarization model (`distilbart-cnn`) plus a rule-based cloze-deletion quiz generator. **Zero cost, zero API key, works offline** after the first model download — lower quality, but the whole system still runs end to end.

> This means the project satisfies "use Mixtral or similar free LLMs / any free cloud service" while still being demoable on a laptop with no internet and no signups — worth mentioning if asked about it in a viva.

---

## ✨ Features

- 🎥 **Multi-format Video Support** — MP4, MOV, MKV, AVI, WEBM
- 🎙️ **Whisper Transcription** — Accurate speech-to-text using OpenAI's Whisper model
- 🧠 **AI Summarization** — TL;DR summaries with key topics and bullet points
- 📝 **Auto Quiz Generation** — 5 MCQs with explanations per video
- ⏳ **Live Progress Tracking** — Real-time progress checklist via background polling
- 🎨 **Chalkboard UI Theme** — Beautiful "classroom" themed interface
- 🔄 **Dual LLM Mode** — Groq API (cloud) or local Hugging Face fallback

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| 🐍 **Python 3.x** | Core programming language |
| 🌐 **Flask** | Web framework & REST API |
| 🎬 **MoviePy** | Audio extraction from video |
| 🎙️ **faster-whisper** | Speech-to-text transcription |
| 🤖 **Groq (Mixtral/Llama)** | Cloud LLM for summarization & quiz |
| 🤗 **Hugging Face** | Local fallback summarization model |
| ☁️ **Vercel** | Deployment platform |

---

## 📁 Project Structure

```
video-quiz-app/
├── app.py                  # Flask routes, job orchestration
├── config.py               # All settings, read from .env
├── requirements.txt
├── .env.example            # Copy to .env and fill in
├── test_smoke.py           # Verifies the install without needing model downloads
├── pipeline/
│   ├── audio_extractor.py  # Step 1 — Extract audio from video
│   ├── transcriber.py      # Step 2 — Whisper transcription
│   ├── summarizer.py       # Step 3 — Groq / local fallback
│   └── quiz_generator.py   # Step 4 — Groq / local fallback
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── processing.html
│   └── result.html
├── static/css/style.css    # "Chalkboard classroom" theme
├── uploads/                # Raw videos land here briefly, then get deleted
└── outputs/                # Extracted audio + final result JSON
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)
- FFmpeg (required by MoviePy for audio extraction)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ramdhote05/video-quiz-app.git
   cd video-quiz-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and optionally add your GROQ_API_KEY
   ```

4. **Run the app**
   ```bash
   python app.py
   ```

5. **Open your browser** at `http://localhost:5000` and upload a video!

### Verify Installation (No Model Downloads Needed)

```bash
python test_smoke.py
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Optional | Groq API key for cloud LLM (free tier). Leave blank for local fallback. |

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. 🍴 Fork the repository
2. 🌿 Create a new branch (`git checkout -b feature/your-feature`)
3. 💾 Commit your changes (`git commit -m 'Add some feature'`)
4. 📤 Push to the branch (`git push origin feature/your-feature`)
5. 🔃 Open a Pull Request

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Ramdhote05**

[![GitHub](https://img.shields.io/badge/GitHub-ramdhote05-181717?style=flat-square&logo=github)](https://github.com/ramdhote05)

---

<div align="center">

### ⭐ If you found this project useful, please give it a star!

[![Star on GitHub](https://img.shields.io/github/stars/ramdhote05/video-quiz-app?style=social)](https://github.com/ramdhote05/video-quiz-app/stargazers)

**Made with ❤️ for students and educators**

</div>
