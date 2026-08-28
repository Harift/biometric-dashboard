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
      width: 100%;
      max-width: 480px;
      padding: 24px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0a0f1d;
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 13px;
      border: 1px solid #1c2b4e;
    }

    .status-live {
      color: #22c55e;
      font-weight: bold;
    }

    .bpm-container {
      text-align: center;
      background: #090d1a;
      padding: 24px;
      border-radius: 16px;
      border: 1px solid #1e2942;
    }

    .bpm-value {
      font-size: 56px;
      font-weight: bold;
      color: #38bdf8;
      margin: 8px 0;
    }

    canvas {
      background: #020617;
      border-radius: 8px;
      width: 100%;
      height: 60px;
      margin-top: 10px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    label {
      font-size: 13px;
      color: #94a3b8;
      font-weight: 600;
      letter-spacing: 0.5px;
    }

    select, button {
      padding: 12px 16px;
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

    .mode-buttons {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .btn-relax { background: #3b82f6; color: white; cursor: pointer; }
    .btn-energize { background: #22c55e; color: black; cursor: pointer; }
    .btn-submit { background: #38bdf8; color: black; cursor: pointer; }

    button:hover { opacity: 0.9; }
  </style>
</head>
<body>

<div class="dashboard-card">
  
  <!-- Header Connection Bar -->
  <div class="header-bar">
    <span>ESP32 STATUS: <span class="status-live">LIVE [GPIO 13]</span></span>
    <span>MODE 2</span>
  </div>

  <!-- Real-Time Heart Rate & ECG Canvas Display -->
  <div class="bpm-container">
    <div style="font-size: 12px; color: #94a3b8; font-weight: bold; letter-spacing: 1px;">BIOMETRIC STREAM</div>
    <div class="bpm-value" id="bpm-val">-- <span style="font-size: 20px;">BPM</span></div>
    
    <!-- Dynamic Waveform Graph -->
    <canvas id="ecgCanvas" width="400" height="60"></canvas>
  </div>

  <!-- Step 1: Preferred Language Input -->
  <div id="step-lang" class="form-group">
    <label for="lang-select">SELECT MUSIC LANGUAGE</label>
    <select id="lang-select">
      <option value="English">English</option>
      <option value="Hindi">Hindi</option>
      <option value="Tamil">Tamil</option>
      <option value="Spanish">Spanish</option>
    </select>
    <button class="btn-submit" onclick="confirmLanguage()">Continue →</button>
  </div>

  <!-- Step 2: Mode Targets (Hidden until step 1 complete) -->
  <div id="step-mode" class="form-group" style="display: none;">
    <label>SELECT AUDIO BIOMATCH TARGET</label>
    <div class="mode-buttons">
      <button class="btn-relax" onclick="fetchRecommendations('relax')">RELAX (Lower BPM)</button>
      <button class="btn-energize" onclick="fetchRecommendations('energize')">ENERGIZE (Match BPM)</button>
    </div>
  </div>

</div>

<script>
  let selectedLanguage = "English";

  // Canvas Oscilloscope Animation logic
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
    
    x += 3;
    if (x > canvas.width) x = 0;
    
    let y = canvas.height / 2;
    if (x % 50 > 20 && x % 50 < 30) {
      y += (Math.random() - 0.5) * 35;
    }
    
    ctx.lineTo(x, y);
    ctx.stroke();
    requestAnimationFrame(drawECG);
  }
  drawECG();

  function confirmLanguage() {
    selectedLanguage = document.getElementById('lang-select').value;
    document.getElementById('step-lang').style.display = 'none';
    document.getElementById('step-mode').style.display = 'flex';
  }

  // Fetch real-time BPM sent by ESP32 via backend API
  async function pollESP32BPM() {
    try {
      const res = await fetch('/api/bpm');
      const data = await res.json();
      
      if (data && data.bpm) {
        document.getElementById('bpm-val').innerHTML = `${data.bpm} <span style="font-size: 20px;">BPM</span>`;
      }
    } catch (err) {
      console.log("Polling ESP32 data error:", err);
    }
  }

  // Poll backend every 1000ms
  setInterval(pollESP32BPM, 1000);

  function fetchRecommendations(mode) {
    const currentBpm = document.getElementById('bpm-val').innerText.split(' ')[0];
    alert(`Triggering recommendations!\nMode: ${mode.toUpperCase()}\nLanguage: ${selectedLanguage}\nCurrent BPM: ${currentBpm}`);
  }
</script>

</body>
</html>
"""

# --- BACKEND SERVER ROUTES ---

@app.route('/')
def home():
    """Serves the dashboard interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/bpm', methods=['GET', 'POST'])
def handle_bpm():
    """Receives data from ESP32 (POST) and serves data to Frontend UI (GET)"""
    global latest_biometrics
    
    if request.method == 'POST':
        data = request.get_json()
        if data and 'bpm' in data:
            latest_biometrics['bpm'] = data['bpm']
            if 'source' in data:
                latest_biometrics['source'] = data['source']
            return jsonify({"status": "success", "received": data['bpm']}), 200
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    # GET request called by UI polling loop
    return jsonify(latest_biometrics)

if __name__ == '__main__':
    # Flask port setup matching typical deployment defaults
    app.run(host='0.0.0.0', port=5000)
