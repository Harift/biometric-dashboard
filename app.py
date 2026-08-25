from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_data = {
    "bpm": 0,
    "source": "None"
}

class BPMData(BaseModel):
    bpm: int
    source: Optional[str] = "Manual Entry"

@app.post("/api/bpm")
async def update_bpm(data: BPMData):
    current_data["bpm"] = data.bpm
    current_data["source"] = data.source or "ESP32 Sensor"
    return {"status": "success", "data": current_data}

@app.get("/api/bpm")
async def get_bpm():
    return current_data

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Biometric Music Recommender</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background-color: #121212; color: white; padding: 20px; }
            .card { background-color: #1e1e1e; padding: 20px; border-radius: 12px; margin: 15px auto; max-width: 450px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            button { background-color: #1db954; color: white; border: none; padding: 10px 18px; font-size: 15px; font-weight: bold; border-radius: 20px; cursor: pointer; margin: 5px; }
            button:hover { background-color: #1ed760; }
            .mode-btn { background-color: #333; }
            .active-mode { background-color: #1db954 !important; }
            input, select { padding: 10px; font-size: 15px; border-radius: 8px; border: none; width: 70%; margin: 8px 0; background-color: #2a2a2a; color: white; text-align: center; }
            .bpm-display { font-size: 52px; font-weight: bold; margin: 10px 0; }
            .normal { color: #1db954; }
            .elevated { color: #ff4d4d; }
            .yt-btn { display: inline-block; background-color: #ff0000; color: white; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 25px; margin-top: 15px; }
            .yt-btn:hover { background-color: #cc0000; }
        </style>
    </head>
    <body>
        <h1>Biometric Music Recommender</h1>
        
        <div>
            <button id="btn-mode1" class="mode-btn active-mode" onclick="setMode('manual')">Mode 1: Manual Entry</button>
            <button id="btn-mode2" class="mode-btn" onclick="setMode('esp32')">Mode 2: ESP32 Stream</button>
        </div>

        <!-- Preferences Section -->
        <div class="card">
            <h3>Music Preferences</h3>
            <label>Language Preference:</label><br>
            <select id="language" onchange="updateRecommendation()">
                <option value="English">English</option>
                <option value="Tamil">Tamil</option>
                <option value="Hindi">Hindi</option>
                <option value="Malayalam">Malayalam</option>
                <option value="Telugu">Telugu</option>
            </select>
            <br><br>
            <label>Mood Strategy:</label><br>
            <select id="strategy" onchange="updateRecommendation()">
                <option value="Match">Match Heart Rate (Maintain Vibe)</option>
                <option value="Regulate">Regulate Heart Rate (Calm / Boost)</option>
            </select>
        </div>

        <!-- Input Section -->
        <div id="manual-section" class="card">
            <h3>Mode 1: Manual Input</h3>
            <input type="number" id="manual-bpm" placeholder="Enter BPM (e.g. 75)">
            <br>
            <button onclick="submitManualBPM()">Submit Reading</button>
        </div>

        <div id="esp32-section" class="card" style="display:none;">
            <h3>Mode 2: ESP32 Sensor Stream</h3>
            <p style="color: #aaa;">Listening for live metrics from ESP32...</p>
        </div>

        <!-- Live Status & Recommendation Output -->
        <div class="card">
            <h3>Live Biometric Status</h3>
            <div id="bpm-value" class="bpm-display normal">-- BPM</div>
            <p id="bpm-state" style="font-size: 18px; font-weight: bold;">State: Idle</p>
            <p id="source-value" style="color: #888;">Source: Waiting for input</p>

            <hr style="border: 0.5px solid #333; margin: 20px 0;">

            <h3>Recommended Playlist</h3>
            <p id="music-recommendation" style="color: #bbb;">Enter BPM to generate recommendation.</p>
            <a id="yt-link" href="#" target="_blank" class="yt-btn" style="display:none;">Open YouTube Music ➔</a>
        </div>

        <script>
            let currentBPM = 0;

            function setMode(mode) {
                document.getElementById('manual-section').style.display = (mode === 'manual') ? 'block' : 'none';
                document.getElementById('esp32-section').style.display = (mode === 'esp32') ? 'block' : 'none';
                document.getElementById('btn-mode1').classList.toggle('active-mode', mode === 'manual');
                document.getElementById('btn-mode2').classList.toggle('active-mode', mode === 'esp32');
            }

            async function submitManualBPM() {
                const bpm = document.getElementById('manual-bpm').value;
                if (!bpm) return alert("Please enter a valid BPM!");
                
                await fetch('/api/bpm', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ bpm: parseInt(bpm), source: "Manual Entry" })
                });
                
                fetchBPM();
            }

            async function fetchBPM() {
                try {
                    const res = await fetch('/api/bpm');
                    const data = await res.json();
                    if (data.bpm > 0) {
                        currentBPM = data.bpm;
                        document.getElementById('source-value').innerText = "Source: " + data.source;
                        updateRecommendation();
                    }
                } catch(e) {}
            }

            function updateRecommendation() {
                if (currentBPM === 0) return;

                const lang = document.getElementById('language').value;
                const strategy = document.getElementById('strategy').value;
                const bpmDisplay = document.getElementById('bpm-value');
                const stateDisplay = document.getElementById('bpm-state');
                const recDisplay = document.getElementById('music-recommendation');
                const ytBtn = document.getElementById('yt-link');

                bpmDisplay.innerText = currentBPM + " BPM";

                let targetTempo = "";
                let query = "";

                if (currentBPM > 85) {
                    bpmDisplay.className = "bpm-display elevated";
                    stateDisplay.innerText = "State: Elevated / Stressed";
                    if (strategy === "Regulate") {
                        targetTempo = "Calming / Relaxing ambient beats to lower heart rate";
                        query = lang + " calming relaxing music";
                    } else {
                        targetTempo = "High-energy Workout / Upbeat tracks matching pulse";
                        query = lang + " high energy gym workout songs";
                    }
                } else {
                    bpmDisplay.className = "bpm-display normal";
                    stateDisplay.innerText = "State: Normal / Resting";
                    if (strategy === "Regulate") {
                        targetTempo = "Upbeat motivating tunes to boost energy";
                        query = lang + " energetic mood booster songs";
                    } else {
                        targetTempo = "Chill / Acoustic Melodies matching resting pulse";
                        query = lang + " chill acoustic lounge music";
                    }
                }

                recDisplay.innerText = targetTempo;
                ytBtn.href = "https://music.youtube.com/search?q=" + encodeURIComponent(query);
                ytBtn.style.display = "inline-block";
            }

            setInterval(fetchBPM, 3000);
            fetchBPM();
        </script>
    </body>
    </html>
    """
