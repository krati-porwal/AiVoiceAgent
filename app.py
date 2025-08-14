from fastapi import FastAPI, HTTPException,Request,UploadFile, File 
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates #Renders HTML with dynamic data
from fastapi.middleware.cors import CORSMiddleware  #Added CORS   Allows JS from another port to call the API.
from pydantic import BaseModel #basemodel help in validation
import requests  #Makes API calls to 3rd party services.
import os
from dotenv import load_dotenv
from pathlib import Path as FilePath
import shutil  #Copies uploaded files to disk.
import uuid  #Creates unique filenames  
from murf import Murf
from fastapi.responses import JSONResponse
from fastapi import Form, Path

# --- SDK Imports ---
import assemblyai as aai   # Speech-to-text transcription API.
import google.generativeai as genai


# Load .env file
load_dotenv(dotenv_path=FilePath(".") / ".env")


MURF_API_KEY = os.getenv("MURF_API_KEY")
murf_client = Murf(api_key=os.getenv("MURF_API_KEY"))

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Global chat history
chat_history = {}  # { session_id: [{"role": "user", "content": "..."}] }

app = FastAPI()

# CORS Middleware (IMPORTANT for fetch to work across ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Mount the /static route to serve JS/CSS etc.
app.mount("/static", StaticFiles(directory="static"), name="static")
#Tell FastAPI where to find your HTML templates
templates = Jinja2Templates(directory="templates")

class TextInput(BaseModel):
    text: str
    voice_id: str

class QueryRequest(BaseModel):
    text: str

#Define ChatResponse model for /agent/chat/{session_id}
class ChatResponse(BaseModel):
    audio_file: str
    transcript: str


    
#------------------------------Endpoints---------------------------------------
# Serve index.html at root path
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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
            "status_code": e.response.status_code if e.response else None,
            "message": e.response.text if e.response else None
        }
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        fb = fallback_response(getattr(data, "voice_id", "en-US-cooper"))
        return JSONResponse(
         content={"audio_file": fb["audio_file"], "transcript": fb["transcript"]},
          status_code=503
)


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
        return {"error": str(e), "message": getattr(e.response, "text", "No response")}


#Stores uploaded audio in uploads/.
#Returns file info.
@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)  # ✅ Create uploads directory if it doesn't exist

    # ✅ Generate a unique filename using uuid4
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_location = f"uploads/{unique_filename}"
  
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"[ERROR] Failed to save file: {str(e)}")
        fb = fallback_response()
        return JSONResponse(
    content={"audio_file": fb["audio_file"], "transcript": fb["transcript"]},
    status_code=503
)

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
    if not file.content_type.startswith("audio/"):
        return JSONResponse(content={"error": "Invalid file type. Please upload an audio file."}, status_code=400)
    try:
        audio_bytes = await file.read()

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_bytes)

        return {"transcript": transcript.text}

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        fb = fallback_response()
        return JSONResponse(
    content={"audio_file": fb["audio_file"], "transcript": fb["transcript"]},
    status_code=503
)



# Receives user’s raw audio.
# Uses AssemblyAI to convert speech → text.
# Sends that text to Murf for TTS.
# Returns the Murf-generated audio URL for playback.
@app.post("/tts/echo")
async def tts_echo(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        return JSONResponse(content={"error": "Invalid file type. Please upload an audio file."}, status_code=400)
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
        print(f"[ERROR] {str(e)}")
        fb = fallback_response()
        return JSONResponse(
    content={"audio_file": fb["audio_file"], "transcript": fb["transcript"]},
    status_code=503
)



@app.post("/llm/query")
async def llm_query(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        return JSONResponse(content={"error": "Invalid file type. Please upload an audio file."}, status_code=400)
    try:
        audio_bytes = await file.read()

        # Transcribe with AssemblyAI
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_bytes).text
        print("User said:", transcript)

        # Get LLM response
        model = genai.GenerativeModel("gemini-2.0-flash")
        llm_resp = model.generate_content(transcript)
        llm_text = llm_resp.text
        print("LLM response:", llm_text)

        # Generate TTS with Murf
        murf_resp = murf_client.text_to_speech.generate(
            text=llm_text[:3000],
            voice_id="en-US-cooper"
        )

        print("Murf API Response:", murf_resp)

        # Return JSON containing Murf audio URL
        return JSONResponse({"audio_file": murf_resp.audio_file})

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        fb = fallback_response()
        return JSONResponse(
    content={"audio_file": fb["audio_file"], "transcript": fb["transcript"]},
    status_code=503
)

@app.post("/agent/chat/{session_id}", response_model=ChatResponse)
async def agent_chat(
    session_id: str = Path(..., description="Unique conversation session ID"),
    file: UploadFile = File(...),
    voice_id: str = Form("en-US-cooper")  #Allow frontend to choose
):

    if not file.content_type.startswith("audio/"):
        return JSONResponse(content={"error": "Invalid file type. Please upload an audio file."}, status_code=400)
    
    try:
        # 1️⃣ Read uploaded audio
        audio_bytes = await file.read()

        # 2️⃣ Transcribe with AssemblyAI
        transcriber = aai.Transcriber()
        user_text = transcriber.transcribe(audio_bytes).text
        print(f"[{session_id}] User said:", user_text)

        # 3️⃣ Store user message in history
        if session_id not in chat_history:
            chat_history[session_id] = []
        chat_history[session_id].append({"role": "user", "content": user_text})

        # 4️⃣ Build conversation context
        context_text = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in chat_history[session_id]
        )

        # 5️⃣ Call LLM with context
        model = genai.GenerativeModel("gemini-2.0-flash")
        llm_resp = model.generate_content(context_text)
        llm_text = llm_resp.text
        print(f"[{session_id}] Assistant:", llm_text)

        # 6️⃣ Save LLM response
        chat_history[session_id].append({"role": "assistant", "content": llm_text})

        # 7️⃣ Convert to audio via Murf
        murf_resp = murf_client.text_to_speech.generate(
            text=llm_text[:3000],
            voice_id=voice_id 
        )

        return ChatResponse(audio_file=murf_resp.audio_file, transcript=llm_text)

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        fb = fallback_response(voice_id)
        return JSONResponse(
    content={"audio_file": fb["audio_file"], "transcript": fb["transcript"]},
    status_code=503
)

@app.get("/history")
def get_history():
    try:
        return {"history": chat_history}
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return JSONResponse(content={"error": "Could not fetch history"}, status_code=500)

# -------------------------
# FALLBACK AUDIO FUNCTION
# -------------------------
def fallback_response(voice_id="en-US-cooper"):
    """Return a safe default response when an API fails."""
    fallback_text = "I'm having trouble connecting right now. Please try again later."

    try:
        murf_resp = murf_client.text_to_speech.generate(
            text=fallback_text,
            voice_id=voice_id
        )
        return {"audio_file": murf_resp.audio_file, "transcript": fallback_text}
    except Exception:
        # If Murf also fails, just return text
        return {"audio_file": None, "transcript": fallback_text}