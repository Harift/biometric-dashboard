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
      --bg-color: #030712;
      --card-bg: #090d16;
      --container-bg: #030712;
      --accent-color: #38bdf8;
      --glow-color: rgba(56, 189, 248, 0.2);
      --text-muted: #94a3b8;
    }

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
      overflow-x: hidden;
      position: relative;
      transition: background-color 0.8s ease;
      animation: bgPulseGlow 2.5s infinite ease-in-out;
    }

    .main-container {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 30px;
      width: 95%;
      max-width: 1100px;
      margin: 20px auto;
    }

    .dashboard-card {
      position: relative;
      z-index: 10;
      background: var(--card-bg);
      border: 1px solid var(--accent-color);
      border-radius: 20px;
      flex: 1;
      max-width: 650px;
      padding: 32px;
      backdrop-filter: blur(14px);
      display: flex;
      flex-direction: column;
      gap: 20px;
      transition: all 0.8s ease;
      box-shadow: 0 10px 35px rgba(0,0,0,0.85);
    }

    /* KURISU SVG AVATAR STYLES */
    .avatar-wrapper {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      width: 340px;
      height: 520px;
    }

    .kurisu-svg {
      width: 100%;
      height: 100%;
      filter: drop-shadow(0 0 20px var(--accent-color));
      transition: filter 0.5s ease, transform 0.3s ease;
    }

    .avatar-dialog-box {
      position: absolute;
      top: 10px;
      background: rgba(9, 13, 22, 0.9);
      border: 1px solid var(--accent-color);
      border-radius: 12px;
      padding: 10px 14px;
      font-size: 13px;
      font-weight: bold;
      color: #ffffff;
      text-align: center;
      box-shadow: 0 4px 15px rgba(0,0,0,0.5);
      pointer-events: none;
      transition: all 0.3s ease;
      max-width: 260px;
    }

    /* Expression transitions */
    .eye, .mouth, .brow, .blush, .sweat {
      transition: all 0.3s ease;
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
  </style>
</head>
<body>

<div class="main-container">

  <!-- DASHBOARD CARD -->
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

  <!-- PURE SVG MAKISE KURISU AVATAR WITH DYNAMIC EXPRESSIONS -->
  <div class="avatar-wrapper">
    <div class="avatar-dialog-box" id="kurisu-dialog">"Waiting for pulse data... Don't keep me waiting."</div>

    <svg class="kurisu-svg" viewBox="0 0 300 450" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="hairGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#b03a1b" />
          <stop offset="100%" stop-color="#5a1807" />
        </linearGradient>
        <linearGradient id="tieGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#ff1a1a" />
          <stop offset="100%" stop-color="#800000" />
        </linearGradient>
        <linearGradient id="eyeGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#a855f7" />
          <stop offset="100%" stop-color="#3b0764" />
        </linearGradient>
      </defs>

      <!-- Back Hair (Long Chestnut-Red) -->
      <path d="M 60 140 Q 30 250 50 420 Q 150 440 250 420 Q 270 250 240 140 Z" fill="url(#hairGrad)" />

      <!-- White Lab Coat / Jacket Backing -->
      <path d="M 70 280 L 30 450 L 270 450 L 230 280 Z" fill="#cfab7a" />
      <path d="M 90 290 L 50 450 L 250 450 L 210 290 Z" fill="#e2e8f0" />

      <!-- Neck & High Collar -->
      <path d="M 130 220 L 170 220 L 175 270 L 125 270 Z" fill="#fce7f3" />
      <path d="M 132 245 L 168 245 L 170 268 L 130 268 Z" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" />

      <!-- Iconic Red Tie -->
      <polygon points="144,260 156,260 160,370 150,390 140,370" fill="url(#tieGrad)" />
      <polygon points="142,255 158,255 155,270 145,270" fill="#cc0000" />

      <!-- Open Khaki Jacket Straps & Lapels -->
      <path d="M 85 285 L 130 350 L 115 450 L 45 450 Z" fill="#b48a56" />
      <path d="M 215 285 L 170 350 L 185 450 L 255 450 Z" fill="#b48a56" />

      <!-- Face Base -->
      <path d="M 100 130 Q 150 240 200 130 Q 200 90 100 90 Z" fill="#fff1f2" />

      <!-- Dynamic Blush -->
      <g id="blush-group" opacity="0">
        <ellipse cx="120" cy="180" rx="14" ry="6" fill="#f43f5e" opacity="0.4" />
        <ellipse cx="180" cy="180" rx="14" ry="6" fill="#f43f5e" opacity="0.4" />
      </g>

      <!-- Dynamic Sweat Drop (Stressed / Extreme BPM) -->
      <path id="sweat-drop" class="sweat" d="M 205 135 Q 210 145 205 150 Q 200 145 205 135 Z" fill="#38bdf8" opacity="0" />

      <!-- Purple Eyes (Kurisu's Sharp Violet Eyes) -->
      <g id="left-eye" class="eye">
        <ellipse cx="125" cy="165" rx="12" ry="16" fill="url(#eyeGrad)" />
        <ellipse cx="125" cy="165" rx="10" ry="13" fill="#000000" />
        <circle cx="122" cy="158" r="4" fill="#ffffff" />
        <path d="M 110 148 Q 125 142 140 150" stroke="#1e293b" stroke-width="3.5" fill="none" stroke-linecap="round" />
      </g>

      <g id="right-eye" class="eye">
        <ellipse cx="175" cy="165" rx="12" ry="16" fill="url(#eyeGrad)" />
        <ellipse cx="175" cy="165" rx="10" ry="13" fill="#000000" />
        <circle cx="172" cy="158" r="4" fill="#ffffff" />
        <path d="M 160 150 Q 175 142 190 148" stroke="#1e293b" stroke-width="3.5" fill="none" stroke-linecap="round" />
      </g>

      <!-- Eyebrows (Tsundere Sharp / Expressive) -->
      <path id="left-brow" class="brow" d="M 110 142 Q 125 136 142 144" stroke="#5a1807" stroke-width="3" fill="none" stroke-linecap="round" />
      <path id="right-brow" class="brow" d="M 158 144 Q 175 136 190 142" stroke="#5a1807" stroke-width="3" fill="none" stroke-linecap="round" />

      <!-- Nose -->
      <path d="M 150 174 L 148 182 L 152 182" stroke="#fda4af" stroke-width="1.5" fill="none" />

      <!-- Dynamic Mouth -->
      <path id="mouth-path" class="mouth" d="M 140 198 Q 150 200 160 198" stroke="#be123c" stroke-width="2.5" fill="none" stroke-linecap="round" />

      <!-- Front Bangs & Side Hair Framing Face -->
      <path d="M 95 130 Q 125 170 130 110 Q 150 180 155 105 Q 170 175 205 130 Q 190 60 110 65 Z" fill="url(#hairGrad)" />
      <!-- Left side strand -->
      <path d="M 95 120 Q 80 200 90 310 Q 105 310 102 200 Z" fill="url(#hairGrad)" />
      <!-- Right side strand -->
      <path d="M 205 120 Q 220 200 210 310 Q 195 310 198 200 Z" fill="url(#hairGrad)" />
    </svg>
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

  /* KURISU EXPRESSION CONTROLLER */
  function setKurisuExpression(emotion) {
    const dialog = document.getElementById('kurisu-dialog');
    const mouth = document.getElementById('mouth-path');
    const leftBrow = document.getElementById('left-brow');
    const rightBrow = document.getElementById('right-brow');
    const blush = document.getElementById('blush-group');
    const sweat = document.getElementById('sweat-drop');

    if (emotion === "waiting") {
      dialog.innerText = '"Waiting for pulse data... Don\'t keep me waiting."';
      mouth.setAttribute("d", "M 142 198 Q 150 197 158 198"); // Slight neutral line
      leftBrow.setAttribute("d", "M 110 142 Q 125 136 142 144");
      rightBrow.setAttribute("d", "M 158 144 Q 175 136 190 142");
      blush.setAttribute("opacity", "0");
      sweat.setAttribute("opacity", "0");
    } 
    else if (emotion === "calm") {
      dialog.innerText = '"Heart rate is perfectly stable. Good job keeping composure."';
      mouth.setAttribute("d", "M 140 195 Q 150 205 160 195"); // Soft smile
      leftBrow.setAttribute("d", "M 110 140 Q 125 135 142 140");
      rightBrow.setAttribute("d", "M 158 140 Q 175 135 190 140");
      blush.setAttribute("opacity", "0.2");
      sweat.setAttribute("opacity", "0");
    }
    else if (emotion === "excited") {
      dialog.innerText = '"B-Baka! Your pulse is spiking fast! Don\'t overdo it!"';
      mouth.setAttribute("d", "M 140 195 Q 150 185 160 195"); // Open surprised mouth
      leftBrow.setAttribute("d", "M 110 135 Q 125 142 142 138"); // Sharp tsundere brow
      rightBrow.setAttribute("d", "M 158 138 Q 175 142 190 135");
      blush.setAttribute("opacity", "0.8"); // High Tsundere Blush
      sweat.setAttribute("opacity", "0");
    }
    else if (emotion === "concerned") {
      dialog.innerText = '"Hey! Your heart rate is dangerously high! Take a breath!"';
      mouth.setAttribute("d", "M 142 202 Q 150 192 158 202"); // Worried frown
      leftBrow.setAttribute("d", "M 110 145 Q 125 138 142 148");
      rightBrow.setAttribute("d", "M 158 148 Q 175 138 190 145");
      blush.setAttribute("opacity", "0");
      sweat.setAttribute("opacity", "1"); // Sweat drop visible
    }
  }

  function updateAnalysis() {
    const bpm = getActiveBPM();
    const targetMode = document.getElementById('target-mode').value;
    const lang = document.getElementById('lang-select').value;
    
    const moodEl = document.getElementById('detected-mood');
    const genreEl = document.getElementById('suggested-genre');
    const recBtn = document.getElementById('rec-btn');

    if (!bpm || bpm <= 0) {
      applyDynamicTheme("#030712", "#090d16", "#030712", "#38bdf8", "rgba(56, 189, 248, 0.15)", "#64748b");
      setKurisuExpression("waiting");
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

    if (bpm < 55) {
      applyDynamicTheme("#140924", "#1b0c30", "#0e061a", "#c084fc", "rgba(192, 132, 252, 0.45)", "#e9d5ff");
      setKurisuExpression("concerned");
      moodEl.innerText = "Critically Low BPM (< 55)";
      genreEl.innerText = "Seek Medical Attention";
    } else if (bpm >= 55 && bpm <= 82) {
      applyDynamicTheme("#031c14", "#062b1f", "#02120d", "#22c55e", "rgba(34, 197, 94, 0.4)", "#86efac");
      setKurisuExpression("calm");
      moodEl.innerText = "Calm Baseline / Normal Vibe";
    } else if (bpm >= 83 && bpm <= 170) {
      applyDynamicTheme("#240909", "#360e0e", "#190505", "#f97316", "rgba(249, 115, 22, 0.45)", "#fdba74");
      setKurisuExpression("excited");
      moodEl.innerText = "High Energy / Excited / Stressed";
    } else {
      applyDynamicTheme("#330505", "#4a0808", "#240303", "#ef4444", "rgba(239, 68, 68, 0.5)", "#fca5a5");
      setKurisuExpression("concerned");
      moodEl.innerText = "BPM Too High (> 170 BPM)";
      genreEl.innerText = "Rest & Medical Caution";
      return;
    }

    let genreText = "";
    if (targetMode === "maintain") {
      if (bpm >= 55 && bpm <= 82) genreText = `${lang} Chill & Soft Hits`;
      else genreText = `${lang} Gym Pump-up OR Soup Songs`;
    } else {
      if (bpm >= 55 && bpm <= 82) genreText = `${lang} Energetic Workout Tracks`;
      else genreText = `${lang} Deep Relaxation Melodies`;
    }

    genreEl.innerText = genreText;
  }

  function handleRecommendationClick() {
    const lang = document.getElementById('lang-select').value;
    const targetMode = document.getElementById('target-mode').value;
    const bpm = getActiveBPM();

    let query = `${lang} mood relaxation music`;
    if (targetMode === "maintain") {
      if (bpm >= 55 && bpm <= 82) query = `${lang} chill relaxing love romantic songs`;
      else query = `${lang} motivational gym pump up songs`;
    } else {
      if (bpm >= 55 && bpm <= 82) query = `${lang} motivational gym pump up workout songs`;
      else query = `${lang} deep relaxation calm soothing melodies`;
    }

    window.open(`https://music.youtube.com/search?q=${encodeURIComponent(query)}`, '_blank');
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
