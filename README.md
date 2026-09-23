# Hindi AI Text-to-Speech

A Hindi Text-to-Speech (TTS) application built with **FastAPI** and **Piper TTS**.

The application converts Hindi text into WAV audio using a Piper voice model and provides a web interface for generating and downloading speech.

---

## Features

- Hindi text-to-speech generation
- Piper TTS engine
- FastAPI backend
- Responsive web interface
- Background TTS processing
- Job ID based generation
- Progress tracking
- Audio download
- Multiple voice options
- Adjustable speech speed
- Supports large Hindi text
- Works on Windows and Ubuntu/Linux

---

# Project Structure

```text
tts/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── README.md
│
├── static/
│   └── index.html
│
├── voices/
│   ├── hi_IN-rohan-medium.onnx
│   └── hi_IN-rohan-medium.onnx.json
│
├── output/
│   └── generated WAV files
│
├── tmp/
│   └── temporary TTS files
│
└── venv/
    └── Python virtual environment
	
	
	Windows

Recommended:

Windows 10/11
Python 3.11
pip
Git
At least 4 GB RAM
Internet connection for installing dependencies
Ubuntu

Recommended:

Ubuntu 20.04 / 22.04 / 24.04
Python 3.11
pip
Git
At least 4 GB RAM
1. Windows Installation
Step 1 - Install Python

Download Python 3.11 from:

https://www.python.org/downloads/

During installation, make sure:

Add Python to PATH

is checked.

Verify:

python --version

Expected:

Python 3.11.x
Step 2 - Clone the Project

Example:

git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

Enter the project:

cd tts

If you already have the project locally, simply open the project directory.

2. Create Virtual Environment - Windows

Create the virtual environment:

python -m venv venv

Activate it:

venv\Scripts\activate

You should see:

(venv)

in the terminal.

3. Install Python Dependencies - Windows

Upgrade pip:

python -m pip install --upgrade pip

Install requirements:

pip install -r requirements.txt

If Piper is included in requirements.txt, it will be installed automatically.

Verify:

pip show piper-tts
4. Download / Add Piper Voice Model

Place the Hindi Piper model inside:

voices/

Example:

voices/
├── hi_IN-rohan-medium.onnx
└── hi_IN-rohan-medium.onnx.json

The .onnx and .onnx.json files must have matching names.

Example:

hi_IN-rohan-medium.onnx
hi_IN-rohan-medium.onnx.json
5. Find Piper Executable - Windows

After installing Piper, find the executable:

where piper

If Piper is installed inside the virtual environment, it may be located at:

venv\Scripts\piper.exe

The application should use:

venv\Scripts\piper.exe

on Windows.

6. Windows Configuration

In app.py, Windows Piper configuration should look similar to:

PIPER_EXE = os.path.join(
    BASE_DIR,
    "venv",
    "Scripts",
    "piper.exe"
)

Voice model:

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
7. Test Piper - Windows

Test Piper directly:

"नमस्ते। यह हिंदी टेक्स्ट टू स्पीच परीक्षण है।" | `
venv\Scripts\piper.exe `
--model voices\hi_IN-rohan-medium.onnx `
--output_file test.wav

If successful:

test.wav

will be created.

Open the file and verify that the Hindi speech works.

8. Run FastAPI - Windows

Start the application:

venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000

Or:

uvicorn app:app --host 127.0.0.1 --port 8000

Open:

http://127.0.0.1:8000
9. Windows Development Mode

For development with automatic reload:

uvicorn app:app --host 127.0.0.1 --port 8000 --reload

Do not use --reload for production.

10. Test API - Windows

Open PowerShell:

$body = @{
    text = "नमस्ते। यह मेरा हिंदी टेक्स्ट टू स्पीच परीक्षण है।"
    voice = "hindi"
    speed = 1.0
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/generate" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

Expected response:

{
    "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "status": "queued",
    "message": "TTS generation started."
}
11. Check Job Status

Use the returned job_id:

http://127.0.0.1:8000/status/JOB_ID

Example:

http://127.0.0.1:8000/status/2d82db04-a37c-4193-9149-d04a56f79f24

Example response:

{
    "job_id": "2d82db04-a37c-4193-9149-d04a56f79f24",
    "status": "processing",
    "progress": 50,
    "current_chunk": 3,
    "total_chunks": 7
}

When completed:

{
    "job_id": "2d82db04-a37c-4193-9149-d04a56f79f24",
    "status": "completed",
    "progress": 100,
    "filename": "2026-09-23_04-33-43_hindi_xxxxx.wav"
}
12. Download Generated Audio

After the job is completed:

http://127.0.0.1:8000/audio/JOB_ID

Example:

http://127.0.0.1:8000/audio/2d82db04-a37c-4193-9149-d04a56f79f24
13. Health Check

Open:

http://127.0.0.1:8000/health

Example:

{
    "status": "ok",
    "piper": true,
    "voices": {
        "hindi": true,
        "male": true,
        "female": true
    }
}
14. Ubuntu Installation

Update packages:

sudo apt update
sudo apt upgrade -y

Install required packages:

sudo apt install -y python3 python3-pip python3-venv git

Check Python:

python3 --version

Recommended:

Python 3.11.x
15. Clone Project - Ubuntu
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git

Enter the directory:

cd tts
16. Create Virtual Environment - Ubuntu
python3 -m venv venv

Activate:

source venv/bin/activate

You should see:

(venv)
17. Install Dependencies - Ubuntu

Upgrade pip:

python -m pip install --upgrade pip

Install requirements:

pip install -r requirements.txt

Verify Piper:

pip show piper-tts
18. Add Hindi Voice Model - Ubuntu

Put the following files inside:

voices/

Example:

voices/
├── hi_IN-rohan-medium.onnx
└── hi_IN-rohan-medium.onnx.json
19. Find Piper - Ubuntu

Run:

which piper

Normally, when the virtual environment is activated:

/home/username/tts/venv/bin/piper

You can also check:

ls -lah venv/bin/piper
20. Ubuntu Configuration

In app.py:

PIPER_EXE = os.path.join(
    BASE_DIR,
    "venv",
    "bin",
    "piper"
)

This is different from Windows.

Windows
venv/Scripts/piper.exe
Ubuntu
venv/bin/piper
21. Test Piper - Ubuntu

Run:

echo "नमस्ते। यह हिंदी टेक्स्ट टू स्पीच परीक्षण है।" | \
venv/bin/piper \
--model voices/hi_IN-rohan-medium.onnx \
--output_file test.wav

Check:

ls -lh test.wav

Play the generated WAV file.

22. Run FastAPI - Ubuntu

Activate the environment:

source venv/bin/activate

Run:

uvicorn app:app --host 0.0.0.0 --port 8000

Open:

http://YOUR_SERVER_IP:8000

For local Ubuntu:

http://127.0.0.1:8000
23. Development Mode - Ubuntu
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
24. Test API - Ubuntu
curl -i -X POST "http://127.0.0.1:8000/generate" \
-H "Content-Type: application/json" \
-d '{"text":"नमस्ते। यह मेरा हिंदी टेक्स्ट टू स्पीच परीक्षण है।","voice":"hindi","speed":1.0}'

Expected:

{
    "job_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "status": "queued",
    "message": "TTS generation started."
}
25. Check Status - Ubuntu
curl "http://127.0.0.1:8000/status/JOB_ID"

Example:

curl "http://127.0.0.1:8000/status/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
26. Download Audio - Ubuntu
curl \
"http://127.0.0.1:8000/audio/JOB_ID" \
-o output.wav

Example:

curl \
"http://127.0.0.1:8000/audio/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
-o output.wav
27. Check Application Health
curl http://127.0.0.1:8000/health
Background Job Architecture

The application does not keep the HTTP request open while Piper generates long audio.

The process works like this:

User
  │
  ▼
POST /generate
  │
  ▼
Create Job ID
  │
  ▼
Return immediately
  │
  ▼
Background TTS Job
  │
  ├── Split text into chunks
  │
  ├── Piper generates chunk 1
  │
  ├── Piper generates chunk 2
  │
  ├── Piper generates chunk 3
  │
  ├── ...
  │
  └── Merge WAV files
          │
          ▼
      Final WAV

The frontend checks:

GET /status/{job_id}

until the job is completed.

Then it requests:

GET /audio/{job_id}