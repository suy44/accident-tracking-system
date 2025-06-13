import os
import json
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import pysftp

# Initialize Flask app with React static folder
app = Flask(__name__, static_folder='build')

# Load SFTP credentials from environment
SFTP_HOST = os.environ.get("SFTP_HOST")
SFTP_USER = os.environ.get("SFTP_USER")
SFTP_PASS = os.environ.get("SFTP_PASS")
CREDENTIALS_FILENAME = "credentials.json"
SFTP_UPLOAD_DIR = "home"  # Update if needed

# SFTP connection helper
def sftp_connection():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    return pysftp.Connection(host=SFTP_HOST, username=SFTP_USER, password=SFTP_PASS, cnopts=cnopts)

# Download credentials from SFTP
def download_credentials():
    with sftp_connection() as sftp:
        sftp.chdir(SFTP_UPLOAD_DIR)
        if sftp.exists(CREDENTIALS_FILENAME):
            with sftp.open(CREDENTIALS_FILENAME, 'r') as f:
                return json.load(f)
        return {}

# Upload credentials to SFTP
def upload_credentials(data):
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name

    with sftp_connection() as sftp:
        sftp.chdir(SFTP_UPLOAD_DIR)
        if sftp.exists(CREDENTIALS_FILENAME):
            sftp.remove(CREDENTIALS_FILENAME)
        sftp.put(tmp_path, CREDENTIALS_FILENAME)

    os.remove(tmp_path)

# ✅ API endpoint: login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing credentials'}), 400

    creds = download_credentials()

    if username in creds and check_password_hash(creds[username], password):
        return jsonify({'success': True, 'message': f"Welcome {username}"}), 200
    return jsonify({'success': False, 'message': "Invalid username or password"}), 400

# ✅ API endpoint: signup
@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    creds = download_credentials()

    if username in creds:
        return jsonify({'success': False, 'message': "Username already exists"}), 400

    creds[username] = generate_password_hash(password)
    upload_credentials(creds)

    return jsonify({'success': True, 'message': "Signup successful"}), 200

# ✅ Serve React frontend (catch-all for "/", "/signup", etc.)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# ✅ Start app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
