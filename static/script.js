document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("queryForm");
  const input = document.getElementById("queryInput");
  const outputDiv = document.getElementById("output");
  const audioPlayer = document.getElementById("audioPlayer");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    outputDiv.textContent = "👩‍🍳 Thinking... whipping up a recipe for you!";
    
    try {
      const response = await fetch("/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        outputDiv.textContent = "⚠️ Error: " + (await response.text());
        return;
      }

      const data = await response.json();

      if (data.error) {
        outputDiv.textContent = "⚠️ " + data.error;
        return;
      }

      // Show text reply
      outputDiv.textContent = data.text || "No text reply.";

      // Play audio if available
      if (data.audio) {
        const audioBlob = new Blob(
          [Uint8Array.from(atob(data.audio), (c) => c.charCodeAt(0))],
          { type: "audio/mpeg" }
        );
        const url = URL.createObjectURL(audioBlob);
        audioPlayer.src = url;
        audioPlayer.play().catch((err) => {
          console.error("Audio playback failed:", err);
          outputDiv.textContent += "\n⚠️ Could not play audio.";
        });
      } else {
        outputDiv.textContent += "\n⚠️ No audio generated.";
      }
    } catch (err) {
      console.error(err);
      outputDiv.textContent = "⚠️ Error: " + err.message;
    }
  });
});
