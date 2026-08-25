from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import time
import asyncio

app = FastAPI()

current_state = {
    "bpm": 72.0,
    "biometric_state": "Neutral / Relaxed",
    "language": "Tamil",
    "mode": "regulate",
    "track_name": "Default Normal Track",
    "track_url": "https://music.youtube.com/search?q=tamil+lofi+chill+beats+tracks",
    "last_updated": time.time()
}

YOUTUBE_MUSIC_MAP = {
    "Tamil": {
        "Calm": {"name": "Tamil Peaceful Melodies", "url": "https://music.youtube.com/search?q=tamil+calm+peaceful+melodies+songs+only"},
        "Normal": {"name": "Tamil Lofi Chill Beats", "url": "https://music.youtube.com/search?q=tamil+lofi+chill+beats+tracks"},
        "Energetic": {"name": "Tamil Kuthu & Dance Hits", "url": "https://music.youtube.com/search?q=tamil+energetic+kuthu+dance+hits+songs"}
    },
    "Malayalam": {
        "Calm": {"name": "Malayalam Soft Acoustic Melodies", "url": "https://music.youtube.com/search?q=malayalam+soft+calming+melodies+songs"},
        "Normal": {"name": "Malayalam Chill Beats", "url": "https://music.youtube.com/search?q=malayalam+chill+lofi+beats+songs"},
        "Energetic": {"name": "Malayalam Fast Beat Dance Songs", "url": "https://music.youtube.com/search?q=malayalam+energetic+dance+hits+songs"}
    },
    "Kannada": {
        "Calm": {"name": "Kannada Peaceful Melodies", "url": "https://music.youtube.com/search?q=kannada+peaceful+melodies+songs"},
        "Normal": {"name": "Kannada Lofi Chill", "url": "https://music.youtube.com/search?q=kannada+chill+lofi+songs"},
        "Energetic": {"name": "Kannada Mass & Dance Beats", "url": "https://music.youtube.com/search?q=kannada+high+energy+mass+beats+songs"}
    },
    "Telugu": {
        "Calm": {"name": "Telugu Calming Melodies", "url": "https://music.youtube.com/search?q=telugu+calm+melodies+songs"},
        "Normal": {"name": "Telugu Chill Lofi Beats", "url": "https://music.youtube.com/search?q=telugu+chill+lofi+beats+songs"},
        "Energetic": {"name": "Telugu High-Voltage Party Hits", "url": "https://music.youtube.com/search?q=telugu+mass+dance+party+hits+songs"}
    },
    "Hindi": {
        "Calm": {"name": "Hindi Meditative & Soft Melodies", "url": "https://music.youtube.com/search?q=hindi+soft+acoustic+calming+songs"},
        "Normal": {"name": "Hindi Lofi & Chill Vibe", "url": "https://music.youtube.com/search?q=hindi+lofi+chill+vibes+songs"},
        "Energetic": {"name": "Bollywood Workout & Gym Hits", "url": "https://music.youtube.com/search?q=bollywood+workout+dance+hits+songs"}
    },
    "International": {
        "Calm": {"name": "Ambient Soundscapes & Deep Relaxation", "url": "https://music.youtube.com/search?q=ambient+peaceful+relaxation+music"},
        "Normal": {"name": "Lofi Hip Hop Radio Beats", "url": "https://music.youtube.com/search?q=lofi+hip+hop+beats"},
        "Energetic": {"name": "Upbeat Electronic Pop Mix", "url": "https://music.youtube.com/search?q=upbeat+pop+workout+hits"}
    }
}

class TelemetryData(BaseModel):
    bpm: float

class ConfigPayload(BaseModel):
    language: str = None
    mode: str = None

def get_recommendation(bpm: float, lang: str, mode: str):
    if bpm > 90:
        raw_state = "High Stress / Anxiety"
        detected_category = "Energetic"
    elif 60 <= bpm <= 90:
        raw_state = "Neutral / Relaxed"
        detected_category = "Normal"
    else:
        raw_state = "Fatigue / Low Energy"
        detected_category = "Calm"

    if mode == "regulate":
        if detected_category == "Energetic":
            target_mood = "Calm"
        elif detected_category == "Calm":
            target_mood = "Energetic"
        else:
            target_mood = "Normal"
    else:
        target_mood = detected_category

    selected_lang = lang if lang in YOUTUBE_MUSIC_MAP else "Tamil"
    track_info = YOUTUBE_MUSIC_MAP[selected_lang][target_mood]

    return raw_state, target_mood, track_info["name"], track_info["url"]

def update_internal_state(bpm: float):
    global current_state
    current_state["bpm"] = bpm
    raw_state, target_mood, track_name, track_url = get_recommendation(
        bpm, current_state["language"], current_state["mode"]
    )
    current_state["biometric_state"] = raw_state
    current_state["track_name"] = f"[{target_mood} Mood Target] {track_name}"
    current_state["track_url"] = track_url

async def check_input_timeout():
    while True:
        await asyncio.sleep(2)
        if time.time() - current_state["last_updated"] > 10:
            if current_state["bpm"] != 72.0:
                update_internal_state(72.0)

@app.on_event("startup")
async def startup_event():
    update_internal_state(72.0)
    asyncio.create_task(check_input_timeout())

@app.post("/api/bpm")
def receive_bpm(data: TelemetryData):
    global current_state
    current_state["last_updated"] = time.time()
    update_internal_state(data.bpm)
    return {"status": "success"}

@app.post("/api/config")
def set_config(payload: ConfigPayload):
    global current_state
    if payload.language:
        current_state["language"] = payload.language
    if payload.mode:
        current_state["mode"] = payload.mode
    update_internal_state(current_state["bpm"])
    return {"status": "config_updated"}

@app.get("/api/current")
def get_current():
    return current_state

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Biometric Music Dashboard</title>
        <style>
            body { 
                font-family: 'Segoe UI', Consolas, sans-serif; 
                background: #050505; 
                color: #ffffff; 
                text-align: center; 
                padding: 30px; 
            }
            h1 { 
                color: #ff0033; 
                text-shadow: 0 0 10px rgba(255, 0, 51, 0.6);
                letter-spacing: 2px;
            }
            .card { 
                background: #111111; 
                border: 2px solid #00ff66; 
                box-shadow: 0 0 15px rgba(0, 255, 102, 0.2);
                border-radius: 10px; 
                padding: 20px; 
                max-width: 500px; 
                margin: 20px auto; 
            }
            h3 {
                color: #00ff66;
                margin-top: 5px;
                letter-spacing: 1px;
            }
            .bpm { 
                font-size: 52px; 
                font-weight: bold; 
                color: #ff0033; 
                text-shadow: 0 0 15px rgba(255, 0, 51, 0.8);
            }
            .state { 
                color: #00ff66; 
                font-size: 18px; 
                margin-top: 5px; 
                font-weight: bold;
            }
            label {
                color: #ffffff;
                font-weight: bold;
            }
            select { 
                background: #000000; 
                color: #00ff66; 
                padding: 10px 15px; 
                border: 1px solid #ff0033; 
                border-radius: 6px; 
                font-size: 16px; 
                margin: 5px; 
                cursor: pointer; 
                outline: none;
            }
            select:focus {
                border-color: #00ff66;
                box-shadow: 0 0 8px rgba(0, 255, 102, 0.8);
            }
            .btn { 
                display: inline-block; 
                background: #ff0033; 
                color: #ffffff; 
                padding: 14px 28px; 
                border-radius: 6px; 
                text-decoration: none; 
                font-weight: bold; 
                margin-top: 15px; 
                box-shadow: 0 0 12px rgba(255, 0, 51, 0.5);
                transition: 0.3s ease;
            }
            .btn:hover { 
                background: #cc0029; 
                box-shadow: 0 0 20px rgba(255, 0, 51, 0.9);
            }
            #trackName {
                color: #e0e0e0;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <h1>BIOMETRIC MUSIC RECOMMENDER</h1>
        
        <div class="card">
            <h3>PREFERENCES</h3>
            <label>Language:</label>
            <select id="langSelect" onchange="updateConfig()">
                <option value="Tamil">Tamil</option>
                <option value="Malayalam">Malayalam</option>
                <option value="Kannada">Kannada</option>
                <option value="Telugu">Telugu</option>
                <option value="Hindi">Hindi</option>
                <option value="International">International</option>
            </select>
            <br><br>
            <label>Goal:</label>
            <select id="modeSelect" onchange="updateConfig()">
                <option value="regulate">Regulate BPM (Balance Pulse)</option>
                <option value="match">Match BPM (Reflect Mood)</option>
            </select>
        </div>

        <div class="card">
            <h3>LIVE HEART RATE</h3>
            <div class="bpm" id="bpm">72 BPM</div>
            <div class="state" id="state">State: Neutral / Relaxed</div>
        </div>

        <div class="card">
            <h3>RECOMMENDED TRACK</h3>
            <p id="trackName">Loading...</p>
            <a id="musicBtn" href="#" target="_blank" class="btn">▶ PLAY ON YOUTUBE MUSIC</a>
        </div>

        <script>
            async function updateConfig() {
                const lang = document.getElementById('langSelect').value;
                const mode = document.getElementById('modeSelect').value;
                await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({language: lang, mode: mode})
                });
                pollData();
            }

            async function pollData() {
                const res = await fetch('/api/current');
                const data = await res.json();
                
                document.getElementById('bpm').innerText = `${data.bpm} BPM`;
                document.getElementById('state').innerText = `State: ${data.biometric_state}`;
                document.getElementById('trackName').innerText = `[${data.language}] ${data.track_name}`;
                document.getElementById('musicBtn').href = data.track_url;
            }

            setInterval(pollData, 2000);
            pollData();
        </script>
    </body>
    </html>
    """