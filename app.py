from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import asyncio
import subprocess
import tempfile
import uuid
import os
import re
import wave
import time
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "tmp")
STATIC_DIR = os.path.join(BASE_DIR, "static")
VOICES_DIR = os.path.join(BASE_DIR, "voices")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(VOICES_DIR, exist_ok=True)


# ============================================================
# PIPER
# ============================================================

PIPER_EXE = os.path.join(BASE_DIR, "venv", "bin", "piper")


VOICES = {
    "hindi": os.path.join(
        VOICES_DIR,
        "hi_IN-rohan-medium.onnx"
    ),
    "male": os.path.join(
        VOICES_DIR,
        "hi_IN-rohan-medium.onnx"
    ),
    "female": os.path.join(
        VOICES_DIR,
        "hi_IN-rohan-medium.onnx"
    ),
}


# ============================================================
# SETTINGS
# ============================================================

WORDS_PER_CHUNK = 150

# Final WAV files older than 5 minutes are deleted.
WAV_MAX_AGE = 5 * 360

# Cleanup runs every 60 seconds.
CLEANUP_INTERVAL = 360


# ============================================================
# JOB STORAGE
# ============================================================

# Example:
#
# jobs[job_id] = {
#     "status": "queued",
#     "progress": 0,
#     "current_chunk": 0,
#     "total_chunks": 0,
#     "filename": None,
#     "error": None,
#     "created_at": ...,
#     "updated_at": ...
# }

jobs = {}

# Only one Piper generation at a time.
# This prevents multiple large requests from consuming
# all available CPU/RAM on PythonAnywhere.
generation_lock = asyncio.Lock()


# ============================================================
# PYDANTIC REQUEST
# ============================================================

class TTSRequest(BaseModel):
    text: str
    voice: str = "hindi"
    speed: float = 1.0


# ============================================================
# CLEANUP
# ============================================================

async def cleanup_old_wav_files():

    while True:

        try:

            now = time.time()

            for filename in os.listdir(OUTPUT_DIR):

                if not filename.lower().endswith(".wav"):
                    continue

                filepath = os.path.join(
                    OUTPUT_DIR,
                    filename
                )

                try:

                    age = now - os.path.getmtime(filepath)

                    if age > WAV_MAX_AGE:

                        os.remove(filepath)

                        print(
                            f"Deleted old WAV: {filepath}",
                            flush=True
                        )

                except Exception as e:

                    print(
                        f"Cleanup error for {filepath}: {e}",
                        flush=True
                    )

        except Exception as e:

            print(
                f"Cleanup task error: {e}",
                flush=True
            )

        await asyncio.sleep(CLEANUP_INTERVAL)


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    cleanup_task = asyncio.create_task(
        cleanup_old_wav_files()
    )

    print(
        "TTS application started",
        flush=True
    )

    try:

        yield

    finally:

        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        print(
            "TTS application stopped",
            flush=True
        )


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Hindi TTS API",
    version="2.0",
    lifespan=lifespan
)


# ============================================================
# TEXT CHUNKING
# ============================================================

def split_text_into_chunks(text: str):

    # First split using sentence boundaries.
    sentences = re.split(
        r'(?<=[.!??])\s+',
        text.strip()
    )

    chunks = []

    current_words = []

    for sentence in sentences:

        words = sentence.split()

        if not words:
            continue

        # If one sentence itself is very large,
        # split it into smaller pieces.
        while len(words) > WORDS_PER_CHUNK:

            if current_words:

                chunks.append(
                    " ".join(current_words)
                )

                current_words = []

            chunks.append(
                " ".join(words[:WORDS_PER_CHUNK])
            )

            words = words[WORDS_PER_CHUNK:]

        current_words.extend(words)

        if len(current_words) >= WORDS_PER_CHUNK:

            chunks.append(
                " ".join(current_words)
            )

            current_words = []

    if current_words:

        chunks.append(
            " ".join(current_words)
        )

    return chunks


# ============================================================
# RUN PIPER
# ============================================================

def run_piper(
    text: str,
    output_wav: str,
    model_path: str,
    speed: float
):

    text_file = None

    try:

        # Create temporary text file.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            dir=TEMP_DIR,
            delete=False
        ) as f:

            f.write(text)

            text_file = f.name

        # Piper length_scale:
        #
        # speed 1.0 = normal
        # speed 1.2 = faster
        # speed 0.8 = slower
        #
        length_scale = 1.0 / speed

        command = [
            PIPER_EXE,
            "--model",
            model_path,
            "--output_file",
            output_wav,
            "--length_scale",
            str(length_scale)
        ]

        print(
            "Running Piper...",
            flush=True
        )

        with open(
            text_file,
            "r",
            encoding="utf-8"
        ) as input_file:

            result = subprocess.run(
                command,
                stdin=input_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

        print(
            f"PIPER RETURN CODE: {result.returncode}",
            flush=True
        )

        if result.stdout:

            print(
                result.stdout,
                flush=True
            )

        if result.stderr:

            print(
                result.stderr,
                flush=True
            )

        if result.returncode != 0:

            raise RuntimeError(
                "Piper failed: "
                + result.stderr[-2000:]
            )

        if not os.path.exists(output_wav):

            raise RuntimeError(
                f"Piper did not create output file: {output_wav}"
            )

        return True

    finally:

        if text_file and os.path.exists(text_file):

            try:

                os.remove(text_file)

            except Exception:
                pass


# ============================================================
# CONCATENATE WAV FILES
# ============================================================

def concatenate_wavs(
    input_files,
    output_file
):

    if not input_files:

        raise RuntimeError(
            "No WAV files to merge."
        )

    with wave.open(
        input_files[0],
        "rb"
    ) as first:

        params = first.getparams()

        with wave.open(
            output_file,
            "wb"
        ) as output:

            output.setparams(params)

            for filepath in input_files:

                with wave.open(
                    filepath,
                    "rb"
                ) as wav:

                    # Verify compatibility.
                    if (
                        wav.getnchannels()
                        != params.nchannels
                        or wav.getsampwidth()
                        != params.sampwidth
                        or wav.getframerate()
                        != params.framerate
                        or wav.getcomptype()
                        != params.comptype
                    ):

                        raise RuntimeError(
                            "WAV format mismatch while merging."
                        )

                    while True:

                        frames = wav.readframes(
                            1024 * 16
                        )

                        if not frames:
                            break

                        output.writeframes(
                            frames
                        )


# ============================================================
# JOB PROCESSOR
# ============================================================

def process_tts_job(
    job_id: str,
    text: str,
    voice: str,
    speed: float
):

    chunk_files = []

    try:

        jobs[job_id]["status"] = "processing"
        jobs[job_id]["updated_at"] = time.time()

        model_path = VOICES.get(
            voice,
            VOICES["hindi"]
        )

        chunks = split_text_into_chunks(text)

        total_chunks = len(chunks)

        jobs[job_id]["total_chunks"] = total_chunks
        jobs[job_id]["current_chunk"] = 0
        jobs[job_id]["progress"] = 0

        print(
            f"JOB {job_id}",
            flush=True
        )

        print(
            f"Received text: {len(text)} chars",
            flush=True
        )

        print(
            f"Voice: {voice}",
            flush=True
        )

        print(
            f"Speed: {speed}",
            flush=True
        )

        print(
            f"Chunks: {total_chunks}",
            flush=True
        )

        # ----------------------------------------------------
        # Generate every chunk
        # ----------------------------------------------------

        for index, chunk in enumerate(
            chunks,
            start=1
        ):

            jobs[job_id]["current_chunk"] = index

            jobs[job_id]["progress"] = int(
                ((index - 1) / total_chunks) * 90
            )

            jobs[job_id]["updated_at"] = time.time()

            print(
                f"Generating chunk {index}/{total_chunks}",
                flush=True
            )

            print(
                f"Chunk text: {chunk[:300]}",
                flush=True
            )

            chunk_file = os.path.join(
                TEMP_DIR,
                f"chunk_{job_id}_{index}.wav"
            )

            run_piper(
                text=chunk,
                output_wav=chunk_file,
                model_path=model_path,
                speed=speed
            )

            chunk_files.append(
                chunk_file
            )

            jobs[job_id]["progress"] = int(
                (index / total_chunks) * 90
            )

            jobs[job_id]["updated_at"] = time.time()

        # ----------------------------------------------------
        # Merge
        # ----------------------------------------------------

        jobs[job_id]["status"] = "merging"
        jobs[job_id]["progress"] = 95
        jobs[job_id]["updated_at"] = time.time()

        print(
            f"Merging {len(chunk_files)} chunks...",
            flush=True
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        filename = (
            f"{timestamp}_"
            f"{voice}_"
            f"{job_id}.wav"
        )

        output_file = os.path.join(
            OUTPUT_DIR,
            filename
        )

        concatenate_wavs(
            chunk_files,
            output_file
        )

        if not os.path.exists(output_file):

            raise RuntimeError(
                "Final WAV file was not created."
            )

        # ----------------------------------------------------
        # Complete
        # ----------------------------------------------------

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["filename"] = filename
        jobs[job_id]["updated_at"] = time.time()

        print(
            f"JOB COMPLETED: {job_id}",
            flush=True
        )

        print(
            f"SAVED: {output_file}",
            flush=True
        )

    except Exception as e:

        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = time.time()

        print(
            f"JOB FAILED: {job_id}",
            flush=True
        )

        print(
            f"TTS ERROR: {e}",
            flush=True
        )

    finally:

        # Delete temporary chunk files.
        for filepath in chunk_files:

            try:

                if os.path.exists(filepath):

                    os.remove(filepath)

            except Exception as e:

                print(
                    f"Could not delete temp file "
                    f"{filepath}: {e}",
                    flush=True
                )


# ============================================================
# BACKGROUND JOB WRAPPER
# ============================================================

async def run_background_job(
    job_id: str,
    text: str,
    voice: str,
    speed: float
):

    # Only one Piper generation at a time.
    async with generation_lock:

        await asyncio.to_thread(
            process_tts_job,
            job_id,
            text,
            voice,
            speed
        )


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def home():

    index_file = os.path.join(
        STATIC_DIR,
        "index.html"
    )

    if not os.path.exists(index_file):

        return JSONResponse({
            "message": "Hindi TTS API is running",
            "docs": "/docs"
        })

    return FileResponse(
        index_file
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "piper": os.path.exists(PIPER_EXE),
        "voices": {
            name: os.path.exists(path)
            for name, path in VOICES.items()
        },
        "jobs": len(jobs)
    }


# ============================================================
# START GENERATION
# ============================================================

@app.post("/generate")
async def generate(req: TTSRequest):

    text = req.text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Text is required."
        )

    if len(text) > 100000:

        raise HTTPException(
            status_code=400,
            detail="Text is too long. Maximum 100,000 characters."
        )

    if req.speed <= 0:

        raise HTTPException(
            status_code=400,
            detail="Speed must be greater than 0."
        )

    if req.speed > 3:

        raise HTTPException(
            status_code=400,
            detail="Maximum speed is 3.0."
        )

    voice = req.voice.lower().strip()

    if voice not in VOICES:

        voice = "hindi"

    model_path = VOICES[voice]

    if not os.path.exists(model_path):

        raise HTTPException(
            status_code=500,
            detail=f"Voice model not found: {model_path}"
        )

    # Create unique job ID.
    job_id = str(
        uuid.uuid4()
    )

    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "current_chunk": 0,
        "total_chunks": 0,
        "filename": None,
        "error": None,
        "created_at": time.time(),
        "updated_at": time.time()
    }

    print(
        f"NEW JOB: {job_id}",
        flush=True
    )

    # Start background processing.
    asyncio.create_task(
        run_background_job(
            job_id,
            text,
            voice,
            req.speed
        )
    )

    # IMPORTANT:
    # Return immediately.
    # The browser will poll /status/{job_id}.
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "TTS generation started."
    }


# ============================================================
# JOB STATUS
# ============================================================

@app.get("/status/{job_id}")
async def get_status(job_id: str):

    job = jobs.get(job_id)

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "current_chunk": job["current_chunk"],
        "total_chunks": job["total_chunks"],
        "filename": job["filename"],
        "error": job["error"]
    }


# ============================================================
# AUDIO
# ============================================================

@app.get("/audio/{job_id}")
async def get_audio(job_id: str):

    job = jobs.get(job_id)

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if job["status"] != "completed":

        return JSONResponse(
            status_code=202,
            content={
                "status": job["status"],
                "message": "Audio is not ready yet."
            }
        )

    filename = job.get("filename")

    if not filename:

        raise HTTPException(
            status_code=500,
            detail="Audio filename missing."
        )

    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )

    if not os.path.exists(filepath):

        raise HTTPException(
            status_code=404,
            detail="Audio file has expired or was removed."
        )

    return FileResponse(
        filepath,
        media_type="audio/wav",
        filename=filename
    )


# ============================================================
# DELETE JOB
# ============================================================

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):

    job = jobs.get(job_id)

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    filename = job.get("filename")

    if filename:

        filepath = os.path.join(
            OUTPUT_DIR,
            filename
        )

        try:

            if os.path.exists(filepath):

                os.remove(filepath)

        except Exception:
            pass

    del jobs[job_id]

    return {
        "status": "deleted",
        "job_id": job_id
    }

