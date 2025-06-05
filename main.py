import os
import json
import tempfile
from flask import Flask, request, redirect, render_template, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pysftp

app = Flask(__name__)

# SFTP Credentials from Render environment
SFTP_HOST = os.environ.get("SFTP_HOST")
SFTP_USER = os.environ.get("SFTP_USER")
SFTP_PASS = os.environ.get("SFTP_PASS")
CREDENTIALS_FILENAME = "credentials.json"

def sftp_connection():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  # Disable host key checking
    return pysftp.Connection(host=SFTP_HOST, username=SFTP_USER, password=SFTP_PASS, cnopts=cnopts)

def download_credentials():
    with sftp_connection() as sftp:
        if sftp.exists(CREDENTIALS_FILENAME):
            with sftp.open(CREDENTIALS_FILENAME, 'r') as f:
                return json.load(f)
        return {}

def upload_credentials(data):
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name

    with sftp_connection() as sftp:
        if sftp.exists(CREDENTIALS_FILENAME):
            sftp.remove(CREDENTIALS_FILENAME)
        sftp.put(tmp_path, CREDENTIALS_FILENAME)

    os.remove(tmp_path)

@app.route('/')
def home():
    return "<h1>Welcome to the SFTP-linked Flask App</h1><a href='/login'>Login</a> | <a href='/signup'>Sign up</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        creds = download_credentials()
        username = request.form['username']
        password = request.form['password']

        if username in creds and check_password_hash(creds[username], password):
            return f"<h3>Welcome, {username}!</h3><a href='/'>Back to Home</a>"
        else:
            return "<p>Invalid username or password.</p>"

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        creds = download_credentials()
        username = request.form['username']
        password = request.form['password']

        if username in creds:
            return "<p>Username already exists.</p>"
        creds[username] = generate_password_hash(password)
        upload_credentials(creds)
        return "<p>Signup successful. You can now <a href='/login'>login</a>.</p>"

    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)
