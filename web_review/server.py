import http.server
import socketserver
import json
import os
import sys
import base64
import secrets
import logging
import traceback
from datetime import datetime

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PORT = 5050
HOST = "127.0.0.1"  # Bind to localhost only
DATA_FILE = os.path.join(os.path.dirname(__file__), "../al_rased/data/labeledSamples/training_data.json")

# Security Credentials
# Default credentials for local dev if not set in env
WEB_USER = os.getenv("WEB_USER", "admin")
WEB_PASS = os.getenv("WEB_PASS", "change_me_please")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Load model once at startup
print("Loading detection model...")
try:
    from al_rased.features.detection.engine import DetectionEngine
    from al_rased.features.detection.handlers import get_thresholds
    DetectionEngine.load_model()
    THRESHOLDS = get_thresholds()
    print("Model loaded!")
except Exception as e:
    print(f"Error loading model: {e}")
    THRESHOLDS = {}

class SecureReviewHandler(http.server.SimpleHTTPRequestHandler):
    def _check_auth(self):
        """Check for Basic Auth header."""
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return False
        
        try:
            # Header format: "Basic base64(user:pass)"
            auth_type, encoded = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return False
                
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            # Use constant-time comparison to prevent timing attacks
            user_match = secrets.compare_digest(username, WEB_USER)
            pass_match = secrets.compare_digest(password, WEB_PASS)
            
            return user_match and pass_match
        except Exception:
            return False

    def _send_auth_challenge(self):
        """Send 401 Unauthorized with Basic Auth challenge."""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Al-Rased Secure Review"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>401 Unauthorized</h1><p>Please enter credentials.</p>")

    def do_HEAD(self):
        if not self._check_auth():
            self._send_auth_challenge()
            return
        super().do_HEAD()

    def do_GET(self):
        if not self._check_auth():
            self._send_auth_challenge()
            return

        global THRESHOLDS
        if self.path == '/':
            self.path = '/web_review/templates/index.html'
        elif self.path.startswith('/static/'):
            self.path = '/web_review' + self.path
        
        if self.path == '/api/samples':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                # Add predictions to each sample
                for sample in data:
                    try:
                        result = DetectionEngine.predict(sample['text'])
                        sample['predicted_label'] = str(result['label'])
                        sample['confidence'] = round(result['confidence'] * 100, 1)
                        sample['matched_keyword'] = result.get('matched_keyword')
                        threshold = THRESHOLDS.get(str(result['label']), 0.5)
                        sample['threshold'] = round(threshold * 100, 1)
                        sample['is_gray_zone'] = result['confidence'] < threshold + 0.1 and result['confidence'] > threshold - 0.15
                    except Exception as e:
                        logging.error(f"Prediction error for sample: {e}")
                        sample['predicted_label'] = "Error"
                        sample['confidence'] = 0.0
                
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                logging.error(traceback.format_exc())
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
            
        elif self.path == '/api/stats':
             self.send_response(200)
             self.send_header('Content-type', 'application/json')
             self.end_headers()
             try:
                 with open(DATA_FILE, 'r') as f:
                     data = json.load(f)
                 from collections import Counter
                 stats = Counter()
                 for d in data:
                     # Support both single label and multi-label
                     if 'labels' in d and isinstance(d['labels'], list):
                         for lbl in d['labels']:
                             stats[lbl] += 1
                     else:
                         stats[d.get('label', 'Unknown')] += 1
                 self.wfile.write(json.dumps(stats).encode())
             except Exception as e:
                 self.wfile.write(json.dumps({"error": str(e)}).encode())
             return

        elif self.path == '/api/backup':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                import shutil
                backup_dir = os.path.join(os.path.dirname(DATA_FILE), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(backup_dir, f'training_data_{timestamp}.json')
                shutil.copy2(DATA_FILE, backup_file)
                
                # Count existing backups
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
                
                self.wfile.write(json.dumps({
                    'success': True,
                    'backup_file': backup_file,
                    'timestamp': timestamp,
                    'total_backups': len(backups)
                }).encode())
            except Exception as e:
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            return

        elif self.path == '/api/retrain':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            import subprocess
            try:
                cmd = [sys.executable, 'al_rased/features/model/train.py']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                if result.returncode == 0:
                    output_summary = "\n".join(result.stdout.splitlines()[-20:])
                    # Reload model and thresholds
                    DetectionEngine._model = None
                    DetectionEngine.load_model()
                    THRESHOLDS = get_thresholds()
                    print("Model and thresholds reloaded!")
                    
                    self.wfile.write(json.dumps({'success': True, 'output': output_summary}).encode())
                else:
                    self.wfile.write(json.dumps({'success': False, 'error': result.stderr}).encode())
            except Exception as e:
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            return

        # Prevent serving arbitrary files
        # The path has already been modified for / and /static/ above
        # Only allow serving specific files
        allowed_paths = [
            '/web_review/templates/index.html',
        ]
        
        is_allowed = self.path in allowed_paths or self.path.startswith('/web_review/static/')
        
        if is_allowed:
            # Check for directory traversal attempts '..'
            if '..' in self.path:
                self.send_error(403, "Forbidden")
                return
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if not self._check_auth():
            self._send_auth_challenge()
            return

        if self.path == '/api/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode())
            
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                # Find and update
                updated = False
                for d in data:
                    if d['text'] == payload['original_text']:
                        # Support both single and multi-label
                        if 'new_labels' in payload:
                            d['labels'] = payload['new_labels']
                            d['label'] = payload['new_labels'][0]  # Keep backward compat
                        else:
                            d['label'] = payload['new_label']
                            d['labels'] = [payload['new_label']]
                        d['reviewed_at'] = datetime.now().isoformat()
                        updated = True
                        break
                
                if updated:
                    with open(DATA_FILE, 'w') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode())
                else:
                    self.send_error(404, "Sample not found")
                    
            except Exception as e:
                self.send_error(500, str(e))
                
        elif self.path == '/api/delete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode())
            
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                
                # Find and delete
                initial_len = len(data)
                data = [d for d in data if d['text'] != payload['original_text']]
                
                if len(data) < initial_len:
                    with open(DATA_FILE, 'w') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode())
                else:
                    self.send_error(404, "Sample not found")
                    
            except Exception as e:
                self.send_error(500, str(e))

print(f"🔒 Secure Server serving at http://{HOST}:{PORT}")
print(f"📂 Data file: {DATA_FILE}")

if WEB_PASS == "change_me_please":
    print("⚠️ WARNING: Using default password. Set WEB_USER and WEB_PASS environment variables!")

# Allow reuse of address to prevent 'Address already in use'
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer((HOST, PORT), SecureReviewHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
