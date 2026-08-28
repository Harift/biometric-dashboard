import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

latest_biometrics = {
    "bpm": None,
    "last_seen": 0,
    "connected": False
}

TIMEOUT_SECONDS = 5

@app.route('/')
def home():
    return render_template('index.html')

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
