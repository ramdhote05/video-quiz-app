"""
Step 2 of the pipeline: speech-to-text using Groq's cloud transcription API
with a fallback to faster-whisper (local/offline) if no GROQ_API_KEY is present.
"""
import os
from config import Config

_model_cache = {}


def _get_model(model_size: str, device: str, compute_type: str):
    """Cache the loaded model so repeated requests don't reload it from disk."""
    from faster_whisper import WhisperModel
    key = (model_size, device, compute_type)
    if key not in _model_cache:
        _model_cache[key] = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _model_cache[key]


def transcribe(audio_path: str, model_size: str = "base", device: str = "cpu",
               compute_type: str = "int8") -> dict:
    """
    Transcribe the audio at `audio_path`.

    Returns a dict:
        {
            "text": "<full transcript as one string>",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 4.2, "text": "Welcome to today's lecture..."},
                ...
            ]
        }
    """
    if Config.GROQ_API_KEY:
        # Use Groq cloud transcription
        from groq import Groq

        client = Groq(api_key=Config.GROQ_API_KEY)
        with open(audio_path, "rb") as file:
            translation = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        
        # verbose_json contains full text, language, and segments
        segments = []
        if hasattr(translation, "segments") and translation.segments:
            for seg in translation.segments:
                if isinstance(seg, dict):
                    segments.append({
                        "start": round(seg.get("start", 0.0), 2),
                        "end": round(seg.get("end", 0.0), 2),
                        "text": seg.get("text", "").strip()
                    })
                else:
                    segments.append({
                        "start": round(getattr(seg, "start", 0.0), 2),
                        "end": round(getattr(seg, "end", 0.0), 2),
                        "text": getattr(seg, "text", "").strip()
                    })
        
        return {
            "text": getattr(translation, "text", "").strip(),
            "language": getattr(translation, "language", "en"),
            "segments": segments,
        }
    else:
        # Local fallback if no GROQ_API_KEY
        model = _get_model(model_size, device, compute_type)
        segments_iter, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            text = seg.text.strip()
            segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": text})
            full_text_parts.append(text)

        return {
            "text": " ".join(full_text_parts).strip(),
            "language": info.language,
            "segments": segments,
        }
