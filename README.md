# 🎙️ AI Voice Agent

An AI-powered conversational voice agent that lets you **speak to an AI**, converts your speech to text, generates intelligent responses, and plays them back in natural voice — all in real time.  
Built for **Day 12 of the 30 Days of AI Voice Agents Challenge**.

---

## 🏗️ Architecture

This project follows a **client-server architecture**:

- **Frontend (HTML, CSS, JavaScript)**  
  - Records audio from the user.  
  - Sends audio to the backend for transcription.  
  - Displays conversation history in a chat-style interface.  
  - Plays back the AI-generated audio response automatically.  

- **Backend (Python - FastAPI)**  
  - Receives audio from the frontend.  
  - Uses **AssemblyAI API** for Speech-to-Text (STT).  
  - Sends transcribed text to **Google Gemini API** for generating AI responses.  
  - Converts AI response text to audio using **Murf AI Text-to-Speech (TTS)**.  
  - Returns both the text and audio to the frontend.  

---

## 📦 Features

- 🎙️ Record voice directly in the browser.  
- 📝 Real-time speech-to-text conversion using AssemblyAI.  
- 🤖 Intelligent AI replies powered by Google Gemini.  
- 🔊 Natural text-to-speech output using Murf AI.  
- 💬 Chat-style interface showing both user and AI messages.  
- 🗂️ **Conversation history saving** — view past chat messages during the session.  
- 🎯 Simple Start/Stop recording controls.  

---

## 🛠️ Technologies Used

- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python (FastAPI)  
- **Speech-to-Text:** AssemblyAI API  
- **AI Chat Response:** Google Gemini API  
- **Text-to-Speech:** Murf AI API  

---

## ⚙️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/voice-agent.git
   cd voice-agent
   
2. **Create and activate a virtual environment**
   ```python -m virtualenv venv
   source venv/bin/activate   # Mac/Linux
   .\venv\Scripts\activate
   
3. **Install dependencies**
   pip install -r requirements.txt
   
4. **Create a .env file in the root folder and add your API keys:**
   MURF_API_KEY = <---your api key--->
   GEMINI_API_KEY =  <---your api key--->
   ASSEMBLYAI_API_KEY =  <---your api key--->

5.**Start the backend server**
   uvicorn main:app --reload

  <img width="1366" height="728" alt="image" src="https://github.com/user-attachments/assets/bba16007-5fd8-4db2-900c-0de2bbb5040e" />



    
