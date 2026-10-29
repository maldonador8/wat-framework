#!/usr/bin/env python3
"""
Twitter/X OAuth 2.0 PKCE Auth — one-time setup
"""

import os
import sys
import json
import secrets
import hashlib
import base64
import urllib.parse
import urllib.request
import urllib.error
import http.server
import threading
import webbrowser

def load_env():
    dirs = [
        os.path.dirname(__file__),
        os.path.join(os.path.dirname(__file__), '..'),
        os.path.join(os.path.dirname(__file__), '..', 'claude-agents'),
    ]
    for d in dirs:
        env_path = os.path.join(d, '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())

load_env()

CLIENT_ID = os.environ.get('TWITTER_CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('TWITTER_CLIENT_SECRET', '')

if not CLIENT_ID:
    print("ERROR: TWITTER_CLIENT_ID not set in .env")
    sys.exit(1)

REDIRECT_URI = 'http://localhost:8765/callback'
SCOPES = 'tweet.read tweet.write users.read offline.access'

code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()
state = secrets.token_urlsafe(16)

auth_code_holder = {'code': None}
server_done = threading.Event()

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if 'code' in params:
            auth_code_holder['code'] = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h2 style="font-family:sans-serif;color:green;">Authorized! Return to your terminal.</h2>')
            server_done.set()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'<h2>Error - no code received.</h2>')
    def log_message(self, *args):
        pass

def get_token(code):
    data = urllib.parse.urlencode({
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier,
        'client_id': CLIENT_ID,
    }).encode()
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if CLIENT_SECRET:
        creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        headers['Authorization'] = f'Basic {creds}'
    req = urllib.request.Request('https://api.twitter.com/2/oauth2/token',
                                  data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Token error {e.code}: {e.read().decode()}")
        return None

def save_token(access_token, refresh_token=''):
    env_path = os.path.join(os.path.dirname(__file__), '..', 'claude-agents', '.env')
    with open(env_path, 'r') as f:
        content = f.read()
    import re
    if 'TWITTER_OAUTH2_TOKEN=' in content:
        content = re.sub(r'TWITTER_OAUTH2_TOKEN=.*', f'TWITTER_OAUTH2_TOKEN={access_token}', content)
    else:
        content = content.rstrip() + f'\nTWITTER_OAUTH2_TOKEN={access_token}\n'
    if refresh_token:
        if 'TWITTER_OAUTH2_REFRESH=' in content:
            content = re.sub(r'TWITTER_OAUTH2_REFRESH=.*', f'TWITTER_OAUTH2_REFRESH={refresh_token}', content)
        else:
            content = content.rstrip() + f'\nTWITTER_OAUTH2_REFRESH={refresh_token}\n'
    with open(env_path, 'w') as f:
        f.write(content)
    print("Token saved to .env")

def run():
    params = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    })
    auth_url = f"https://twitter.com/i/oauth2/authorize?{params}"

    server = http.server.HTTPServer(('localhost', 8765), CallbackHandler)
    server.timeout = 1

    def serve():
        while not server_done.is_set():
            server.handle_request()
        server.server_close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    print(f"\n{'='*60}")
    print("  TWITTER/X OAUTH 2.0 — ONE-TIME SETUP")
    print(f"{'='*60}")
    print("\nSTEP 1: Copy this URL and open it in your browser:\n")
    print(f"  {auth_url}\n")
    print("STEP 2: Log in with your X account and click Authorize")
    print("STEP 3: The page will redirect to localhost — come back here\n")
    print("Waiting for authorization (2 min timeout)...")

    webbrowser.open(auth_url)

    server_done.wait(timeout=120)

    if not auth_code_holder['code']:
        print("\nERROR: Timed out. Make sure http://localhost:8765/callback is in your app's Callback URIs on developer.x.com, then try again.")
        sys.exit(1)

    print("Got authorization code. Exchanging for token...")
    token_data = get_token(auth_code_holder['code'])

    if not token_data or 'access_token' not in token_data:
        print(f"ERROR: {token_data}")
        sys.exit(1)

    save_token(token_data['access_token'], token_data.get('refresh_token', ''))

    print("\nDone! Now test posting:")
    print("  python3 tools/twitter_post.py --text 'Hello from Bible with AI!' --dry-run")

if __name__ == '__main__':
    run()
