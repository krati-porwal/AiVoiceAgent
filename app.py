from fastapi import FastAPI, HTTPException
from pydantic import BaseModel #basemodel help in validation
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
load_dotenv(dotenv_path=Path(".") / ".env")
MURF_API_KEY = os.getenv("MURF_API_KEY")

app = FastAPI()

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