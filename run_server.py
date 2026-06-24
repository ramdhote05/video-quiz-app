"""Local preview runner for the Flask app.

This avoids Flask's debug reloader so the server stays alive when launched
from Windows shortcuts, cmd start, or Codex preview commands.
"""
import os
import sys
import traceback

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(LOG_DIR, exist_ok=True)


def _redirect_console_output():
    log_path = os.path.join(LOG_DIR, "preview-server.log")
    stream = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = stream
    sys.stderr = stream
    return stream


if __name__ == "__main__":
    _redirect_console_output()
    try:
        print("Starting preview server on http://127.0.0.1:5000/", flush=True)
        from app import app

        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        print("Preview server stopped.", flush=True)
    except Exception:
        traceback.print_exc()
        raise
