from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
from flask_cors import CORS
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, 
     resources={
         r"/auth/google": {
             "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
             "methods": ["POST"],
             "allow_headers": ["Content-Type"],
             "supports_credentials": True
         }
     })
app.secret_key = os.urandom(24)  # Required for session management

# Get Google Client ID from environment
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
print(f"Loaded GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")  # Debug print

@app.route("/")
def index():
    return render_template('index.html', client_id=GOOGLE_CLIENT_ID)

@app.route("/auth/google", methods=['POST'])
def auth_google():
    try:
        # Get the credential and CSRF token from the request
        data = request.get_json()
        credential = data.get('credential')
        csrf_token_cookie = request.cookies.get('g_csrf_token')
        csrf_token_body = data.get('g_csrf_token')
        
        if not credential:
            return jsonify({'success': False, 'error': 'No credential provided'}), 400
            
        if not csrf_token_cookie or not csrf_token_body or csrf_token_cookie != csrf_token_body:
            return jsonify({'success': False, 'error': 'Failed to verify double submit cookie'}), 400
            
        # Verify the credential
        idinfo = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Store user info in session
        session['user'] = {
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', '')
        }
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route("/dashboard")
def dashboard():
    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', session=session)

if __name__ == '__main__':
    app.run(debug=True)