from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel
import subprocess
import uuid
import os

app = FastAPI()

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TTSRequest(BaseModel):
    text: str
    voice: str = "female"
    speed: float = 1.0

VOICE_MAP = {
    "female": "voices/en_US-amy-medium.onnx",
    "male": "voices/en_US-arctic-medium.onnx",
}

@app.post("/generate")
def generate(req: TTSRequest):
    model_path = VOICE_MAP.get(req.voice, VOICE_MAP["female"])
    output_path = os.path.join(OUTPUT_DIR, f"{uuid.uuid4()}.wav")

    length_scale = 1.0 / req.speed  # piper speed control

    subprocess.run(
        [
            "piper",
            "--model", model_path,
            "--output_file", output_path,
            "--length_scale", str(length_scale),
        ],
        input=req.text.encode("utf-8"),
        check=True,
    )

    with open(output_path, "rb") as f:
        audio_bytes = f.read()

    os.remove(output_path)  # cleanup, don't accumulate files on server disk

    return Response(content=audio_bytes, media_type="audio/wav")