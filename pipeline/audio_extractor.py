"""
Step 1 of the pipeline: pull a clean mono WAV audio track out of the uploaded
video file so it can be fed to the speech-to-text model.
"""
import os
import shutil
import subprocess


def _ffmpeg_command() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Extract the audio track from `video_path` and write it as a 16kHz mono
    WAV file (the format Whisper-family models expect) into `output_dir`.

    Returns the path to the generated audio file.
    """
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.wav")

    # Run FFmpeg to extract audio as mono 16kHz WAV
    cmd = [
        _ffmpeg_command(),
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_path
    ]
    
    # Run the command and capture output
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        if "Output file is empty" in result.stderr or "does not contain any stream" in result.stderr:
            raise ValueError("This video file has no audio track to transcribe.")
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise ValueError("This video file has no audio track to transcribe.")

    return audio_path
