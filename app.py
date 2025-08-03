# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route("/")
# def home():
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True) 

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# Load .env file to get API key
load_dotenv()
MURF_API_KEY = os.getenv("MURF_API_KEY")

# Create FastAPI app
app = FastAPI()

# Input format
class TextInput(BaseModel):
    text: str

# backend route 
@app.post("/generate")
def generate(data: TextInput):
    url = "https://api.murf.ai/v1/speech/generate"

    headers = {
        "Authorization": f"Bearer {MURF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": data.text,
        "voice": "en-IN-Neerja"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))