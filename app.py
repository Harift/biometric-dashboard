import time
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

latest_biometrics = {
    "bpm": None,
    "last_seen": 0,
    "connected": False
}

TIMEOUT_SECONDS = 5

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BioSync - Dynamic Biometric Music</title>
  <style>
    body {
      background-color: #0b1329;
      color: #ffffff;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      transition: background-color 0.8s ease; /* Smooth full BG transition */
    }

    .dashboard-card {
      background: rgba(19, 30, 58, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      width: 90%;
      max-width: 750px;
      padding: 32px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      backdrop-filter: blur(10px);
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(10, 15, 29, 0.7);
      padding: 14px 20px;
      border-radius: 12px;
      font-size: 14px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .status-badge {
      font-weight: bold;
      padding: 4px 8px;
      border-radius: 6px;
    }

    .status-live { color: #22c55e; background: rgba(34, 197, 94, 0.1); }
    .status-offline { color: #ef4444; background: rgba(239, 68, 68, 0.1); }

    .bpm-container {
      text-align: center;
      background: rgba(9, 13, 26, 0.7);
      padding: 24px;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .bpm-value {
      font-size: 56px;
      font-weight: bold;
      color: #38bdf8;
      margin: 4px 0;
      transition: color 0.5s ease;
    }

    .bpm-waiting {
      font-size: 24px;
      color: #64748b;
    }

    .info-panel {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      background: rgba(10, 15, 29, 0.7);
      padding: 16px;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .info-box {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .info-title {
      font-size: 11px;
      color: #94a3b8;
      font-weight: bold;
      letter-spacing: 1px;
    }

    .info-value {
      font-size: 15px;
      font-weight: bold;
      color: #38bdf8;
      transition: color 0.5s ease;
    }

    canvas {
      background: rgba(2, 6, 23, 0.8);
      border-radius: 8px;
      width: 100%;
      height: 60px;
      margin-top: 8px;
    }

    .controls-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    label {
      font-size: 12px;
      color: #94a3b8;
      font-weight: 700;
      letter-spacing: 1px;
    }

    select, input, button {
      padding: 12px 14px;
      border-radius: 10px;
      border: none;
      font-size: 14px;
      font-weight: bold;
    }

    select, input {
      background: #1c2b4e;
      color: white;
      outline: none;
    }

    .btn-submit {
      grid-column: span 2;
      background: #38bdf8;
      color: #0b1329;
      font-size: 16px;
      cursor: pointer;
      margin-top: 6px;
      transition: all 0.3s ease;
    }

    .btn-submit:hover {
      filter: brightness(1.15);
    }

    .btn-disabled {
      background: #334155 !important;
      color: #94a3b8 !important;
      cursor: not-allowed !important;
    }

    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.75);
      justify-content: center;
      align-items: center;
      z-index: 100;
    }

    .modal-content {
      background: #131e3a;
      border: 1px solid #38bdf8;
      border-radius: 16px;
      padding: 24px;
      max-width: 400px;
      text-align: center;
    }

    .modal-btn {
      width: 100%;
      margin-top: 10px;
      cursor: pointer;
      background: #1c2b4e;
      color: #ffffff;
      border: 1px solid #38bdf8;
    }

    .modal-btn:hover {
      background: #38bdf8;
      color: #0b1329;
    }
  </style>
</head>
<body>

<div class="dashboard-card">
  
  <div class="header-bar">
    <span>ESP32 SENSOR: <span id="esp-status-badge" class="status-badge status-offline">WAITING FOR ESP32</span></span>
    <div>
      <span style="color: #94a3b8; margin-right: 8px;">INPUT MODE:</span>
      <select class="mode-select-header" id="input-mode-select" onchange="toggleInputMode()">
        <option value="esp32" selected>ESP32 Hardware Stream</option>
        <option value="manual">Manual BPM Input</option>
      </select>
    </div>
  </div>

  <div class="bpm-container">
    <div style="font-size: 12px; color: #94a3b8; font-weight: bold; letter-spacing: 1.5px;">BIOMETRIC STREAM</div>
    <div class="bpm-value" id="bpm-val"><span class="bpm-waiting">Touch ESP32 Sensor...</span></div>
    
    <div id="manual-input-container" style="display: none; margin-top: 10px;">
      <input type="number" id="manual-bpm-field" placeholder="Enter BPM (e.g. 75)" min="40" max="200" oninput="updateAnalysis()" style="width: 200px; text-align: center;">
    </div>

    <canvas id="ecgCanvas" width="600" height="60"></canvas>
  </div>

  <div class="info-panel">
    <div class="info-box">
      <span class="info-title">DETECTED MOOD STATE</span>
      <span class="info-value" id="detected-mood">Waiting for Data...</span>
    </div>
    <div class="info-box">
      <span class="info-title">RECOMMENDED GENRE</span>
      <span class="info-value" id="suggested-genre">Waiting for Selection...</span>
    </div>
  </div>

  <div class="controls-grid">
    <div class="form-group">
      <label for="lang-select">SELECT MUSIC LANGUAGE</label>
      <select id="lang-select" onchange="updateAnalysis()">
        <option value="Tamil">Tamil</option>
        <option value="International">International</option>
        <option value="Hindi">Hindi</option>
        <option value="Telugu">Telugu</option>
        <option value="Malayalam">Malayalam</option>
      </select>
    </div>

    <div class="form-group">
      <label for="target-mode">BIOMATCH TARGET MODE</label>
      <select id="target-mode" onchange="updateAnalysis()">
        <option value="maintain">Maintain My Mood</option>
        <option value="change">Change My Mood</option>
      </select>
    </div>

    <button id="rec-btn" class="btn-submit btn-disabled" onclick="handleRecommendationClick()" disabled>Waiting for Valid Input...</button>
  </div>

</div>

<div class="modal-overlay" id="highBpmModal">
  <div class="modal-content">
    <h3 style="margin-top:0; color:#ef4444;">High BPM Detected!</h3>
    <p style="font-size:14px; color:#94a3b8;">You selected <b>Maintain My Mood</b> with a high heart rate. Which vibe do you prefer?</p>
    <button class="modal-btn" onclick="triggerSearch('motivational')">🔥 Motivational, Gym & Pump-up</button>
    <button class="modal-btn" onclick="triggerSearch('breakup')">💔 Breakup & Soup Songs</button>
  </div>
</div>

<script>
  let isHardwareConnected = false;
  let espBpmValue = 0;
  let activeInputMode = "esp32";
  let activeWaveColor = '#38bdf8';

  const canvas = document.getElementById('ecgCanvas');
  const ctx = canvas.getContext('2d');
  let x = 0;

  function drawECG() {
    ctx.fillStyle = 'rgba(2, 6, 23, 0.15)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.beginPath();
    const activeState = (activeInputMode === 'esp32' && isHardwareConnected) || (activeInputMode === 'manual' && getActiveBPM() > 0);
    ctx.strokeStyle = activeState ? activeWaveColor : '#334155';
    ctx.lineWidth = 2;
    ctx.moveTo(x, canvas.height / 2);
    
    x += 4;
    if (x > canvas.width) x = 0;
    
    let y = canvas.height / 2;
    if (activeState && x % 60 > 25 && x % 60 < 35) {
      y += (Math.random() - 0.5) * 40;
    }
    
    ctx.lineTo(x, y);
    ctx.stroke();
    requestAnimationFrame(drawECG);
  }
  drawECG();

  function toggleInputMode() {
    activeInputMode = document.getElementById('input-mode-select').value;
    const manualContainer = document.getElementById('manual-input-container');
    const bpmValDisplay = document.getElementById('bpm-val');

    if (activeInputMode === 'manual') {
      manualContainer.style.display = 'block';
      bpmValDisplay.style.display = 'none';
    } else {
      manualContainer.style.display = 'none';
      bpmValDisplay.style.display = 'block';
    }
    updateAnalysis();
  }

  function getActiveBPM() {
    if (activeInputMode === 'manual') {
      return parseInt(document.getElementById('manual-bpm-field').value) || 0;
    }
    return espBpmValue;
  }

  async function pollESP32BPM() {
    try {
      const res = await fetch('/api/bpm');
      const data = await res.json();
      
      const badge = document.getElementById('esp-status-badge');
      const bpmContainer = document.getElementById('bpm-val');

      if (data && data.connected && data.bpm > 0) {
        isHardwareConnected = true;
        espBpmValue = data.bpm;

        badge.className = 'status-badge status-live';
        badge.innerText = 'LIVE [GPIO 13]';

        if (activeInputMode === 'esp32') {
          bpmContainer.innerHTML = `${data.bpm} <span style="font-size: 24px;">BPM</span>`;
        }
      } else {
        isHardwareConnected = false;
        espBpmValue = 0;

        badge.className = 'status-badge status-offline';
        badge.innerText = 'WAITING FOR ESP32';

        if (activeInputMode === 'esp32') {
          bpmContainer.innerHTML = `<span class="bpm-waiting">Touch ESP32 Sensor...</span>`;
        }
      }
      updateAnalysis();
    } catch (err) {
      console.log("Polling error:", err);
    }
  }

  setInterval(pollESP32BPM, 1000);

  function updateAnalysis() {
    const bpm = getActiveBPM();
    const targetMode = document.getElementById('target-mode').value;
    const lang = document.getElementById('lang-select').value;
    
    const moodEl = document.getElementById('detected-mood');
    const genreEl = document.getElementById('suggested-genre');
    const recBtn = document.getElementById('rec-btn');
    const bpmValEl = document.getElementById('bpm-val');

    if (!bpm || bpm <= 0) {
      document.body.style.backgroundColor = "#0b1329"; // Default dark bg
      moodEl.innerText = "Waiting for Data...";
      genreEl.innerText = "Waiting for Selection...";
      recBtn.disabled = true;
      recBtn.className = "btn-submit btn-disabled";
      recBtn.innerText = "Waiting for Valid Input...";
      activeWaveColor = '#334155';
      return;
    }

    recBtn.disabled = false;
    recBtn.className = "btn-submit";
    recBtn.innerText = "Open YouTube Music Recommendation →";

    // Dynamic Full Page Background & Accent Colors
    if (bpm >= 55 && bpm <= 66) {
      document.body.style.backgroundColor = "#0a192f"; // Calm Blue
      activeWaveColor = "#38bdf8";
      bpmValEl.style.color = "#38bdf8";
      moodEl.style.color = "#38bdf8";
      recBtn.style.background = "#38bdf8";
      moodEl.innerText = "Relaxed / Peaceful (Low BPM)";
    } else if (bpm >= 67 && bpm <= 82) {
      document.body.style.backgroundColor = "#06231a"; // Balanced Green
      activeWaveColor = "#22c55e";
      bpmValEl.style.color = "#22c55e";
      moodEl.style.color = "#22c55e";
      recBtn.style.background = "#22c55e";
      moodEl.innerText = "Calm Baseline / Normal Vibe";
    } else if (bpm >= 83 && bpm <= 170) {
      document.body.style.backgroundColor = "#2a0e0e"; // Energetic Red/Orange
      activeWaveColor = "#ef4444";
      bpmValEl.style.color = "#ef4444";
      moodEl.style.color = "#ef4444";
      recBtn.style.background = "#ef4444";
      moodEl.innerText = "High Energy / Excited / Stressed";
    } else {
      document.body.style.backgroundColor = "#0b1329";
      moodEl.innerText = "Out of Range";
    }

    let genreText = "";
    if (targetMode === "maintain") {
      if (bpm >= 55 && bpm <= 66) genreText = `${lang} Chill, Relaxing & Love Songs`;
      else if (bpm >= 67 && bpm <= 82) genreText = `${lang} Normal Vibe & Folk Hits`;
      else if (bpm >= 83 && bpm <= 170) genreText = `${lang} Gym Pump-up OR Breakup/Soup`;
      else genreText = `${lang} Trending Music`;
    } else {
      if (bpm >= 55 && bpm <= 66) genreText = `${lang} Motivational Gym Pump-up`;
      else if (bpm >= 67 && bpm <= 82) genreText = `${lang} Chill & Romantic Songs`;
      else if (bpm >= 83 && bpm <= 170) genreText = `${lang} Soothing Deep Relaxation`;
      else genreText = `${lang} Peaceful Music`;
    }

    genreEl.innerText = genreText;
  }

  function handleRecommendationClick() {
    const bpm = getActiveBPM();
    const targetMode = document.getElementById('target-mode').value;

    if (targetMode === "maintain" && bpm >= 83 && bpm <= 170) {
      document.getElementById('highBpmModal').style.display = 'flex';
    } else {
      triggerSearch();
    }
  }

  function triggerSearch(highBpmChoice = null) {
    document.getElementById('highBpmModal').style.display = 'none';

    const lang = document.getElementById('lang-select').value;
    const targetMode = document.getElementById('target-mode').value;
    const bpm = getActiveBPM();

    let query = "";

    if (targetMode === "maintain") {
      if (bpm >= 55 && bpm <= 66) {
        query = `${lang} chill relaxing love romantic songs`;
      } else if (bpm >= 67 && bpm <= 82) {
        query = `${lang} normal vibe folk upbeat hits`;
      } else if (bpm >= 83 && bpm <= 170) {
        if (highBpmChoice === "breakup") {
          query = `${lang} breakup soup sad emotional songs`;
        } else {
          query = `${lang} motivational gym pump up workout songs`;
        }
      } else {
        query = `${lang} trending music songs`;
      }
    } else {
      if (bpm >= 55 && bpm <= 66) {
        query = `${lang} motivational gym pump up workout songs`;
      } else if (bpm >= 67 && bpm <= 82) {
        query = `${lang} chill relaxing love romantic songs`;
      } else if (bpm >= 83 && bpm <= 170) {
        query = `${lang} deep relaxation calm soothing melodies`;
      } else {
        query = `${lang} soothing peaceful songs`;
      }
    }

    const ytMusicUrl = `https://music.youtube.com/search?q=${encodeURIComponent(query)}`;
    window.open(ytMusicUrl, '_blank');
  }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/bpm', methods=['GET', 'POST'])
def handle_bpm():
    global latest_biometrics
    
    if request.method == 'POST':
        data = request.get_json()
        if data and 'bpm' in data:
            latest_biometrics['bpm'] = int(data['bpm'])
            latest_biometrics['last_seen'] = time.time()
            latest_biometrics['connected'] = True
            return jsonify({"status": "success", "received": data['bpm']}), 200
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    is_active = (time.time() - latest_biometrics['last_seen']) < TIMEOUT_SECONDS
    latest_biometrics['connected'] = is_active

    return jsonify(latest_biometrics)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
