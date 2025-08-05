async function generateAudio() {
  const text = document.getElementById("textInput").value;
  const voice = document.getElementById("voiceSelect").value;

  if (!text) {
    alert("Please enter some text.");
    return;
  }

  try {
    const response = await fetch("/generate-audio", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: text,
        voice_id: voice,
      }),
    });

    const result = await response.json();

    if (result.audioFile) {
      const audioPlayer = document.getElementById("audioPlayer");
      audioPlayer.src = result.audioFile;

      // Wait for the audio to be ready before playing
      audioPlayer.oncanplaythrough = () => {
        audioPlayer.play().catch((error) => {
          console.error("Autoplay error:", error);
          alert("Audio is ready. Click Play to listen.");
        });
      };
    } else {
      alert("Failed to generate audio.");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Something went wrong.");
  }
}
 //echobot 
let mediaRecorder;
let recordedChunks = [];

function startRecording() {
  recordedChunks = [];
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((stream) => {
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = function (e) {
        if (e.data.size > 0) {
          recordedChunks.push(e.data);
        }
      };

      mediaRecorder.onstop = function () {
        const blob = new Blob(recordedChunks, { type: "audio/webm" });
        const audioURL = URL.createObjectURL(blob);
        const audio = document.getElementById("echoAudio");
        audio.src = audioURL;
        audio.play();
      };

      mediaRecorder.start();
      console.log("Recording started");
    })
    .catch((err) => {
      alert("Microphone access denied: " + err.message);
    });
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    console.log("Recording stopped");
  }
}