from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory storage for heart rate data
current_data = {
    "bpm": 0,
    "source": "None"
}

class BPMData(BaseModel):
    bpm: int
    source: str = "Manual Entry"

@app.post("/api/bpm")
async def update_bpm(data: BPMData):
    current_data["bpm"] = data.bpm
    current_data["source"] = data.source
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
        <title>Biometric Music Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background-color: #121212; color: white; padding: 20px; }
            .card { background-color: #1e1e1e; padding: 20px; border-radius: 12px; margin: 20px auto; max-width: 400px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            button { background-color: #1db954; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 20px; cursor: pointer; margin: 5px; }
            button:hover { background-color: #1ed760; }
            input { padding: 10px; font-size: 16px; border-radius: 8px; border: none; width: 60%; text-align: center; }
            .mode-btn { background-color: #333; }
            .active-mode { background-color: #1db954 !important; }
            .bpm-display { font-size: 48px; font-weight: bold; margin: 10px 0; color: #1db954; }
        </style>
    </head>
    <body>
        <h1>Biometric Music Dashboard</h1>
        
        <!-- Mode Switcher -->
        <div>
            <button id="btn-mode1" class="mode-btn active-mode" onclick="setMode('manual')">Mode 1: Manual Entry</button>
            <button id="btn-mode2" class="mode-btn" onclick="setMode('esp32')">Mode 2: ESP32 Stream</button>
        </div>

        <!-- Mode 1: Manual Input Section -->
        <div id="manual-section" class="card">
            <h2>Mode 1: Manual Entry</h2>
            <p>Enter heart rate measured from your phone:</p>
            <input type="number" id="manual-bpm" placeholder="Enter BPM (e.g. 75)">
            <br><br>
            <button onclick="submitManualBPM()">Submit BPM</button>
        </div>

        <!-- Mode 2: ESP32 Live Monitor Section -->
        <div id="esp32-section" class="card" style="display:none;">
            <h2>Mode 2: ESP32 Live Stream</h2>
            <p>Listening for incoming data from your ESP32 board...</p>
        </div>

        <!-- Shared Live Status Display -->
        <div class="card">
            <h3>Current Active Reading</h3>
            <div id="bpm-value" class="bpm-display">-- BPM</div>
            <p id="source-value">Source: Waiting for data...</p>
        </div>

        <script>
            let currentMode = 'manual';

            function setMode(mode) {
                currentMode = mode;
                document.getElementById('manual-section').style.display = (mode === 'manual') ? 'block' : 'none';
                document.getElementById('esp32-section').style.display = (mode === 'esp32') ? 'block' : 'none';
                
                document.getElementById('btn-mode1').classList.toggle('active-mode', mode === 'manual');
                document.getElementById('btn-mode2').classList.toggle('active-mode', mode === 'esp32');
            }

            async function submitManualBPM() {
                const bpm = document.getElementById('manual-bpm').value;
                if (!bpm) return alert("Please enter a valid BPM value!");
                
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
                        document.getElementById('bpm-value').innerText = data.bpm + " BPM";
                        document.getElementById('source-value').innerText = "Source: " + data.source;
                    }
                } catch(e) {}
            }

            // Auto-refresh data every 3 seconds for Mode 2 updates
            setInterval(fetchBPM, 3000);
            fetchBPM();
        </script>
    </body>
    </html>
    """
