"""
Central configuration for the AI Video Summarization & Quiz Generator.
All values can be overridden via a .env file (see .env.example).
"""
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 500)) * 1024 * 1024  # default 500MB

    # --- Folders ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
    ALLOWED_EXTENSIONS = {"mp4", "mov", "mkv", "avi", "webm", "m4v"}

    # --- Whisper (speech-to-text) ---
    # tiny / base / small / medium / large-v3  (bigger = more accurate, slower)
    WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")  # "cuda" if you have a GPU
    WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

    # --- LLM backend for summarization & quiz generation ---
    # If GROQ_API_KEY is set, the app uses Groq's free-tier cloud API (fast, high quality,
    # runs models like Mixtral/Llama). Get a free key at https://console.groq.com
    # If it is NOT set, the app automatically falls back to a fully local/offline pipeline
    # (Hugging Face transformers for summarization + a rule-based quiz generator) so the
    # project still works with zero API keys and zero cost.
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "mixtral-8x7b-32768")

    # Local fallback summarization model (downloaded automatically the first time, then cached)
    LOCAL_SUMMARY_MODEL = os.environ.get("LOCAL_SUMMARY_MODEL", "sshleifer/distilbart-cnn-12-6")

    # --- Quiz ---
    NUM_QUIZ_QUESTIONS = int(os.environ.get("NUM_QUIZ_QUESTIONS", 5))

    @staticmethod
    def ensure_folders():
        for attr, folder_name in (
            ("UPLOAD_FOLDER", "uploads"),
            ("OUTPUT_FOLDER", "outputs"),
        ):
            folder = getattr(Config, attr)
            try:
                os.makedirs(folder, exist_ok=True)
                test_path = os.path.join(folder, ".write-test")
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write("ok")
                os.remove(test_path)
            except OSError:
                fallback = os.path.join(tempfile.gettempdir(), "video-quiz-app", folder_name)
                os.makedirs(fallback, exist_ok=True)
                setattr(Config, attr, fallback)
