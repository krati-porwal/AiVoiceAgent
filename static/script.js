// ====== TEXT TO SPEECH GENERATION ======
async function generateAudio() {
  const text = document.getElementById("textInput").value.trim();
  const voice = document.getElementById("voiceSelect").value;

  if (!text) {
    alert("Please enter some text.");
    return;
  }

  try {
    const response = await fetch("/generate-audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice_id: voice }),
    });

    const result = await response.json();

    if (result.audio_file) {
      const audioPlayer = document.getElementById("ttsAudioPlayer");
      audioPlayer.src = result.audio_file;
      audioPlayer.oncanplaythrough = () => {
        audioPlayer.play().catch(() => {
          alert("Audio is ready. Click Play to listen.");
        });
      };
    }else if (result.transcript) {
         alert(result.transcript); // Show fallback text
    } else {
       alert("Failed to generate audio.");
  }  
  } catch (error) {
    console.error("Error generating audio:", error);
    alert("Something went wrong.");
  }
}

// ====== AUDIO RECORDING VARIABLES ======
let mediaRecorder;
let recordedChunks = [];

// ====== SESSION ID ======
const urlParams = new URLSearchParams(window.location.search);
let sessionId = urlParams.get("session_id");
if (!sessionId) {
  sessionId = crypto.randomUUID();
  window.history.replaceState({}, "", `?session_id=${sessionId}`);
}

// ====== START RECORDING ======
function startRecording() {
  recordedChunks = [];
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then((stream) => {
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
      };
      mediaRecorder.onstop = handleRecordingStop;
      mediaRecorder.start();
      console.log("Recording started");
    })
    .catch((err) => {
      alert("Microphone access denied: " + err.message);
    });
}

// ====== STOP RECORDING ======
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    console.log("Recording stopped");
  }
}

// ====== HANDLE RECORDING STOP ======
async function handleRecordingStop() {
  const blob = new Blob(recordedChunks, { type: "audio/webm" });

  // 1️⃣ Show placeholder in chat
  const chatBox = document.getElementById("chat-box");
  const userMsg = document.createElement("div");
  userMsg.className = "chat user";
  userMsg.innerText = "Transcribing...";
  chatBox.appendChild(userMsg);

  try {
    // 2️⃣ Transcribe
    const transData = await transcribeAudio(blob);
    userMsg.innerText = transData.transcript || "[Transcription failed]";

    // 3️⃣ Send to AI and get reply
    const botReply = await chatWithAgent(blob);

    // 4️⃣ Show AI reply text
   const botMsg = document.createElement("div");
   botMsg.className = "chat bot";

    // Prefer transcript > text, but don't duplicate
   let replyText = botReply.transcript || botReply.text || "[No reply]";
   botMsg.innerText = replyText;
   chatBox.appendChild(botMsg);


    // 5️⃣ Play AI reply audio if exists
    if (botReply.audio_file) {
      const botAudio = document.createElement("audio");
      botAudio.controls = true;
      botAudio.src = botReply.audio_file;
      botMsg.appendChild(botAudio);
      botAudio.play().catch(() => {
        console.log("Audio ready, click play to listen.");
      });
    }
  } catch (err) {
    console.error("Error in stop-record flow:", err);
    alert("Something went wrong while processing your recording.");
  }
}

// ====== TRANSCRIBE AUDIO ======
async function transcribeAudio(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/transcribe/file", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  document.getElementById("transcriptText").innerText = data.transcript || data.error;
  return data;
}

// ====== CHAT WITH AI AGENT ======
async function chatWithAgent(blob) {
  const formData = new FormData();
  formData.append("file", blob, "voice.webm");
  formData.append("voice_id", document.getElementById("voiceSelect").value);

  const response = await fetch(`/agent/chat/${sessionId}`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  return data;
}
