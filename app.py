from fastapi import FastAPI, HTTPException,Request
from fastapi import UploadFile, File  #Handles file uploads.
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates #Renders HTML with dynamic data
from fastapi.middleware.cors import CORSMiddleware  #Added CORS   Allows JS from another port to call the API.
from pydantic import BaseModel #basemodel help in validation
import requests  #Makes API calls to 3rd party services.
import os
from dotenv import load_dotenv
from pathlib import Path
import shutil  #Copies uploaded files to disk.
import uuid  #Creates unique filenames
import assemblyai as aai   # Speech-to-text transcription API.
from murf import Murf

# Load .env file
load_dotenv(dotenv_path=Path(".") / ".env")
MURF_API_KEY = os.getenv("MURF_API_KEY")

# Initialize Murf client
murf_client = Murf(api_key=os.getenv("MURF_API_KEY"))

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

#Sets up transcription API.
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


#Gets available voices from Murf.
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


#Stores uploaded audio in uploads/.
#Returns file info.
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

 #Transcribe Audio
#Reads audio.
#Sends to AssemblyAI.
#Returns transcription text.
@app.post("/transcribe/file")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_bytes)

        return {"transcript": transcript.text}

    except Exception as e:
        return {"error": str(e)}


# Receives user’s raw audio.
# Uses AssemblyAI to convert speech → text.
# Sends that text to Murf for TTS.
# Returns the Murf-generated audio URL for playback.

@app.post("/tts/echo")
async def tts_echo(file: UploadFile = File(...)):
    try:
        # 1. Read the uploaded audio file
        audio_bytes = await file.read()

        # 2. Transcribe audio using AssemblyAI
        transcriber = aai.Transcriber()
        transcription = transcriber.transcribe(audio_bytes).text

        # 3. Send transcription to Murf for new voice audio
        response = murf_client.text_to_speech.generate(
            text=transcription,
            voice_id="en-US-cooper"  # choose any valid Murf voice
        )

        # 4. Return Murf audio URL
        return {"audio_url": response.audio_file}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))