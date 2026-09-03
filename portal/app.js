/**
 * ULTRON WEB HUD JAVASCRIPT CONTROLLER
 * Handles real-time telemetry updates, speech recognition, and command dispatch.
 */

document.addEventListener("DOMContentLoaded", () => {
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-trigger");
  const micBtn = document.getElementById("mic-trigger");
  const outputBox = document.getElementById("output-box");
  const headline = document.getElementById("hud-headline");
  const waveform = document.getElementById("waveform");

  // Vitals elements
  const valCpu = document.getElementById("val-cpu");
  const valRam = document.getElementById("val-ram");
  const valRamText = document.getElementById("val-ram-text");
  const valDisk = document.getElementById("val-disk");
  const valBatt = document.getElementById("val-batt");

  let isListening = false;
  let recognition = null;

  // Initialize Web Speech API if supported
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add("listening");
      headline.textContent = "Listening to your voice...";
      waveform.style.opacity = "1";
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      userInput.value = transcript;
      executeCommand(transcript);
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopListening();
    };

    recognition.onend = () => {
      stopListening();
    };
  }

  function stopListening() {
    isListening = false;
    micBtn.classList.remove("listening");
    headline.textContent = "Ultron standing by for next instruction.";
    waveform.style.opacity = "0.4";
  }

  micBtn.addEventListener("click", () => {
    if (!recognition) {
      alert("Voice recognition not supported in this browser. Please type your command.");
      return;
    }
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });

  // Submit via button or Enter
  sendBtn.addEventListener("click", () => {
    const cmd = userInput.value.trim();
    if (cmd) {
      executeCommand(cmd);
    }
  });

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const cmd = userInput.value.trim();
      if (cmd) {
        executeCommand(cmd);
      }
    }
  });

  window.sendQuickCommand = function(cmd) {
    userInput.value = cmd;
    executeCommand(cmd);
  };

  async function executeCommand(cmd) {
    appendLog("user", `> ${cmd}`);
    headline.textContent = `Analyzing: "${cmd}"`;
    userInput.value = "";
    userInput.disabled = true;

    try {
      // Send to local Ultron server API
      const res = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd })
      });

      if (res.ok) {
        const data = await res.json();
        headline.textContent = data.spoken_response || "Task complete.";
        appendLog("success", `[ULTRON]: ${data.spoken_response}`);

        // Update events
        refreshEvents();
      } else {
        fallbackExecution(cmd);
      }
    } catch (err) {
      // Offline fallback if portal opened statically without portal_server
      fallbackExecution(cmd);
    } finally {
      userInput.disabled = false;
      userInput.focus();
    }
  }

  function fallbackExecution(cmd) {
    headline.textContent = `Transmitted to Ultron engine: "${cmd}"`;
    appendLog("system", `[LOCAL TRANSMIT]: Command received. To execute with live Windows control, ensure 'python portal_server.py' is running.`);
  }

  function appendLog(type, message) {
    const entry = document.createElement("div");
    entry.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    entry.innerHTML = `<span class="timestamp">[${time}]</span> ${message}`;
    outputBox.appendChild(entry);
    outputBox.scrollTop = outputBox.scrollHeight;
  }

  // Poll vitals from backend
  async function pollVitals() {
    try {
      const res = await fetch("/api/vitals");
      if (res.ok) {
        const data = await res.json();
        valCpu.textContent = `${data.cpu_percent}%`;
        valRam.textContent = `${data.memory_percent}%`;
        valRamText.textContent = `${data.memory_used_gb} / ${data.memory_total_gb} GB`;
        valDisk.textContent = `${data.disk_percent}%`;
        valDiskText.textContent = `${data.disk_free_gb} GB Free`;
        if (data.battery_percent !== null) {
          valBatt.textContent = `${data.battery_percent}%`;
        }
      }
    } catch (e) {
      // Silent error if local server not yet started
    }
  }

  async function refreshEvents() {
    try {
      const res = await fetch("/api/events");
      if (res.ok) {
        const events = await res.json();
        const container = document.getElementById("events-stream");
        container.innerHTML = "";
        events.forEach(ev => {
          const card = document.createElement("div");
          card.className = "event-card";
          card.innerHTML = `
            <div class="event-top">
              <span class="agent-tag">${ev.agent_name}</span>
              <span class="event-time">${ev.timestamp.slice(11, 19)}</span>
            </div>
            <div class="event-action">${ev.action}</div>
            <div class="event-desc">${ev.target || ""}</div>
          `;
          container.appendChild(card);
        });
      }
    } catch (e) {}
  }

  setInterval(pollVitals, 3000);
  pollVitals();
  refreshEvents();
});
