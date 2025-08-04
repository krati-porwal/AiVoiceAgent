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
        audioPlayer.play().catch(error => {
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
