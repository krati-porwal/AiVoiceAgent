from fastapi import FastAPI, HTTPException,Request
from fastapi import UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware  #Added CORS
from pydantic import BaseModel #basemodel help in validation
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import shutil
import uuid 
import assemblyai as aai

# Load .env file
load_dotenv(dotenv_path=Path(".") / ".env")
MURF_API_KEY = os.getenv("MURF_API_KEY")

app = FastAPI()

# CORS Middleware (IMPORTANT for fetch to work across ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 Mount the /static route to serve JS/CSS etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

# 👉 Tell FastAPI where to find your HTML templates
templates = Jinja2Templates(directory="templates")

aai.settings.api_key ="7a25540c2e374e109ccd261ce80a68a9"

# 🏠 Serve index.html at root path
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


class TextInput(BaseModel):
    text: str
    voice_id: str


@app.post("/generate-audio")  #decorators
def generate(data: TextInput):  #method define
    url = "https://api.murf.ai/v1/speech/generate"

    headers = {
        "api-key": MURF_API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "text": data.text,
        "voice_id": data.voice_id
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {
            "error": str(e),
            "status_code": response.status_code,
            "message": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voices")
def get_voices():
    url = "https://api.murf.ai/v1/speech/voices"
    headers = {
        "api-key": MURF_API_KEY,
        "accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "message": response.text}

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)  # ✅ Create uploads directory if it doesn't exist

    # ✅ Generate a unique filename using uuid4
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_location = f"uploads/{unique_filename}"
  
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get size
    size = os.path.getsize(file_location)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_in_bytes": size
    }

@app.post("/transcribe/file")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_bytes)

        return {"transcript": transcript.text}

    except Exception as e:
        return {"error": str(e)}