from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global memory storage for incoming ESP32 data
latest_biometrics = {
    "bpm": 72,
    "source": "ESP32",
    "status": "System Active"
}

# --- EMBEDDED DYNAMIC HTML FRONTEND ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BioSync - Biometric Music Recommender</title>
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
    }

    .dashboard-card {
      background: #131e3a;
      border: 1px solid #1e2942;
      border-radius: 20px;
      width: 90%;
      max-width: 750px;
      padding: 32px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0a0f1d;
      padding: 14px 20px;
      border-radius: 12px;
      font-size: 14px;
      border: 1px solid #1c2b4e;
    }

    .status-live {
      color: #22c55e;
      font-weight: bold;
    }

    .mode-select-header {
      background: #1c2b4e;
      color: #38bdf8;
      border: 1px solid #38bdf8;
      padding: 6px 12px;
      border-radius: 8px;
      font-weight: bold;
      cursor: pointer;
      font-size: 13px;
    }

    .bpm-container {
      text-align: center;
      background: #090d1a;
      padding: 28px;
      border-radius: 16px;
      border: 1px solid #1e2942;
    }

    .bpm-value {
      font-size: 64px;
      font-weight: bold;
      color: #38bdf8;
      margin: 8px 0;
    }

    canvas {
      background: #020617;
      border-radius: 8px;
      width: 100%;
      height: 70px;
      margin-top: 12px;
    }

    .controls-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    label {
      font-size: 12px;
      color: #94a3b8;
      font-weight: 700;
      letter-spacing: 1px;
    }

    select, button {
      padding: 14px 16px;
      border-radius: 10px;
      border: none;
      font-size: 14px;
      font-weight: bold;
    }

    select {
      background: #1c2b4e;
      color: white;
      outline: none;
      cursor: pointer;
    }

    .btn-submit {
      grid-column: span 2;
      background: #38bdf8;
      color: #0b1329;
      font-size: 16px;
      cursor: pointer;
      margin-top: 10px;
      transition: background 0.2s ease;
    }

    .btn-submit:hover {
      background: #7dd3fc;
    }
  </style>
</head>
<body>

<div class="dashboard-card">
  
  <div class="header-bar">
    <span>ESP32 STATUS: <span class="status-live">LIVE [GPIO 13]</span></span>
    <div>
      <span style="color: #94a3b8; margin-right: 8px;">ACTIVE SYSTEM:</span>
      <select class="mode-select-header" id="system-mode">
        <option value="Mode 1: Manual Pulse">Mode 1: Manual Pulse</option>
        <option value="Mode 2: ESP32 Touch" selected>Mode 2: ESP32 Touch</option>
        <option value="Mode 3: Continuous Stream">Mode 3: Continuous Stream</option>
      </select>
    </div>
  </div>

  <div class="bpm-container">
    <div style="font-size: 12px; color: #94a3b8; font-weight: bold; letter-spacing: 1.5px;">BIOMETRIC STREAM</div>
    <div class="bpm-value" id="bpm-val">-- <span style="font-size: 24px;">BPM</span></div>
    <canvas id="ecgCanvas" width="600" height="70"></canvas>
  </div>

  <div class="controls-grid">
    
    <!-- Language Selection -->
    <div class="form-group">
      <label for="lang-select">SELECT MUSIC LANGUAGE</label>
      <select id="lang-select">
        <option value="Tamil">Tamil</option>
        <option value="International">International</option>
        <option value="Hindi">Hindi</option>
        <option value="Telugu">Telugu</option>
        <option value="Malayalam">Malayalam</option>
      </select>
    </div>

    <!-- Biomatch Target Mode (2 Target Modes) -->
    <div class="form-group">
      <label for="target-mode">BIOMATCH TARGET MODE</label>
      <select id="target-mode">
        <option value="change">Change My Mood</option>
        <option value="maintain">Maintain My Mood</option>
      </select>
    </div>

    <button class="btn-submit" onclick="generateYouTubeRecommendation()">Open YouTube Music Recommendation →</button>
  </div>

</div>

<script>
  // Dynamic Canvas ECG Waveform Animation
  const canvas = document.getElementById('ecgCanvas');
  const ctx = canvas.getContext('2d');
  let x = 0;

  function drawECG() {
    ctx.fillStyle = 'rgba(2, 6, 23, 0.15)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.beginPath();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.moveTo(x, canvas.height / 2);
    
    x += 4;
    if (x > canvas.width) x = 0;
    
    let y = canvas.height / 2;
    if (x % 60 > 25 && x % 60 < 35) {
      y += (Math.random() - 0.5) * 40;
    }
    
    ctx.lineTo(x, y);
    ctx.stroke();
    requestAnimationFrame(drawECG);
  }
  drawECG();

  // Polling backend endpoint for live ESP32 BPM values
  async function pollESP32BPM() {
    try {
      const res = await fetch('/api/bpm');
      const data = await res.json();
      
      if (data && data.bpm) {
        document.getElementById('bpm-val').innerHTML = `${data.bpm} <span style="font-size: 24px;">BPM</span>`;
      }
    } catch (err) {
      console.log("Polling ESP32 data...");
    }
  }
  setInterval(pollESP32BPM, 1000);

  // Direct YouTube Music Search Generator
  function generateYouTubeRecommendation() {
    const lang = document.getElementById('lang-select').value;
    const targetMode = document.getElementById('target-mode').value;
    
    // Extract numerical heart rate
    const bpmText = document.getElementById('bpm-val').innerText;
    const bpm = parseInt(bpmText) || 72;

    let query = "";

    if (targetMode === "change") {
      // Logic for "Change My Mood": If BPM is high, fetch relaxing music. If low, fetch energetic music.
      if (bpm > 85) {
        query = `${lang} relaxing calm soothing music songs`;
      } else {
        query = `${lang} high energy upbeat workout songs`;
      }
    } else {
      // Logic for "Maintain My Mood": Match the current state directly
      if (bpm > 85) {
        query = `${lang} energetic high tempo party songs`;
      } else if (bpm < 65) {
        query = `${lang} deep relaxation ambient meditation music`;
      } else {
        query = `${lang} chill pleasant acoustic melody songs`;
      }
    }

    // Launch YouTube Music with targeted search query in a new tab
    const ytMusicUrl = `https://music.youtube.com/search?q=${encodeURIComponent(query)}`;
    window.open(ytMusicUrl, '_blank');
  }
</script>

</body>
</html>
"""

# --- FLASK API ROUTES ---

@app.route('/')
def home():
    """Serves the main biometric dashboard interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/bpm', methods=['GET', 'POST'])
def handle_bpm():
    """Receives heart rate from ESP32 POST request and provides GET polling for UI"""
    global latest_biometrics
    
    if request.method == 'POST':
        data = request.get_json()
        if data and 'bpm' in data:
            latest_biometrics['bpm'] = data['bpm']
            if 'source' in data:
                latest_biometrics['source'] = data['source']
            return jsonify({"status": "success", "received": data['bpm']}), 200
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    return jsonify(latest_biometrics)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
