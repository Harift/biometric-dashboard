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
    :root {
      --bg-color: #000000;
      --card-bg: #000000;
      --container-bg: #050505;
      --accent-color: #38bdf8;
      --glow-color: rgba(56, 189, 248, 0.2);
      --text-muted: #94a3b8;
    }

    /* 2-Second Ambient Entire Background Glow */
    @keyframes bgPulseGlow {
      0% { box-shadow: inset 0 0 40px var(--glow-color); }
      50% { box-shadow: inset 0 0 120px var(--glow-color); }
      100% { box-shadow: inset 0 0 40px var(--glow-color); }
    }

    body {
      background-color: var(--bg-color);
      color: #ffffff;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      transition: background-color 0.8s ease;
      animation: bgPulseGlow 2s infinite ease-in-out;
    }

    .dashboard-card {
      background: var(--card-bg);
      border: 1px solid var(--accent-color);
      border-radius: 20px;
      width: 90%;
      max-width: 750px;
      padding: 32px;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      gap: 20px;
      transition: all 0.8s ease;
    }

    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--container-bg);
      padding: 14px 20px;
      border-radius: 12px;
      font-size: 14px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      transition: all 0.8s ease;
    }

    .status-badge {
      font-weight: bold;
      padding: 4px 8px;
      border-radius: 6px;
    }

    .status-live { color: #22c55e; background: rgba(34, 197, 94, 0.15); }
    .status-offline { color: #ef4444; background: rgba(239, 68, 68, 0.15); }

    .bpm-container {
      text-align: center;
      background: var(--container-bg);
      padding: 24px;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      transition: all 0.8s ease;
    }

    .bpm-value {
      font-size: 56px;
      font-weight: bold;
      color: var(--accent-color);
      margin: 4px 0;
      transition: color 0.5s ease;
    }

    .bpm-waiting {
      font-size: 24px;
      color: var(--text-muted);
    }

    .info-panel {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      background: var(--container-bg);
      padding: 16px;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      transition: all 0.8s ease;
    }

    .info-box {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .info-title {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: bold;
      letter-spacing: 1px;
    }

    .info-value {
      font-size: 15px;
      font-weight: bold;
      color: var(--accent-color);
      transition: color 0.5s ease;
    }

    canvas {
      background: rgba(0, 0, 0, 0.6);
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
      color: var(--text-muted);
      font-weight: 700;
      letter-spacing: 1px;
    }

    select, input, button {
      padding: 12px 14px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      font-size: 14px;
      font-weight: bold;
      transition: all 0.5s ease;
    }

    select, input {
      background: var(--container-bg);
      color: #ffffff;
      outline: none;
    }

    .btn-submit {
      grid-column: span 2;
      background: var(--accent-color);
      color: #000000;
      font-size: 16px;
      cursor: pointer;
      margin-top: 6px;
      border: none;
      transition: all 0.3s ease;
    }

    .btn-submit:hover {
      filter: brightness(1.2);
    }

    .btn-disabled {
      background: #1e293b !important;
      color: #64748b !important;
      cursor: not-allowed !important;
      border: none !important;
    }

    /* Modal Styling */
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.9);
      justify-content: center;
      align-items: center;
      z-index: 100;
    }

    .modal-content {
      background: #090d16;
      border: 2px solid #ef4444;
      border-radius: 16px;
      padding: 24px;
      max-width: 400px;
      text-align: center;
    }

    .modal-btn {
      width: 100%;
      margin-top: 12px;
      padding: 12px;
      border-radius: 8px;
      cursor: pointer;
      background: #111827;
      color: #ffffff;
      border: 1px solid #ef4444;
      font-weight: bold;
    }

    .modal-btn:hover {
      background: #ef4444;
      color: #ffffff;
    }
  </style>
</head>
<body>

<div class="dashboard-card" id="main-card">
  
  <div class="header-bar">
    <span>ESP32 SENSOR: <span id="esp-status-badge" class="status-badge status-offline">WAITING FOR ESP32</span></span>
    <div>
      <span style="color: var(--text-muted); margin-right: 8px;">INPUT MODE:</span>
      <select class="mode-select-header" id="input-mode-select" onchange="toggleInputMode()">
        <option value="esp32" selected>ESP32 Hardware Stream</option>
        <option value="manual">Manual BPM Input</option>
      </select>
    </div>
  </div>

  <div class="bpm-container">
    <div style="font-size: 12px; color: var(--text-muted); font-weight: bold; letter-spacing: 1.5px;">BIOMETRIC STREAM</div>
    <div class="bpm-value" id="bpm-val"><span class="bpm-waiting">Touch ESP32 Sensor...</span></div>
    
    <div id="manual-input-container" style="display: none; margin-top: 10px;">
      <input type="number" id="manual-bpm-field" placeholder="Enter BPM (e.g. 75)" min="30" max="250" oninput="updateAnalysis()" style="width: 200px; text-align: center;">
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

<!-- High BPM Option Selection Modal (83 - 170 BPM) -->
<div class="modal-overlay" id="highBpmModal">
  <div class="modal-content" style="border-color: #ef4444;">
    <h3 style="margin-top:0; color:#ef4444;">High BPM Detected!</h3>
    <p style="font-size:14px; color:#94a3b8;">You selected <b>Maintain My Mood</b> with an elevated heart rate. Which vibe do you prefer?</p>
    <button class="modal-btn" style="border-color:#38bdf8;" onclick="triggerSearch('motivational')">🔥 Motivational, Gym & Pump-up</button>
    <button class="modal-btn" style="border-color:#38bdf8;" onclick="triggerSearch('breakup')">💔 Breakup & Soup Songs</button>
  </div>
</div>

<!-- Low BPM Warning Modal (< 55 BPM) -->
<div class="modal-overlay" id="lowBpmWarningModal">
  <div class="modal-content" style="border-color: #a855f7;">
    <h2 style="margin-top:0; color:#a855f7;">⚠️ ALERT</h2>
    <p style="font-size:18px; color:#ffffff; font-weight:bold;">BPM is critically low (< 55 BPM).</p>
    <p style="font-size:15px; color:#c084fc;">Seek Medical Attention!</p>
    <button class="modal-btn" style="border-color: #a855f7;" onclick="closeModal('lowBpmWarningModal')">Acknowledge & Dismiss</button>
  </div>
</div>

<!-- High Rest Warning Modal (171 - 200 BPM) -->
<div class="modal-overlay" id="extremeBpmWarningModal">
  <div class="modal-content" style="border-color: #ef4444;">
    <h2 style="margin-top:0; color:#ef4444;">⚠️ BPM TOO HIGH</h2>
    <p style="font-size:16px; color:#ffffff; font-weight:bold;">Your heart rate is high (171-200 BPM). Please take rest!</p>
    <button class="modal-btn" style="border-color: #ef4444;" onclick="playMelodyAndClose()">Relax with Calming Melody →</button>
  </div>
</div>

<!-- Critical Medical Help Emergency Modal (> 200 BPM) -->
<div class="modal-overlay" id="criticalMedicalModal">
  <div class="modal-content" style="border-color: #dc2626; background: #1a0303;">
    <h1 style="margin-top:0; color:#dc2626;">🚨 CRITICAL ALERT</h1>
    <p style="font-size:18px; color:#ffffff; font-weight:bold;">BPM EXCEEDS 200!</p>
    <p style="font-size:16px; color:#f87171; font-weight:bold;">Seek Medical Help!</p>
    <button class="modal-btn" style="border-color: #dc2626; background: #dc2626; color: white;" onclick="closeModal('criticalMedicalModal')">Acknowledge Emergency</button>
  </div>
</div>

<script>
  let isHardwareConnected = false;
  let espBpmValue = 0;
  let activeInputMode = "esp32";
  let activeWaveColor = '#334155';

  const canvas = document.getElementById('ecgCanvas');
  const ctx = canvas.getContext('2d');
  let x = 0;

  function drawECG() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
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

  function applyDynamicTheme(bgColor, cardBg, containerBg, accentColor, glowColor, textMuted) {
    const root = document.documentElement;
    root.style.setProperty('--bg-color', bgColor);
    root.style.setProperty('--card-bg', cardBg);
    root.style.setProperty('--container-bg', containerBg);
    root.style.setProperty('--accent-color', accentColor);
    root.style.setProperty('--glow-color', glowColor);
    root.style.setProperty('--text-muted', textMuted);

    activeWaveColor = accentColor;

    const recBtn = document.getElementById('rec-btn');
    if (!recBtn.disabled) {
      recBtn.style.background = accentColor;
    }
  }

  function updateAnalysis() {
    const bpm = getActiveBPM();
    const targetMode = document.getElementById('target-mode').value;
    const lang = document.getElementById('lang-select').value;
    
    const moodEl = document.getElementById('detected-mood');
    const genreEl = document.getElementById('suggested-genre');
    const recBtn = document.getElementById('rec-btn');

    // Default state: Pure black background & front panel with subtle gray glow
    if (!bpm || bpm <= 0) {
      applyDynamicTheme("#000000", "#000000", "#050505", "#38bdf8", "rgba(255, 255, 255, 0.08)", "#64748b");
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

    // Dynamic Full-Page Theme & Text Shifts
    if (bpm < 55) {
      // Low BPM Alert (Purple)
      applyDynamicTheme("#140924", "#1b0c30", "#0e061a", "#c084fc", "rgba(192, 132, 252, 0.45)", "#e9d5ff");
      moodEl.innerText = "Critically Low BPM (< 55)";
      genreEl.innerText = "Seek Medical Attention";
    } else if (bpm >= 55 && bpm <= 66) {
      // Relaxed (Deep Ocean Blue)
      applyDynamicTheme("#051329", "#081d3d", "#030e21", "#38bdf8", "rgba(56, 189, 248, 0.4)", "#93c5fd");
      moodEl.innerText = "Relaxed / Peaceful (55-66 BPM)";
    } else if (bpm >= 67 && bpm <= 82) {
      // Calm Baseline (Forest Green)
      applyDynamicTheme("#031c14", "#062b1f", "#02120d", "#22c55e", "rgba(34, 197, 94, 0.4)", "#86efac");
      moodEl.innerText = "Calm Baseline / Normal Vibe";
    } else if (bpm >= 83 && bpm <= 170) {
      // High Energy (Orange / Warm Amber)
      applyDynamicTheme("#240909", "#360e0e", "#190505", "#f97316", "rgba(249, 115, 22, 0.45)", "#fdba74");
      moodEl.innerText = "High Energy / Excited / Stressed";
    } else if (bpm > 170 && bpm <= 200) {
      // BPM High Caution (Deep Red)
      applyDynamicTheme("#330505", "#4a0808", "#240303", "#ef4444", "rgba(239, 68, 68, 0.5)", "#fca5a5");
      moodEl.innerText = "BPM Too High (171-200 BPM)";
      genreEl.innerText = "Rest & Soothing Melody";
      return;
    } else {
      // > 200 Critical Medical Emergency (Crimson Red)
      applyDynamicTheme("#450000", "#5e0000", "#300000", "#dc2626", "rgba(220, 38, 38, 0.75)", "#fecaca");
      moodEl.innerText = "DANGER: BPM > 200";
      genreEl.innerText = "Seek Medical Help!";
      return;
    }

    let genreText = "";
    if (targetMode === "maintain") {
      if (bpm >= 55 && bpm <= 66) genreText = `${lang} Chill, Relaxing & Love Songs`;
      else if (bpm >= 67 && bpm <= 82) genreText = `${lang} Normal Vibe & Folk Hits`;
      else if (bpm >= 83 && bpm <= 170) genreText = `${lang} Gym Pump-up OR Breakup/Soup`;
    } else {
      if (bpm >= 55 && bpm <= 66) genreText = `${lang} Motivational Gym Pump-up`;
      else if (bpm >= 67 && bpm <= 82) genreText = `${lang} Chill & Romantic Songs`;
      else if (bpm >= 83 && bpm <= 170) genreText = `${lang} Soothing Deep Relaxation`;
    }

    genreEl.innerText = genreText;
  }

  function handleRecommendationClick() {
    const bpm = getActiveBPM();
    const targetMode = document.getElementById('target-mode').value;

    if (bpm > 200) {
      document.getElementById('criticalMedicalModal').style.display = 'flex';
    } else if (bpm < 55) {
      document.getElementById('lowBpmWarningModal').style.display = 'flex';
    } else if (bpm > 170 && bpm <= 200) {
      document.getElementById('extremeBpmWarningModal').style.display = 'flex';
    } else if (targetMode === "maintain" && bpm >= 83 && bpm <= 170) {
      document.getElementById('highBpmModal').style.display = 'flex';
    } else {
      triggerSearch();
    }
  }

  function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
  }

  function playMelodyAndClose() {
    closeModal('extremeBpmWarningModal');
    const lang = document.getElementById('lang-select').value;
    const query = `${lang} deep relaxation soothing flute instrumental melodies`;
    window.open(`https://music.youtube.com/search?q=${encodeURIComponent(query)}`, '_blank');
  }

  function triggerSearch(highBpmChoice = null) {
    closeModal('highBpmModal');

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
      }
    } else {
      if (bpm >= 55 && bpm <= 66) {
        query = `${lang} motivational gym pump up workout songs`;
      } else if (bpm >= 67 && bpm <= 82) {
        query = `${lang} chill relaxing love romantic songs`;
      } else if (bpm >= 83 && bpm <= 170) {
        query = `${lang} deep relaxation calm soothing melodies`;
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
