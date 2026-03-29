"""
AfroMations - Clipper Engine (Async Web Bridge)
Runs the video processing pipeline in a thread pool.
Bridges web.py (async FastAPI) <-> app_enhanced.py (sync processing).
"""
import os
import json
import asyncio
import threading
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/tmp/afromations/uploads"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/tmp/afromations/outputs"))
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        return True
    except Exception:
        return False


def _whisper_available() -> bool:
    try:
        import whisper  # noqa
        return True
    except ImportError:
        return False


def process_clip_sync(
    input_path: str,
    query: str,
    output_path: str,
    progress_cb: Optional[Callable] = None,
) -> dict:
    """
    Synchronous clip processing.
    Runs Whisper transcription → Groq segment selection → MoviePy editing.
    Falls back to mock if dependencies aren't available.
    """

    def report(pct: int, msg: str):
        if progress_cb:
            progress_cb(pct, msg)

    report(5, "Checking dependencies...")

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    if not _ffmpeg_available() or not _whisper_available():
        return _mock_processing(input_path, query, output_path, progress_cb)

    try:
        import whisper
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        # Step 1 – Transcribe
        report(10, "Loading Whisper model...")
        model = whisper.load_model(WHISPER_MODEL)

        report(25, "Transcribing audio...")
        result = model.transcribe(input_path)
        segments = [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in result["segments"]
        ]

        # Step 2 – Select segments
        report(50, "Finding relevant moments...")
        if GROQ_API_KEY and GROQ_API_KEY not in ("stub-key", ""):
            import requests as req
            prompt = f"""You are an expert video editor. Given a transcript, identify all conversations related to the user query.
Output ONLY valid JSON: {{"conversations": [{{"start": 0.0, "end": 5.0}}]}}

Transcript:
{json.dumps(segments, indent=2)}

User query: {query}"""
            resp = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.2,
                },
                timeout=30,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            conversations = json.loads(raw)["conversations"]
        else:
            # Keyword-based fallback
            query_words = set(query.lower().split())
            conversations = [
                {"start": s["start"], "end": s["end"]}
                for s in segments
                if any(w in s["text"].lower() for w in query_words)
            ][:5] or [{"start": 0, "end": min(30, segments[-1]["end"])}]

        # Step 3 – Edit
        report(70, "Editing video clips...")
        video = VideoFileClip(input_path)
        clips = []
        for conv in conversations:
            try:
                start = float(conv["start"])
                end = float(conv["end"])
                if end > start and end <= video.duration:
                    clips.append(
                        video.subclip(start, end).fadein(0.3).fadeout(0.3)
                    )
            except Exception:
                continue

        if not clips:
            clips = [video.subclip(0, min(30, video.duration))]

        report(85, "Rendering output file...")
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac",
                              logger=None)
        video.close()
        final.close()

        report(100, "Done!")
        return {
            "status": "complete",
            "output_path": output_path,
            "clips_count": len(clips),
            "segments_found": len(conversations),
            "mode": "ai" if (GROQ_API_KEY and GROQ_API_KEY not in ("stub-key", "")) else "keyword",
        }

    except Exception as exc:
        return _mock_processing(input_path, query, output_path, progress_cb,
                                error=str(exc))


def _mock_processing(input_path: str, query: str, output_path: str,
                     progress_cb, error: str = None) -> dict:
    """
    Mock processing when dependencies aren't available.
    Copies a portion of the input video as the output.
    """
    def report(pct, msg):
        if progress_cb:
            progress_cb(pct, msg)

    report(30, "Running in demo mode...")

    try:
        # Try ffmpeg copy of first 30 seconds
        subprocess.run([
            "ffmpeg", "-i", input_path, "-t", "30",
            "-c", "copy", output_path, "-y"
        ], capture_output=True, timeout=60)
        report(100, "Demo clip ready")
        return {
            "status": "complete",
            "output_path": output_path,
            "clips_count": 1,
            "segments_found": 1,
            "mode": "demo",
            "note": "Demo mode: returned first 30 seconds. Install Whisper+Groq for AI clipping.",
        }
    except Exception:
        # Absolute fallback: copy the file
        shutil.copy(input_path, output_path)
        report(100, "File copied (demo)")
        return {
            "status": "complete",
            "output_path": output_path,
            "clips_count": 1,
            "segments_found": 1,
            "mode": "fallback",
        }


# ─── Async wrapper ────────────────────────────────────────────────────────────

async def run_clip_job(
    job_id: str,
    input_path: str,
    query: str,
    on_progress: Callable,
    on_complete: Callable,
    on_error: Callable,
):
    """
    Run clip processing in a thread pool so it doesn't block FastAPI event loop.
    """
    loop = asyncio.get_event_loop()
    output_path = str(OUTPUT_DIR / f"{job_id}.mp4")

    def progress_cb(pct: int, msg: str):
        asyncio.run_coroutine_threadsafe(on_progress(pct, msg), loop)

    def _run():
        try:
            result = process_clip_sync(input_path, query, output_path, progress_cb)
            asyncio.run_coroutine_threadsafe(on_complete(result), loop)
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(on_error(str(exc)), loop)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def save_upload(file_bytes: bytes, filename: str, job_id: str) -> str:
    """Save uploaded video bytes to disk and return the path."""
    ext = Path(filename).suffix or ".mp4"
    dest = UPLOAD_DIR / f"{job_id}{ext}"
    dest.write_bytes(file_bytes)
    return str(dest)
